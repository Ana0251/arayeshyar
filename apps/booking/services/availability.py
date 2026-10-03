"""
سرویس محاسبه‌ی اسلات‌های آزاد.

─── الگوریتم: ───
1. ساعت کاری روز رو بگیر
2. بازه‌های پُر (رزرو + وقفه) رو محاسبه کن
3. بازه‌های پُر رو ادغام کن
4. بازه‌های آزاد = تفاضل
5. برای هر بازه‌ی آزاد، با گام duration اسلات بساز

─── نکته‌ی timezone: ───
همه‌ی datetime ها توی UTC محاسبه میشن (چون Django DB رو UTC نگه می‌داره).
فقط برای نمایش، به Tehran تبدیل میشن.
"""

"""
سرویس محاسبه‌ی اسلات‌های آزاد.
"""

from datetime import date, datetime, time, timedelta
from datetime import timezone as dt_timezone   
from typing import TYPE_CHECKING

from django.db.models import Q
from django.utils import timezone

from apps.business.constants import Weekday
from apps.business.models import (
    Break,
    Business,
    DayOff,
    SpecialWorkingHours,
    Staff,
    Station,
    WorkingHours,
)

from ..constants import DEFAULT_SLOT_DURATION, SlotStatus

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════
#  SlotInfo
# ═══════════════════════════════════════════════════════════════


class SlotInfo:
    """اطلاعات یه اسلات (برای template)."""

    __slots__ = ("time", "status", "label")

    def __init__(
        self,
        time: time,
        status: str = SlotStatus.AVAILABLE,
        label: str = "",
    ) -> None:
        self.time = time
        self.status = status
        self.label = label

    def to_dict(self) -> dict:
        return {
            "time": self.time.strftime("%H:%M"),
            "status": self.status,
            "label": self.label,
        }


# ═══════════════════════════════════════════════════════════════
#  AvailabilityService
# ═══════════════════════════════════════════════════════════════


