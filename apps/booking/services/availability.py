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

─── نکته‌ی سالن vs شخصی: ───
- سالن: ساعت کاری از StaffSchedule (شیفت کارمندها)
- شخصی: ساعت کاری از WorkingHours (برنامه هفتگی معمولی)
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
        همه‌ی اسلات‌ها با وضعیت.

        ─── حالت‌ها: ───
        1. تاریخ گذشته → []
        2. staff مشخص → فقط اسلات‌های اون کارمند
        3. staff=None + سالن → union اسلات‌های آزاد همه‌ی کارمندها
        4. شخصی → از WorkingHours
        """
        today = timezone.localdate()
        if self.target_date < today:
            return []

        # ─── ساعت کاری ───
        hours = self._get_business_hours()
        if not hours:
            return []

        start_time, end_time = hours

        day_start = timezone.make_aware(
            datetime.combine(self.target_date, start_time),
            self.current_tz,
        ).astimezone(dt_timezone.utc)

        day_end = timezone.make_aware(
            datetime.combine(self.target_date, end_time),
            self.current_tz,
        ).astimezone(dt_timezone.utc)

        # ─── اگه امروز، از الان ───
        if self.target_date == today:
            now_rounded = self._round_up_to_duration(timezone.now(), duration)
            if now_rounded > day_start:
                day_start = now_rounded

        if day_start >= day_end:
            return []

        # ─── حالت ۱: staff مشخص ───
        if self.staff:
            return self._get_slots_for_staff(
                self.staff, day_start, day_end, duration
            )

        # ─── حالت ۲: staff=None + سالن ───
        if self.business.is_salon and self.station:
            return self._get_slots_for_all_staff(
                day_start, day_end, duration
            )

        # ─── حالت ۳: شخصی ───
        return self._get_slots_legacy(day_start, day_end, duration)

    def is_slot_available(
        self,
        start_at: datetime,
        duration: int,
        exclude_appointment_id: int | None = None,
    ) -> bool:
        """
        چک می‌کنه یه اسلات خاص آزاده یا نه.
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

        # ─── چک زمان گذشته ───
        now_utc = timezone.now()
        if start_utc <= now_utc:
            return False

        # ─── چک ساعت کاری ───
        if not self._is_within_business_hours(start_utc, end_utc):
            return False

        # ─── چک شیفت کارمند (فقط سالن) ───
        if not self._is_within_staff_schedule(start_utc, end_utc):
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
    #  Slots Builders
    # ═══════════════════════════════════════════════════════════

    def _get_slots_for_staff(
        self,
        staff: Staff,
        day_start: datetime,
        day_end: datetime,
        duration: int,
    ) -> list[SlotInfo]:
        """
        اسلات‌های آزاد برای یه کارمند مشخص (فقط سالن).

        ─── برای شخصی، مستقیم _get_slots_legacy صدا زده میشه. ───
        """
        from apps.business.models import StaffSchedule

        iranian_weekday = Weekday.from_python_weekday(self.target_date.weekday())

        schedules = StaffSchedule.objects.filter(
            staff=staff,
            station=self.station,
            weekday=iranian_weekday,
            is_active=True,
        )

        if not schedules.exists():
            return []

        all_slots = []
        step = timedelta(minutes=duration)

        booked = self._get_booked_ranges_for_staff(staff)
        breaks = self._get_break_ranges()

        for schedule in schedules:
            sch_start = timezone.make_aware(
                datetime.combine(self.target_date, schedule.start_time),
                self.current_tz,
            ).astimezone(dt_timezone.utc)

            sch_end = timezone.make_aware(
                datetime.combine(self.target_date, schedule.end_time),
                self.current_tz,
            ).astimezone(dt_timezone.utc)

            sch_start = max(sch_start, day_start)
            sch_end = min(sch_end, day_end)

            if sch_start >= sch_end:
                continue

            busy = booked + breaks
            merged = self._merge_ranges(busy, sch_start, sch_end)
            free = self._get_free_ranges(sch_start, sch_end, merged)

            for free_start, free_end in free:
                current = free_start
                while current + step <= free_end:
                    local_time = timezone.localtime(current).time()
                    all_slots.append(local_time)
                    current += step

        unique_slots = sorted(set(all_slots))
        return [SlotInfo(t, SlotStatus.AVAILABLE) for t in unique_slots]

    def _get_slots_for_all_staff(
        self,
        day_start: datetime,
        day_end: datetime,
        duration: int,
    ) -> list[SlotInfo]:
        """اسلات‌های آزاد وقتی staff مشخص نیست (سالن)."""
        from apps.business.models import StaffSchedule

        iranian_weekday = Weekday.from_python_weekday(self.target_date.weekday())

        schedules = (
            StaffSchedule.objects.filter(
                station=self.station,
                weekday=iranian_weekday,
                is_active=True,
                staff__is_active=True,
            )
            .select_related("staff")
        )

        if not schedules.exists():
            return []

        all_slot_times = set()
        step = timedelta(minutes=duration)
        breaks = self._get_break_ranges()
        booked_cache: dict[int, list] = {}

        for schedule in schedules:
            staff_id = schedule.staff_id
            if staff_id not in booked_cache:
                booked_cache[staff_id] = self._get_booked_ranges_for_staff(
                    schedule.staff
                )
            booked = booked_cache[staff_id]

            sch_start = timezone.make_aware(
                datetime.combine(self.target_date, schedule.start_time),
                self.current_tz,
            ).astimezone(dt_timezone.utc)

            sch_end = timezone.make_aware(
                datetime.combine(self.target_date, schedule.end_time),
                self.current_tz,
            ).astimezone(dt_timezone.utc)

            sch_start = max(sch_start, day_start)
            sch_end = min(sch_end, day_end)

            if sch_start >= sch_end:
                continue

            busy = booked + breaks
            merged = self._merge_ranges(busy, sch_start, sch_end)
            free = self._get_free_ranges(sch_start, sch_end, merged)

            for free_start, free_end in free:
                current = free_start
                while current + step <= free_end:
                    local_time = timezone.localtime(current).time()
                    all_slot_times.add(local_time)
                    current += step

        return [
            SlotInfo(t, SlotStatus.AVAILABLE)
            for t in sorted(all_slot_times)
        ]

    def _get_slots_legacy(
        self,
        day_start: datetime,
        day_end: datetime,
        duration: int,
    ) -> list[SlotInfo]:
        """برای کسب‌وکار شخصی (از WorkingHours)."""
        busy = self._get_busy_ranges()
        merged = self._merge_ranges(busy, day_start, day_end)
        free = self._get_free_ranges(day_start, day_end, merged)

        slots = []
        step = timedelta(minutes=duration)
        for free_start, free_end in free:
            current = free_start
            while current + step <= free_end:
                local_time = timezone.localtime(current).time()
                slots.append(SlotInfo(local_time, SlotStatus.AVAILABLE))
                current += step

        return slots

    # ═══════════════════════════════════════════════════════════
    #  Helpers
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _round_up_to_duration(dt: datetime, duration: int) -> datetime:
        """رند کردن datetime به بالا بر اساس duration."""
        dt = dt.replace(second=0, microsecond=0)

        minutes = dt.minute
        remainder = minutes % duration

        if remainder != 0:
            minutes_to_add = duration - remainder
            dt = dt + timedelta(minutes=minutes_to_add)

        return dt

    # ═══════════════════════════════════════════════════════════
    #  Business Hours
    # ═══════════════════════════════════════════════════════════

    def _get_business_hours(self) -> tuple[time, time] | None:
        """
        ساعت کاری روز.

        ─── منطق: ───
        1. اگه روز تعطیله → None
        2. اگه ساعت خاص هست → از SpecialWorkingHours
        3. اگه سالن و station هست → union شیفت‌های کارمندها
        4. اگه شخصی → از WorkingHours
        """
        # ─── چک تعطیلی ───
        if self._has_day_off():
            return None

        # ─── چک ساعت خاص ───
        special = self._get_special_hours()
        if special:
            return (special.start_time, special.end_time)

        # ═══════════════════════════════════════════════════════════
        #  سالن: از StaffSchedule
        # ═══════════════════════════════════════════════════════════
        if self.business.is_salon and self.station:
            schedules = self._get_station_schedules()
            if schedules:
                min_start = min(s[0] for s in schedules)
                max_end = max(s[1] for s in schedules)
                return (min_start, max_end)

        # ═══════════════════════════════════════════════════════════
        #  شخصی (یا سالن بدون شیفت): از WorkingHours
        # ═══════════════════════════════════════════════════════════
        working = self._get_working_hours_legacy()
        if working:
            return (working.start_time, working.end_time)

        return None

    def _get_station_schedules(self) -> list[tuple[time, time]]:
        """شیفت‌های کارمندهای یه اتاق برای یه روز (فقط سالن)."""
        from apps.business.models import StaffSchedule

        iranian_weekday = Weekday.from_python_weekday(self.target_date.weekday())

        qs = StaffSchedule.objects.filter(
            station=self.station,
            weekday=iranian_weekday,
            is_active=True,
        )

        if self.staff:
            qs = qs.filter(staff=self.staff)

        return [(s.start_time, s.end_time) for s in qs]

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

    def _get_working_hours_legacy(self) -> WorkingHours | None:
        """
     برنامه هفتگی (فقط شخصی).

        ─── نکته: ───
    برای کسب‌وکار شخص    ی، WorkingHours همیشه station=None داره.
    پس اگه سالن نباش    ه، station رو نادیده می‌گیریم.
        """
        iranian_weekday = Weekday.from_python_weekday(self.target_date.weekday())

        qs = WorkingHours.objects.filter(
            business=self.business,
            weekday=iranian_weekday,
            is_active=True,
        )

        # ─── فقط برای سالن‌ها station رو فیلتر کن ───
        if self.business.is_salon and self.station:
            qs = qs.filter(station=self.station)
        else:
            qs = qs.filter(station__isnull=True)

        return qs.first()

    def _is_within_staff_schedule(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> bool:
        """
        چک می‌کنه اسلات توی شیفت کارمند باشه.

        ─── نکته: ───
        - برای شخصی: همیشه True (شیفت معنی نداره)
        - برای سالن بدون staff: True (چک جداگانه در _get_slots_for_all_staff)
        - برای سالن با staff: چک واقعی
        """
        # ─── شخصی یا بدون staff → True ───
        if not self.business.is_salon:
            return True

        if not self.staff:
            return True

        from apps.business.models import StaffSchedule

        iranian_weekday = Weekday.from_python_weekday(self.target_date.weekday())

        schedules = StaffSchedule.objects.filter(
            staff=self.staff,
            station=self.station,
            weekday=iranian_weekday,
            is_active=True,
        )

        for schedule in schedules:
            sch_start_utc = timezone.make_aware(
                datetime.combine(self.target_date, schedule.start_time),
                self.current_tz,
            ).astimezone(dt_timezone.utc)

            sch_end_utc = timezone.make_aware(
                datetime.combine(self.target_date, schedule.end_time),
                self.current_tz,
            ).astimezone(dt_timezone.utc)

            if start_utc >= sch_start_utc and end_utc <= sch_end_utc:
                return True

        return False

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
            (
                a.start_at.astimezone(dt_timezone.utc),
                a.end_at.astimezone(dt_timezone.utc),
            )
            for a in qs.only("start_at", "end_at")
        ]

    def _get_booked_ranges_for_staff(
        self,
        staff: Staff,
        exclude_appointment_id: int | None = None,
    ) -> list[tuple[datetime, datetime]]:
        """بازه‌های رزرو‌شده برای یه کارمند خاص (UTC)."""
        from ..models import Appointment

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
            staff=staff,
            start_at__gte=day_start_utc,
            start_at__lte=day_end_utc,
        ).exclude(status="cancelled")

        if exclude_appointment_id:
            qs = qs.exclude(pk=exclude_appointment_id)

        return [
            (
                a.start_at.astimezone(dt_timezone.utc),
                a.end_at.astimezone(dt_timezone.utc),
            )
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

        filtered = [
            (max(s, day_start), min(e, day_end))
            for s, e in ranges
            if s < day_end and e > day_start
        ]

        if not filtered:
            return []

        filtered.sort(key=lambda x: x[0])

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

        day_open_utc = timezone.make_aware(
            datetime.combine(self.target_date, open_time),
            self.current_tz,
        ).astimezone(dt_timezone.utc)

        day_close_utc = timezone.make_aware(
            datetime.combine(self.target_date, close_time),
            self.current_tz,
        ).astimezone(dt_timezone.utc)

        return start_utc >= day_open_utc and end_utc <= day_close_utc