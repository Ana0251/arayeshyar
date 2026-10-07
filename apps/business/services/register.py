"""
سرویس ثبت‌نام کسب‌وکار.

─── نکته: ───
منطق ثبت‌نام اینجا متمرکزه — views نازک می‌مونن.

─── جریان: ───
1. کاربر انتخاب‌ها رو توی session ذخیره می‌کنه
2. در مرحله‌ی آخر، یه Business ساخته میشه
3. ایستگاه‌ها و خدمات از session خونده میشن و ساخته میشن

─── نکته مهم: ───
- Staff owner خودکار توسط signal ساخته میشه
- مسئول‌های هر خدمت از طریق StaffService (نه M2M) ثبت میشن
"""

import logging
from typing import Any

from django.db import transaction
from django.utils.text import slugify

from apps.accounts.constants import Role
from apps.accounts.models import BusinessOwnerProfile, User

from ..models import (
    ActivityType,
    Business,
    Plan,
    Service,
    Staff,
    StaffService,
    Station,
    TargetAudience,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Session Keys
# ═══════════════════════════════════════════════════════════════

SESSION_KEYS = [
    "reg_audience",
    "reg_is_salon",
    "reg_activity",
    "reg_custom_activity",
    "reg_stations",
    "reg_services",
]


# ═══════════════════════════════════════════════════════════════
#  RegisterService
# ═══════════════════════════════════════════════════════════════


class RegisterService:
    """
    سرویس ثبت‌نام کسب‌وکار.

    ─── استفاده: ───
        service = RegisterService(request)
        business = service.finalize(info_data=..., files=...)
    """

    def __init__(self, request) -> None:
        self.request = request
        self.session = request.session
        self.user: User = request.user

    # ═══════════════════════════════════════════════════════════
    #  Session helpers
    # ═══════════════════════════════════════════════════════════

    def clear_session(self) -> None:
        """پاک کردن session ثبت‌نام."""
        for key in SESSION_KEYS:
            self.session.pop(key, None)

    def get(self, key: str, default: Any = None) -> Any:
        return self.session.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.session[key] = value
        self.session.modified = True

    # ═══════════════════════════════════════════════════════════
    #  Finalize — ساخت Business
    # ═══════════════════════════════════════════════════════════

    @transaction.atomic
    def finalize(
        self,
        *,
        info_data: dict,
        files: dict | None = None,
    ) -> Business:
        """
        ساخت نهایی کسب‌وکار.

        Args:
            info_data: دیکشنری اطلاعات پایه
            files: فایل‌های آپلودی

        Returns:
            Business
        """
        files = files or {}

        # ─── خواندن session ───
        audience_id = self.get("reg_audience")
        is_salon = bool(self.get("reg_is_salon", False))
        activity_id = self.get("reg_activity")
        custom_activity = self.get("reg_custom_activity", "")
        stations_data = self.get("reg_stations", []) or []
        services_data = self.get("reg_services", []) or []

        # ─── TargetAudience ───
        audience = TargetAudience.objects.get(id=audience_id)

        # ─── ActivityType ───
        if activity_id:
            activity = ActivityType.objects.get(id=activity_id)
        else:
            activity = self._get_or_create_custom_activity(
                custom_activity,
                is_salon,
            )

        # ─── Plan trial ───
        trial_plan = Plan.objects.filter(slug="trial").first()

        # ─── شماره موبایل مدیر / شناسه ورود ───
        owner_phone = info_data.get("owner_phone")
        if owner_phone and self.user.phone != owner_phone:
            self.user.phone = owner_phone
            self.user.save(update_fields=["phone"])

        # ─── Business ───
        business = Business(
            owner=self.user,
            target_audience=audience,
            activity_type=activity,
            is_salon=is_salon,
            name=info_data.get("name", ""),
            owner_name=info_data.get("owner_name", ""),
            landline=info_data.get("landline", ""),
            region=info_data.get("region", ""),
            address=info_data.get("address", ""),
            bio=info_data.get("bio", ""),
            plan=trial_plan,
            is_active=False,
        )

        # ─── فایل‌ها ───
        if files.get("avatar"):
            business.avatar = files["avatar"]
        if files.get("business_license"):
            business.business_license = files["business_license"]
        if files.get("entrance_photo"):
            business.entrance_photo = files["entrance_photo"]

        business.save()

        # ─── بعد از save، signal ها اجرا میشن ───
        business.refresh_from_db()

        # ─── ایستگاه‌ها (فقط سالن) ───
        stations = []
        if is_salon and stations_data:
            stations = self._create_stations(business, stations_data)

        # ─── انتخاب ایستگاه پیش‌فرض ───
        if stations:
            default_station = stations[0]
        else:
            default_station = business.stations.filter(is_active=True).first()
            if not default_station:
                default_station = Station.objects.create(
                    business=business,
                    name="محل کار" if not is_salon else "ایستگاه اصلی",
                    order=0,
                )

        # ─── Staff صاحب (از signal) ───
        owner_staff = business.staff.filter(is_owner=True).first()

        # ─── خدمات ───
        if services_data:
            self._create_services(
                business,
                services_data,
                default_station,
                owner_staff,
            )

        # ─── آپدیت role کاربر ───
        if self.user.role != Role.BUSINESS_OWNER:
            self.user.role = Role.BUSINESS_OWNER
            self.user.save(update_fields=["role"])
        BusinessOwnerProfile.objects.get_or_create(user=self.user)

        # ─── پاک کردن session ───
        self.clear_session()

        logger.info(
            f"Business registered: {business.name} by {self.user.email}"
        )

        return business

    # ═══════════════════════════════════════════════════════════
    #  Private
    # ═══════════════════════════════════════════════════════════

    def _get_or_create_custom_activity(
        self,
        name: str,
        is_salon: bool,
    ) -> ActivityType:
        """ساخت ActivityType برای «سایر»."""
        name = name.strip()
        if not name:
            raise ValueError("نام فعالیت سفارشی خالیه.")

        base_slug = slugify(name, allow_unicode=True) or "custom"
        slug = base_slug
        counter = 1

        while ActivityType.objects.filter(slug=slug).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"

        activity = ActivityType.objects.create(
            slug=slug,
            name=name,
            icon="✨",
            is_salon=is_salon,
            is_active=False,
            order=100,
        )

        logger.info(f"Custom ActivityType created: {name}")
        return activity

    def _create_stations(
        self,
        business: Business,
        stations_data: list[dict],
    ) -> list[Station]:
        """
        ساخت ایستگاه‌ها + Staff های مرتبط.

        ─── هر ایستگاه: ───
        - name (اجباری)
        - staff (اختیاری، اسم فرد) → Staff جدید می‌سازه
        """
        stations = []

        for idx, data in enumerate(stations_data):
            name = (data.get("name") or "").strip()
            if not name:
                continue

            station = Station.objects.create(
                business=business,
                name=name,
                order=idx,
            )
            stations.append(station)

            # ─── Staff اختیاری (فقط ساخت، بدون M2M) ───
            staff_name = (data.get("staff") or "").strip()
            if staff_name:
                Staff.objects.get_or_create(
                    business=business,
                    name=staff_name,
                    defaults={
                        "is_owner": False,
                        "order": idx,
                    },
                )

        return stations

    def _create_services(
        self,
        business: Business,
        services_data: list[dict],
        station: Station,
        owner_staff: Staff | None = None,
    ) -> list[Service]:
        """
        ساخت خدمات.

        ─── نکته: ───
        station اجباریه. صاحب کسب‌وکار به‌عنوان مسئول پیش‌فرض از
        طریق StaffService اضافه میشه.
        """
        services = []

        for idx, data in enumerate(services_data):
            name = (data.get("name") or "").strip()
            if not name:
                continue

            try:
                duration = int(data.get("duration") or 30)
            except (ValueError, TypeError):
                duration = 30

            try:
                price = int(data.get("price") or 0)
            except (ValueError, TypeError):
                price = 0

            service = Service.objects.create(
                business=business,
                station=station,
                name=name,
                duration=max(5, min(duration, 600)),
                price=max(0, price),
                order=idx,
            )

            # ─── اضافه کردن صاحب به عنوان مسئول از طریق StaffService ───
            if owner_staff:
                StaffService.objects.get_or_create(
                    staff=owner_staff,
                    service=service,
                    station=station,
                    defaults={
                        "price": 0,
                        "is_active": True,
                    },
                )

            services.append(service)

        return services