class AvailabilityService:
    """
    سرویس محاسبه‌ی اسلات‌های آزاد.

    ─── استفاده: ───
        service = AvailabilityService(
            business=business,
            target_date=target_date,
            station=station,
            staff=staff,
        )
        slots = service.get_available_slots(duration=90)
    """

    def __init__(
        self,
        business: Business,
        target_date: date,
        station: Station | None = None,
        staff: Staff | None = None,
    ) -> None:
        self.business = business
        self.target_date = target_date
        self.station = station
        self.staff = staff
        self.current_tz = timezone.get_current_timezone()

    # ═══════════════════════════════════════════════════════════
    #  Public API
    # ═══════════════════════════════════════════════════════════

    def get_available_slots(self, duration: int = DEFAULT_SLOT_DURATION) -> list[time]:
        """اسلات‌های آزاد (فقط available)."""
        slots_with_status = self.get_all_slots_with_status(duration)
        return [s.time for s in slots_with_status if s.status == SlotStatus.AVAILABLE]

    def get_all_slots_with_status(
        self,
        duration: int = DEFAULT_SLOT_DURATION,
    ) -> list[SlotInfo]:
        """
        همه‌ی اسلات‌ها با وضعیت (available, booked, break, short).

        ─── نکته‌ی مهم: ───
        همه‌ی محاسبات توی UTC هستن. فقط برای نمایش، به Tehran تبدیل میشن.
        """
        # ─── ۱. ساعت کاری (به‌صورت Tehran → UTC) ───
        hours = self._get_business_hours()
        if not hours:
            return []

        start_time, end_time = hours

        # ─── ساخت با Tehran، بعد تبدیل به UTC ───
        day_start_local = timezone.make_aware(
            datetime.combine(self.target_date, start_time),
            self.current_tz,
        )
        day_end_local = timezone.make_aware(
            datetime.combine(self.target_date, end_time),
            self.current_tz,
        )

        day_start = day_start_local.astimezone(dt_timezone.utc)
        day_end = day_end_local.astimezone(dt_timezone.utc)

        # ═══════════════════════════════════════════════════════════
        #  اگه امروز، از الان شروع کن
        # ═══════════════════════════════════════════════════════════
        now_utc = timezone.now()
        now_local = timezone.localtime(now_utc)

        if self.target_date == now_local.date():
            # ─── الان (UTC) رو floor کن ───
            now_utc_floored = now_utc.replace(second=0, microsecond=0)
            if now_utc_floored > day_start:
                day_start = now_utc_floored

        # ─── ۲. بازه‌های پُر (UTC) ───
        busy_ranges = self._get_busy_ranges()

        # ─── ۳. ادغام ───
        merged_busy = self._merge_ranges(busy_ranges, day_start, day_end)

        # ─── ۴. بازه‌های آزاد ───
        free_ranges = self._get_free_ranges(day_start, day_end, merged_busy)

        # ─── ۵. اسلات‌ها (با گام duration) ───
        slots: list[SlotInfo] = []
        step = timedelta(minutes=duration)

        for free_start, free_end in free_ranges:
            current = free_start
            while current + step <= free_end:
                # ─── تبدیل به Tehran برای نمایش ───
                local_time = timezone.localtime(current).time()
                slots.append(SlotInfo(local_time, SlotStatus.AVAILABLE))
                current += step

        slots.sort(key=lambda s: s.time)
        return slots

    def is_slot_available(
        self,
        start_at: datetime,
        duration: int,
        exclude_appointment_id: int | None = None,
    ) -> bool:
        """
        چک می‌کنه یه اسلات خاص آزاده یا نه.

        ─── نکته: ───
        start_at باید aware باشه (مثلاً با timezone.make_aware ساخته شده).
        اگه aware با Tehran باشه، خودکار به UTC تبدیل میشه.
        """
        # ─── تبدیل به UTC ───
        if timezone.is_aware(start_at):
            start_utc = start_at.astimezone(dt_timezone.utc)
        else:
            start_utc = timezone.make_aware(
                start_at,
                self.current_tz,
            ).astimezone(dt_timezone.utc)

        end_utc = start_utc + timedelta(minutes=duration)

        # ═══ چک: زمان گذشته؟ ═══
        now_utc = timezone.now()
        if start_utc < now_utc:
            return False

        # ─── چک: توی ساعت کاریه؟ ───
        if not self._is_within_business_hours(start_utc, end_utc):
            return False

        # ─── چک تداخل ───
        busy_ranges = self._get_busy_ranges(
            exclude_appointment_id=exclude_appointment_id
        )
        for b_start, b_end in busy_ranges:
            if start_utc < b_end and end_utc > b_start:
                return False

        return True

    # ═══════════════════════════════════════════════════════════
    #  Business Hours
    # ═══════════════════════════════════════════════════════════

    def _get_business_hours(self) -> tuple[time, time] | None:
        """ساعت کاری روز."""
        if self._has_day_off():
            return None

        special = self._get_special_hours()
        if special:
            return (special.start_time, special.end_time)

        working = self._get_working_hours()
        if working:
            return (working.start_time, working.end_time)

        if self.station:
            fallback = AvailabilityService(
                self.business, self.target_date, station=None, staff=self.staff
            )
            return fallback._get_business_hours()

        return None

    def _has_day_off(self) -> bool:
        qs = DayOff.objects.filter(business=self.business, date=self.target_date)
        if self.station:
            qs = qs.filter(station=self.station)
        else:
            qs = qs.filter(station__isnull=True)
        return qs.exists()

    def _get_special_hours(self) -> SpecialWorkingHours | None:
        qs = SpecialWorkingHours.objects.filter(
            business=self.business, date=self.target_date
        )
        if self.station:
            qs = qs.filter(station=self.station)
        else:
            qs = qs.filter(station__isnull=True)
        return qs.first()

    def _get_working_hours(self) -> WorkingHours | None:
        iranian_weekday = Weekday.from_python_weekday(self.target_date.weekday())

        qs = WorkingHours.objects.filter(
            business=self.business,
            weekday=iranian_weekday,
            is_active=True,
        )
        if self.station:
            qs = qs.filter(station=self.station)
        else:
            qs = qs.filter(station__isnull=True)

        return qs.first()

    # ═══════════════════════════════════════════════════════════
    #  Busy Ranges (همه UTC)
    # ═══════════════════════════════════════════════════════════

    def _get_busy_ranges(
        self,
        exclude_appointment_id: int | None = None,
    ) -> list[tuple[datetime, datetime]]:
        """بازه‌های پُر = رزروها + وقفه‌ها (UTC)."""
        ranges: list[tuple[datetime, datetime]] = []
        ranges.extend(self._get_booked_ranges(exclude_appointment_id))
        ranges.extend(self._get_break_ranges())
        return ranges

    def _get_booked_ranges(
        self,
        exclude_appointment_id: int | None = None,
    ) -> list[tuple[datetime, datetime]]:
        """بازه‌های رزرو‌شده (UTC)."""
        from ..models import Appointment

        # ─── فیلتر روز ───
        day_start_local = timezone.make_aware(
            datetime.combine(self.target_date, time.min),
            self.current_tz,
        )
        day_end_local = timezone.make_aware(
            datetime.combine(self.target_date, time.max),
            self.current_tz,
        )
        day_start_utc = day_start_local.astimezone(dt_timezone.utc)
        day_end_utc = day_end_local.astimezone(dt_timezone.utc)

        qs = Appointment.objects.filter(
            business=self.business,
            start_at__gte=day_start_utc,
            start_at__lte=day_end_utc,
        ).exclude(status="cancelled")

        if self.staff:
            qs = qs.filter(staff=self.staff)
        elif self.station:
            qs = qs.filter(station=self.station)

        if exclude_appointment_id:
            qs = qs.exclude(pk=exclude_appointment_id)

        return [
            (a.start_at.astimezone(dt_timezone.utc), a.end_at.astimezone(dt_timezone.utc))
            for a in qs.only("start_at", "end_at")
        ]

    def _get_break_ranges(self) -> list[tuple[datetime, datetime]]:
        """بازه‌های وقفه (UTC)."""
        qs = Break.objects.filter(business=self.business, is_active=True)

        if self.station:
            qs = qs.filter(Q(station=self.station) | Q(station__isnull=True))
        else:
            qs = qs.filter(station__isnull=True)

        ranges = []
        for b in qs:
            start_local = timezone.make_aware(
                datetime.combine(self.target_date, b.start_time),
                self.current_tz,
            )
            end_local = timezone.make_aware(
                datetime.combine(self.target_date, b.end_time),
                self.current_tz,
            )
            ranges.append((
                start_local.astimezone(dt_timezone.utc),
                end_local.astimezone(dt_timezone.utc),
            ))

        return ranges

    # ═══════════════════════════════════════════════════════════
    #  Range Math (UTC)
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _merge_ranges(
        ranges: list[tuple[datetime, datetime]],
        day_start: datetime,
        day_end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """بازه‌ها رو ادغام کن (UTC)."""
        if not ranges:
            return []

        # ─── فیلتر بازه‌های توی روز ───
        filtered = [
            (max(s, day_start), min(e, day_end))
            for s, e in ranges
            if s < day_end and e > day_start
        ]

        if not filtered:
            return []

        # ─── مرتب‌سازی ───
        filtered.sort(key=lambda x: x[0])

        # ─── ادغام ───
        merged = [filtered[0]]
        for start, end in filtered[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged

    @staticmethod
    def _get_free_ranges(
        day_start: datetime,
        day_end: datetime,
        busy: list[tuple[datetime, datetime]],
    ) -> list[tuple[datetime, datetime]]:
        """بازه‌های آزاد = تفاضل بازه‌ی کاری و بازه‌های پُر (UTC)."""
        if not busy:
            return [(day_start, day_end)]

        free: list[tuple[datetime, datetime]] = []
        current = day_start

        for busy_start, busy_end in busy:
            if current < busy_start:
                free.append((current, busy_start))
            current = max(current, busy_end)

        if current < day_end:
            free.append((current, day_end))

        return free

    def _is_within_business_hours(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> bool:
        """چک می‌کنه توی ساعت کاریه (UTC)."""
        hours = self._get_business_hours()
        if not hours:
            return False

        open_time, close_time = hours

        day_open_local = timezone.make_aware(
            datetime.combine(self.target_date, open_time),
            self.current_tz,
        )
        day_close_local = timezone.make_aware(
            datetime.combine(self.target_date, close_time),
            self.current_tz,
        )

        day_open_utc = day_open_local.astimezone(dt_timezone.utc)
        day_close_utc = day_close_local.astimezone(dt_timezone.utc)

        return start_utc >= day_open_utc and end_utc <= day_close_utc