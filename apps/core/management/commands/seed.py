"""
مدیریت command برای پر کردن دیتابیس با داده‌ی تستی.

─── استفاده: ───
    python manage.py seed                # داده‌ی کامل
    python manage.py seed --clear        # پاک کردن + داده‌ی جدید
    python manage.py seed --minimal      # فقط TargetAudience و ActivityType
"""

from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.business.constants import Plan
from apps.business.models import (
    ActivityType,
    Break,
    Business,
    DayOff,
    Service,
    SpecialWorkingHours,
    Staff,
    Station,
    TargetAudience,
    WorkingHours,
)


# ═══════════════════════════════════════════════════════════════
#  Command
# ═══════════════════════════════════════════════════════════════


class Command(BaseCommand):
    help = "پر کردن دیتابیس با داده‌ی تستی"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="پاک کردن داده‌های قبلی قبل از seed",
        )
        parser.add_argument(
            "--minimal",
            action="store_true",
            help="فقط TargetAudience و ActivityType (بدون کسب‌وکار)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🌱 شروع seed..."))

        if options["clear"]:
            self._clear_data()

        with transaction.atomic():
            audiences = self._create_audiences()
            activities = self._create_activities()

            if not options["minimal"]:
                self._create_businesses(audiences, activities)
                self._create_customers()

        self.stdout.write(self.style.SUCCESS("✅ Seed با موفقیت انجام شد!"))
        self._print_summary()

    # ═══════════════════════════════════════════════════════════
    #  Clear
    # ═══════════════════════════════════════════════════════════

    def _clear_data(self):
        """پاک کردن داده‌های قبلی."""
        from apps.booking.models import Appointment, BlockedCustomer, WaitingList

        self.stdout.write(self.style.WARNING("🧹 پاک کردن داده‌های قبلی..."))

        # ─── به ترتیب وابستگی ───
        Appointment.objects.all().delete()
        WaitingList.objects.all().delete()
        BlockedCustomer.objects.all().delete()

        Service.objects.all().delete()
        Station.objects.all().delete()

        WorkingHours.objects.all().delete()
        DayOff.objects.all().delete()
        SpecialWorkingHours.objects.all().delete()
        Break.objects.all().delete()

        Staff.objects.all().delete()
        Business.objects.all().delete()

        User.objects.filter(role=Role.CUSTOMER).delete()
        User.objects.filter(role=Role.BUSINESS_OWNER).delete()

        self.stdout.write(self.style.SUCCESS("   ✓ پاک شد"))

    # ═══════════════════════════════════════════════════════════
    #  TargetAudience
    # ═══════════════════════════════════════════════════════════

    def _create_audiences(self):
        """ساخت مخاطبین."""
        self.stdout.write("👥 ساخت مخاطبین...")

        data = [
            {"slug": "men", "name": "آقایان", "icon": "👨", "order": 1},
            {"slug": "women", "name": "بانوان", "icon": "👩", "order": 2},
            {"slug": "both", "name": "هردو", "icon": "👫", "order": 3},
            {"slug": "kids", "name": "کودکان", "icon": "🧒", "order": 4},
        ]

        audiences = {}
        for item in data:
            obj, created = TargetAudience.objects.get_or_create(
                slug=item["slug"],
                defaults=item,
            )
            audiences[item["slug"]] = obj
            if created:
                self.stdout.write(f"   + {obj}")

        return audiences

    # ═══════════════════════════════════════════════════════════
    #  ActivityType
    # ═══════════════════════════════════════════════════════════

    def _create_activities(self):
        """ساخت انواع فعالیت."""
        self.stdout.write("💼 ساخت انواع فعالیت...")

        personal = [
            {"slug": "barber", "name": "آرایشگر مردانه", "icon": "💈", "order": 1},
            {"slug": "hairdresser", "name": "آرایشگر زنانه", "icon": "💇", "order": 2},
            {"slug": "nails", "name": "ناخن‌کار", "icon": "💅", "order": 3},
            {"slug": "tattoo", "name": "تتو کار", "icon": "🖋️", "order": 4},
            {"slug": "massage", "name": "ماساژور", "icon": "💆", "order": 5},
            {"slug": "waxing", "name": "اپیلاسیون", "icon": "✨", "order": 6},
        ]

        salon = [
            {"slug": "beauty-salon", "name": "سالن زیبایی", "icon": "🏢", "order": 1},
            {"slug": "laser-clinic", "name": "کلینیک لیزر", "icon": "⚡", "order": 2},
            {"slug": "massage-salon", "name": "سالن ماساژ", "icon": "💆", "order": 3},
            {"slug": "nail-salon", "name": "سالن ناخن", "icon": "💅", "order": 4},
        ]

        activities = {}
        for item in personal:
            obj, created = ActivityType.objects.get_or_create(
                slug=item["slug"],
                defaults={**item, "is_salon": False},
            )
            activities[item["slug"]] = obj
            if created:
                self.stdout.write(f"   + {obj}")

        for item in salon:
            obj, created = ActivityType.objects.get_or_create(
                slug=item["slug"],
                defaults={**item, "is_salon": True},
            )
            activities[item["slug"]] = obj
            if created:
                self.stdout.write(f"   + {obj}")

        return activities

    # ═══════════════════════════════════════════════════════════
    #  Businesses
    # ═══════════════════════════════════════════════════════════

    def _create_businesses(self, audiences, activities):
        """ساخت کسب‌وکارهای تستی."""
        self.stdout.write("🏪 ساخت کسب‌وکارها...")

        self._create_barber_ali(audiences["men"], activities["barber"])
        self._create_sara_salon(audiences["women"], activities["beauty-salon"])
        self._create_rose_laser(audiences["women"], activities["laser-clinic"])

    # ───────────────────────────────────────────────────────────
    #  Helper: اطمینان از وجود Station و Staff
    # ───────────────────────────────────────────────────────────

    def _ensure_station_and_staff(self, business):
        """
        اطمینان از وجود Station و Staff برای کسب‌وکار.

        ─── چرا؟ ───
        سیگنال post_save ممکنه Station رو نساخته باشه (اگه business از
        قبل وجود داشته). اینجا دستی چک می‌کنیم.
        """
        business.refresh_from_db()

        # ─── Staff صاحب ───
        owner_staff = business.staff.filter(is_owner=True).first()
        if not owner_staff:
            owner_staff = Staff.objects.create(
                business=business,
                name=business.owner_name or business.name,
                phone=business.owner.phone,
                is_owner=True,
            )
            self.stdout.write(
                self.style.WARNING(f"   ⚠️ Staff صاحب برای {business.name} ساخته شد")
            )

        # ─── Station پیش‌فرض (اگه شخصی) ───
        station = business.stations.filter(is_active=True).first()
        if not station:
            station = Station.objects.create(
                business=business,
                name="محل کار",
                order=0,
            )
            self.stdout.write(
                self.style.WARNING(f"   ⚠️ Station پیش‌فرض برای {business.name} ساخته شد")
            )

        return station, owner_staff

    # ───────────────────────────────────────────────────────────
    #  کسب‌وکار ۱: آرایشگر علی (شخصی)
    # ───────────────────────────────────────────────────────────

    def _create_barber_ali(self, audience, activity):
        """آرایشگر علی (شخصی)."""
        user, created = User.objects.get_or_create(
            phone="09111111111",
            defaults={"role": Role.BUSINESS_OWNER, "is_active": True},
        )
        if created:
            user.set_unusable_password()
            user.save()

        business, created = Business.objects.get_or_create(
            owner=user,
            defaults={
                "target_audience": audience,
                "activity_type": activity,
                "is_salon": False,
                "name": "آرایشگر علی",
                "owner_name": "علی رضایی",
                "region": "ونک",
                "address": "خیابان ونک، پلاک ۱۲",
                "bio": "۱۰ سال سابقه، متخصص اصلاح کلاسیک",
                "plan": Plan.TRIAL,
                "plan_expires_at": timezone.localdate() + timedelta(days=30),
                "is_active": True,
                "auto_confirm": True,
            },
        )
        if not created:
            return

        self.stdout.write(f"   + {business}")

        station, owner_staff = self._ensure_station_and_staff(business)

        # ─── خدمات ───
        services_data = [
            {"name": "کوتاهی مو", "duration": 30, "price": 150_000},
            {"name": "اصلاح ریش", "duration": 20, "price": 80_000},
            {"name": "رنگ مو", "duration": 90, "price": 500_000},
        ]

        for idx, s in enumerate(services_data):
            svc, svc_created = Service.objects.get_or_create(
                business=business,
                station=station,
                name=s["name"],
                defaults={
                    "duration": s["duration"],
                    "price": s["price"],
                    "order": idx,
                },
            )
            if svc_created:
                svc.staff_members.add(owner_staff)

        # ─── برنامه هفتگی ───
        for weekday in range(0, 5):
            WorkingHours.objects.get_or_create(
                business=business,
                station=None,
                weekday=weekday,
                defaults={
                    "start_time": time(9, 0),
                    "end_time": time(21, 0),
                    "is_active": True,
                },
            )

    # ───────────────────────────────────────────────────────────
    #  کسب‌وکار ۲: سالن زیبایی سارا
    # ───────────────────────────────────────────────────────────

    def _create_sara_salon(self, audience, activity):
        """سالن زیبایی سارا."""
        user, created = User.objects.get_or_create(
            phone="09122222222",
            defaults={"role": Role.BUSINESS_OWNER, "is_active": True},
        )
        if created:
            user.set_unusable_password()
            user.save()

        business, created = Business.objects.get_or_create(
            owner=user,
            defaults={
                "target_audience": audience,
                "activity_type": activity,
                "is_salon": True,
                "name": "سالن زیبایی سارا",
                "owner_name": "سارا محمدی",
                "region": "سعادت‌آباد",
                "address": "بلوار سعادت‌آباد، پلاک ۴۵",
                "bio": "سالن تخصصی زیبایی و آرایش",
                "plan": Plan.TRIAL,
                "is_active": True,
                "auto_confirm": False,
            },
        )
        if not created:
            return

        self.stdout.write(f"   + {business}")

        # ─── اطمینان از Staff صاحب ───
        _, sara_staff = self._ensure_station_and_staff(business)

        # ─── کارمندها ───
        naghmeh, _ = Staff.objects.get_or_create(
            business=business,
            name="نرگس احمدی",
            defaults={"phone": "09121111111", "order": 1},
        )
        kosar, _ = Staff.objects.get_or_create(
            business=business,
            name="کوثر رضایی",
            defaults={"phone": "09122222222", "order": 2},
        )
        zainab, _ = Staff.objects.get_or_create(
            business=business,
            name="زینب کریمی",
            defaults={"phone": "09123333333", "order": 3},
        )
        maryam, _ = Staff.objects.get_or_create(
            business=business,
            name="مریم موسوی",
            defaults={"phone": "09124444444", "order": 4},
        )

        # ─── اتاق‌ها ───
        room_color, _ = Station.objects.get_or_create(
            business=business,
            name="اتاق رنگ",
            defaults={"order": 0},
        )
        room_color.staff_members.set([naghmeh, kosar, zainab, sara_staff])

        room_nails, _ = Station.objects.get_or_create(
            business=business,
            name="اتاق ناخن",
            defaults={"order": 1},
        )
        room_nails.staff_members.set([maryam])

        # ─── خدمات ───
        services_data = [
            {"station": room_color, "name": "هایلایت", "duration": 120, "price": 800_000, "staff": [naghmeh, kosar, zainab]},
            {"station": room_color, "name": "رنگ مو", "duration": 90, "price": 500_000, "staff": [naghmeh, kosar]},
            {"station": room_color, "name": "کوتاهی مو", "duration": 30, "price": 150_000, "staff": [sara_staff]},
            {"station": room_nails, "name": "مانیکور", "duration": 45, "price": 200_000, "staff": [maryam]},
            {"station": room_nails, "name": "پدیکور", "duration": 60, "price": 250_000, "staff": [maryam]},
        ]

        for idx, s in enumerate(services_data):
            svc, svc_created = Service.objects.get_or_create(
                business=business,
                station=s["station"],
                name=s["name"],
                defaults={
                    "duration": s["duration"],
                    "price": s["price"],
                    "order": idx,
                },
            )
            if svc_created:
                svc.staff_members.set(s["staff"])

        # ─── برنامه هفتگی ───
        for weekday in range(0, 6):
            WorkingHours.objects.get_or_create(
                business=business,
                station=None,
                weekday=weekday,
                defaults={
                    "start_time": time(9, 0),
                    "end_time": time(21, 0),
                    "is_active": True,
                },
            )

    # ───────────────────────────────────────────────────────────
    #  کسب‌وکار ۳: کلینیک لیزر رز
    # ───────────────────────────────────────────────────────────

    def _create_rose_laser(self, audience, activity):
        """کلینیک لیزر رز."""
        user, created = User.objects.get_or_create(
            phone="09133333333",
            defaults={"role": Role.BUSINESS_OWNER, "is_active": True},
        )
        if created:
            user.set_unusable_password()
            user.save()

        business, created = Business.objects.get_or_create(
            owner=user,
            defaults={
                "target_audience": audience,
                "activity_type": activity,
                "is_salon": True,
                "name": "کلینیک لیزر رز",
                "owner_name": "دکتر سارا محمدی",
                "region": "سعادت‌آباد",
                "address": "بلوار دریا، پلاک ۸۸",
                "bio": "لیزر تخصصی با آخرین تکنولوژی",
                "plan": Plan.PRO,
                "is_active": True,
                "auto_confirm": True,
            },
        )
        if not created:
            return

        self.stdout.write(f"   + {business}")

        # ─── اطمینان از Staff صاحب ───
        _, doctor = self._ensure_station_and_staff(business)

        # ─── اپراتورها ───
        naghmeh, _ = Staff.objects.get_or_create(
            business=business, name="نرگس احمدی", defaults={"order": 1}
        )
        kosar, _ = Staff.objects.get_or_create(
            business=business, name="کوثر رضایی", defaults={"order": 2}
        )
        zainab, _ = Staff.objects.get_or_create(
            business=business, name="زینب کریمی", defaults={"order": 3}
        )

        # ─── اتاق‌ها ───
        room1, _ = Station.objects.get_or_create(
            business=business, name="اتاق ۱ (الکس)", defaults={"order": 0}
        )
        room1.staff_members.set([naghmeh, zainab])

        room2, _ = Station.objects.get_or_create(
            business=business, name="اتاق ۲ (دایود)", defaults={"order": 1}
        )
        room2.staff_members.set([naghmeh, kosar])

        room3, _ = Station.objects.get_or_create(
            business=business, name="اتاق ۳ (Nd:YAG)", defaults={"order": 2}
        )
        room3.staff_members.set([kosar])

        # ─── خدمات ───
        services_data = [
            {"station": room1, "name": "لیزر مو — بازو", "duration": 30, "price": 500_000, "staff": [naghmeh, zainab]},
            {"station": room1, "name": "لیزر مو — پا", "duration": 60, "price": 800_000, "staff": [naghmeh, zainab]},
            {"station": room2, "name": "لیزر صورت", "duration": 20, "price": 400_000, "staff": [naghmeh, kosar]},
            {"station": room2, "name": "لیزر مو — پا", "duration": 45, "price": 700_000, "staff": [naghmeh, kosar]},
            {"station": room3, "name": "لیزر مو — زیربغل", "duration": 15, "price": 300_000, "staff": [kosar]},
            {"station": room2, "name": "مشاوره رایگان", "duration": 15, "price": 0, "staff": [doctor]},
        ]

        for idx, s in enumerate(services_data):
            svc, svc_created = Service.objects.get_or_create(
                business=business,
                station=s["station"],
                name=s["name"],
                defaults={
                    "duration": s["duration"],
                    "price": s["price"],
                    "order": idx,
                },
            )
            if svc_created:
                svc.staff_members.set(s["staff"])

        # ─── برنامه هفتگی ───
        for weekday in range(0, 6):
            WorkingHours.objects.get_or_create(
                business=business,
                station=None,
                weekday=weekday,
                defaults={
                    "start_time": time(9, 0),
                    "end_time": time(21, 0),
                    "is_active": True,
                },
            )

    # ═══════════════════════════════════════════════════════════
    #  Customers
    # ═══════════════════════════════════════════════════════════

    def _create_customers(self):
        """ساخت مشتری‌های تستی."""
        self.stdout.write("👤 ساخت مشتری‌ها...")

        customers = [
            {"phone": "09190000001", "name": "زهرا احمدی"},
            {"phone": "09190000002", "name": "فاطمه رضایی"},
            {"phone": "09190000003", "name": "مریم کریمی"},
        ]

        for c in customers:
            user, created = User.objects.get_or_create(
                phone=c["phone"],
                defaults={"role": Role.CUSTOMER, "is_active": True},
            )
            if created:
                user.set_unusable_password()
                user.save()

                profile = user.customer_profile
                profile.full_name = c["name"]
                profile.save()

                self.stdout.write(f"   + {c['name']} ({c['phone']})")

    # ═══════════════════════════════════════════════════════════
    #  Summary
    # ═══════════════════════════════════════════════════════════

    def _print_summary(self):
        """خلاصه‌ی داده‌ها."""
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("📊 خلاصه:"))
        self.stdout.write(f"   مخاطبین: {TargetAudience.objects.count()}")
        self.stdout.write(f"   انواع فعالیت: {ActivityType.objects.count()}")
        self.stdout.write(f"   کسب‌وکارها: {Business.objects.count()}")
        self.stdout.write(f"   کارمندها: {Staff.objects.count()}")
        self.stdout.write(f"   ایستگاه‌ها: {Station.objects.count()}")
        self.stdout.write(f"   خدمات: {Service.objects.count()}")
        self.stdout.write(f"   مشتری‌ها: {User.objects.filter(role=Role.CUSTOMER).count()}")
        self.stdout.write("")

        self.stdout.write(self.style.MIGRATE_HEADING("🔗 لینک‌های تستی:"))
        for business in Business.objects.all():
            self.stdout.write(
                f"   {business.name}: http://127.0.0.1:8000/b/{business.slug}/book/"
            )
        self.stdout.write("")

        self.stdout.write(self.style.MIGRATE_HEADING("🔑 لاگین:"))
        self.stdout.write("   صاحب آرایشگر علی: 09111111111")
        self.stdout.write("   صاحب سالن سارا:  09122222222")
        self.stdout.write("   صاحب لیزر رز:   09133333333")
        self.stdout.write("   مشتری زهرا:     09190000001")
        self.stdout.write("")