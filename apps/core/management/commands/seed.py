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
from apps.blog.models import BlogPost
from apps.business.models import (
    ActivityType,
    Break,
    Business,
    DayOff,
    Plan,
    Service,
    SpecialWorkingHours,
    Staff,
    StaffSchedule,
    StaffService,
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
            help="فقط TargetAudience و ActivityType",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("🌱 شروع seed..."))

        # پلن‌های پایه باید بعد از Reset کامل دیتابیس توسط خود seed ساخته شوند.
        # قبلاً این داده‌ها در Data Migration جداگانه ساخته می‌شدند و با حذف
        # migrationهای قدیمی دیگر وجود ندارند.
        self._create_plans()

        if options["clear"]:
            self._clear_data()

        with transaction.atomic():
            audiences = self._create_audiences()
            activities = self._create_activities()

            if not options["minimal"]:
                self._create_businesses(audiences, activities)
                self._create_customers()
                self._create_blog_posts()

        self.stdout.write(self.style.SUCCESS("✅ Seed با موفقیت انجام شد!"))
        self._print_summary()


    # ═══════════════════════════════════════════════════════════
    #  Plans
    # ═══════════════════════════════════════════════════════════

    def _create_plans(self):
        """ساخت/به‌روزرسانی پلن‌های پایه سیستم."""
        self.stdout.write("💳 ساخت پلن‌های پایه...")

        plans = [
            {
                "slug": "trial",
                "name": "دوره تست",
                "icon": "🎁",
                "description": "دوره‌ی تست ۳۰ روزه رایگان",
                "price": 0,
                "duration_days": 30,
                "features": [
                    "همه‌ی امکانات پایه",
                    "۳۰ روز رایگان",
                ],
                "order": 1,
                "is_active": True,
                "is_paid": False,
                "has_pro_features": False,
            },
            {
                "slug": "basic",
                "name": "پلن پایه",
                "icon": "⭐",
                "description": "پلن اقتصادی برای شروع",
                "price": 500_000,
                "duration_days": 30,
                "features": [
                    "نوبت‌دهی آنلاین",
                    "لینک اختصاصی + QR Code",
                    "پنل کسب‌وکار",
                    "مدیریت خدمات و ایستگاه‌ها",
                    "برنامه هفتگی",
                ],
                "order": 2,
                "is_active": True,
                "is_paid": True,
                "has_pro_features": False,
            },
            {
                "slug": "pro",
                "name": "پلن ویژه",
                "icon": "💎",
                "description": "پلن حرفه‌ای با همه‌ی امکانات",
                "price": 1_200_000,
                "duration_days": 30,
                "features": [
                    "همه‌ی امکانات پایه",
                    "یادآور پیامکی",
                    "لیست انتظار هوشمند",
                    "گزارش درآمد",
                    "ساعات طلایی",
                    "مشتریان خواب‌رفته",
                    "نوبت‌های تکراری",
                ],
                "order": 3,
                "is_active": True,
                "is_paid": True,
                "has_pro_features": True,
            },
        ]

        for data in plans:
            Plan.objects.update_or_create(
                slug=data["slug"],
                defaults=data,
            )

        self.stdout.write(self.style.SUCCESS("   ✓ پلن‌های پایه آماده شدند"))

    # ═══════════════════════════════════════════════════════════
    #  Clear
    # ═══════════════════════════════════════════════════════════

    def _clear_data(self):
        """پاک کردن داده‌های قبلی."""
        from apps.booking.models import Appointment, BlockedCustomer, WaitingList

        self.stdout.write(self.style.WARNING("🧹 پاک کردن داده‌های قبلی..."))

        Appointment.objects.all().delete()
        WaitingList.objects.all().delete()
        BlockedCustomer.objects.all().delete()
        BlogPost.objects.all().delete()

        StaffService.objects.all().delete()
        StaffSchedule.objects.all().delete()
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
            obj, _ = TargetAudience.objects.get_or_create(
                slug=item["slug"],
                defaults=item,
            )
            audiences[item["slug"]] = obj

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
            obj, _ = ActivityType.objects.get_or_create(
                slug=item["slug"],
                defaults={**item, "is_salon": False},
            )
            activities[item["slug"]] = obj

        for item in salon:
            obj, _ = ActivityType.objects.get_or_create(
                slug=item["slug"],
                defaults={**item, "is_salon": True},
            )
            activities[item["slug"]] = obj

        return activities

    # ═══════════════════════════════════════════════════════════
    #  Businesses
    # ═══════════════════════════════════════════════════════════

    def _create_businesses(self, audiences, activities):
        """ساخت کسب‌وکارهای تستی."""
        self.stdout.write("🏪 ساخت کسب‌وکارها...")

        try:
            trial_plan = Plan.objects.get(slug="trial")
            pro_plan = Plan.objects.get(slug="pro")
        except Plan.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Plan ها پیدا نشدن!"))
            return

        self._create_barber_ali(audiences["men"], activities["barber"], trial_plan)
        self._create_sara_salon(audiences["women"], activities["beauty-salon"], trial_plan)
        self._create_rose_laser(audiences["women"], activities["laser-clinic"], pro_plan)

    # ───────────────────────────────────────────────────────────
    #  Helper: Staff صاحب
    # ───────────────────────────────────────────────────────────

    def _ensure_owner_staff(self, business):
        """اطمینان از وجود Staff صاحب."""
        business.refresh_from_db()

        owner_staff = business.staff.filter(is_owner=True).first()
        if not owner_staff:
            owner_staff = Staff.objects.create(
                business=business,
                name=business.owner_name or business.name,
                phone=business.owner.phone,
                is_owner=True,
            )

        return owner_staff

    # ───────────────────────────────────────────────────────────
    #  Helper: شیفت کارمند
    # ───────────────────────────────────────────────────────────

    def _create_schedule(
        self,
        staff,
        station,
        weekday,
        start_hour,
        end_hour,
    ):
        """ساخت شیفت کارمند."""
        StaffSchedule.objects.get_or_create(
            staff=staff,
            station=station,
            weekday=weekday,
            start_time=time(start_hour, 0),
            defaults={
                "end_time": time(end_hour, 0),
                "is_active": True,
            },
        )

    # ───────────────────────────────────────────────────────────
    #  Helper: StaffService
    # ───────────────────────────────────────────────────────────

    def _link_staff_service(self, staff, service, price=0):
        """اتصال کارمند به خدمت."""
        StaffService.objects.get_or_create(
            staff=staff,
            service=service,
            station=service.station,
            defaults={
                "price": price,
                "is_active": True,
            },
        )

    # ───────────────────────────────────────────────────────────
    #  کسب‌وکار ۱: آرایشگر علی (شخصی)
    # ───────────────────────────────────────────────────────────

    def _create_barber_ali(self, audience, activity, plan):
        """آرایشگر علی (شخصی)."""
        user, created = User.objects.get_or_create(
            phone="09111111111",
            defaults={"email": "ali@arayeshyar.test", "role": Role.BUSINESS_OWNER, "is_active": True},
        )
        user.email = "ali@arayeshyar.test"
        user.role = Role.BUSINESS_OWNER
        user.set_password("123456")
        user.save(update_fields=["email", "role", "password"])

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
                "plan": plan,
                "plan_expires_at": timezone.localdate() + timedelta(days=plan.duration_days),
                "is_active": True,
                "auto_confirm": True,
            },
        )
        if not created:
            return

        self.stdout.write(f"   + {business}")

        owner_staff = self._ensure_owner_staff(business)

        station = business.stations.filter(is_active=True).first()
        if not station:
            station = Station.objects.create(
                business=business,
                name="محل کار",
                order=0,
            )

        services_data = [
            {"name": "کوتاهی مو", "duration": 30, "price": 150_000},
            {"name": "اصلاح ریش", "duration": 20, "price": 80_000},
            {"name": "رنگ مو", "duration": 90, "price": 500_000},
        ]

        for idx, s in enumerate(services_data):
            svc, _ = Service.objects.get_or_create(
                business=business,
                station=station,
                name=s["name"],
                defaults={
                    "duration": s["duration"],
                    "price": s["price"],
                    "order": idx,
                },
            )
            self._link_staff_service(owner_staff, svc)

        # ─── WorkingHours (فقط شخصی) ───
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

    def _create_sara_salon(self, audience, activity, plan):
        """سالن زیبایی سارا."""
        user, created = User.objects.get_or_create(
            phone="09122222222",
            defaults={"email": "sara@arayeshyar.test", "role": Role.BUSINESS_OWNER, "is_active": True},
        )
        user.email = "sara@arayeshyar.test"
        user.role = Role.BUSINESS_OWNER
        user.set_password("123456")
        user.save(update_fields=["email", "role", "password"])

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
                "plan": plan,
                "plan_expires_at": timezone.localdate() + timedelta(days=plan.duration_days),
                "is_active": True,
                "auto_confirm": False,
            },
        )
        if not created:
            return

        self.stdout.write(f"   + {business}")

        sara_staff = self._ensure_owner_staff(business)

        naghmeh, _ = Staff.objects.get_or_create(
            business=business, name="نرگس احمدی", defaults={"phone": "09121111111", "order": 1}
        )
        kosar, _ = Staff.objects.get_or_create(
            business=business, name="کوثر رضایی", defaults={"phone": "09122222222", "order": 2}
        )
        zainab, _ = Staff.objects.get_or_create(
            business=business, name="زینب کریمی", defaults={"phone": "09123333333", "order": 3}
        )
        maryam, _ = Staff.objects.get_or_create(
            business=business, name="مریم موسوی", defaults={"phone": "09124444444", "order": 4}
        )

        room_color, _ = Station.objects.get_or_create(
            business=business, name="اتاق رنگ", defaults={"order": 0}
        )
        room_nails, _ = Station.objects.get_or_create(
            business=business, name="اتاق ناخن", defaults={"order": 1}
        )

        # ─── شیفت‌ها ───
        for weekday in range(0, 6):
            self._create_schedule(naghmeh, room_color, weekday, 9, 14)
            self._create_schedule(kosar, room_color, weekday, 14, 21)
            self._create_schedule(zainab, room_color, weekday, 9, 17)
            self._create_schedule(maryam, room_nails, weekday, 9, 18)

        # ─── خدمات ───
        services_data = [
            {"station": room_color, "name": "هایلایت", "duration": 120, "price": 800_000, "staff": [naghmeh, kosar, zainab]},
            {"station": room_color, "name": "رنگ مو", "duration": 90, "price": 500_000, "staff": [naghmeh, kosar]},
            {"station": room_color, "name": "کوتاهی مو", "duration": 30, "price": 150_000, "staff": [sara_staff]},
            {"station": room_nails, "name": "مانیکور", "duration": 45, "price": 200_000, "staff": [maryam]},
            {"station": room_nails, "name": "پدیکور", "duration": 60, "price": 250_000, "staff": [maryam]},
        ]

        for idx, s in enumerate(services_data):
            svc, _ = Service.objects.get_or_create(
                business=business,
                station=s["station"],
                name=s["name"],
                defaults={
                    "duration": s["duration"],
                    "price": s["price"],
                    "order": idx,
                },
            )
            for staff in s["staff"]:
                self._link_staff_service(staff, svc)

    # ───────────────────────────────────────────────────────────
    #  کسب‌وکار ۳: کلینیک لیزر رز
    # ───────────────────────────────────────────────────────────

    def _create_rose_laser(self, audience, activity, plan):
        """کلینیک لیزر رز."""
        user, created = User.objects.get_or_create(
            phone="09133333333",
            defaults={"email": "rose@arayeshyar.test", "role": Role.BUSINESS_OWNER, "is_active": True},
        )
        user.email = "rose@arayeshyar.test"
        user.role = Role.BUSINESS_OWNER
        user.set_password("123456")
        user.save(update_fields=["email", "role", "password"])

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
                "plan": plan,
                "plan_expires_at": timezone.localdate() + timedelta(days=plan.duration_days),
                "is_active": True,
                "auto_confirm": True,
            },
        )
        if not created:
            return

        self.stdout.write(f"   + {business}")

        doctor = self._ensure_owner_staff(business)

        naghmeh, _ = Staff.objects.get_or_create(
            business=business, name="نرگس احمدی", defaults={"order": 1}
        )
        kosar, _ = Staff.objects.get_or_create(
            business=business, name="کوثر رضایی", defaults={"order": 2}
        )
        zainab, _ = Staff.objects.get_or_create(
            business=business, name="زینب کریمی", defaults={"order": 3}
        )

        room1, _ = Station.objects.get_or_create(
            business=business, name="اتاق ۱ (الکس)", defaults={"order": 0}
        )
        room2, _ = Station.objects.get_or_create(
            business=business, name="اتاق ۲ (دایود)", defaults={"order": 1}
        )
        room3, _ = Station.objects.get_or_create(
            business=business, name="اتاق ۳ (Nd:YAG)", defaults={"order": 2}
        )

        # ─── شیفت‌ها ───
        for weekday in range(0, 6):
            self._create_schedule(naghmeh, room1, weekday, 9, 17)
            self._create_schedule(zainab, room1, weekday, 9, 17)
            self._create_schedule(naghmeh, room2, weekday, 10, 18)
            self._create_schedule(kosar, room2, weekday, 10, 18)
            self._create_schedule(kosar, room3, weekday, 9, 15)

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
            svc, _ = Service.objects.get_or_create(
                business=business,
                station=s["station"],
                name=s["name"],
                defaults={
                    "duration": s["duration"],
                    "price": s["price"],
                    "order": idx,
                },
            )
            for staff in s["staff"]:
                self._link_staff_service(staff, svc)

    # ═══════════════════════════════════════════════════════════
    #  Customers
    # ═══════════════════════════════════════════════════════════

    def _create_customers(self):
        """ساخت مشتری‌های تستی."""
        self.stdout.write("👤 ساخت مشتری‌ها...")

        customers = [
            {"email": "zahra@arayeshyar.test", "phone": "09190000001", "name": "زهرا احمدی"},
            {"email": "fatemeh@arayeshyar.test", "phone": "09190000002", "name": "فاطمه رضایی"},
            {"email": "maryam@arayeshyar.test", "phone": "09190000003", "name": "مریم کریمی"},
        ]

        for c in customers:
            user, created = User.objects.get_or_create(
                phone=c["phone"],
                defaults={"email": c["email"], "role": Role.CUSTOMER, "is_active": True},
            )
            user.email = c["email"]
            user.role = Role.CUSTOMER
            user.set_password("123456")
            user.save(update_fields=["email", "role", "password"])

            profile = user.customer_profile
            profile.full_name = c["name"]
            profile.save(update_fields=["full_name", "updated_at"])

            if created:
                self.stdout.write(f"   + {c['name']} ({c['phone']})")


    # ═══════════════════════════════════════════════════════════
    #  Blog
    # ═══════════════════════════════════════════════════════════

    def _create_blog_posts(self):
        """ساخت/به‌روزرسانی مقاله‌های اولیه وبلاگ."""
        self.stdout.write("📝 ساخت مقاله‌های اولیه وبلاگ...")

        posts = [
            {
                "slug": "how-to-choose-a-good-salon",
                "title": "چطور یک آرایشگاه خوب انتخاب کنیم؟ ۷ نکته مهم قبل از رزرو",
                "excerpt": "برای انتخاب آرایشگاه یا سالن زیبایی مناسب، تخصص، بهداشت، قیمت، نظم و شیوه نوبت‌دهی را با هم بررسی کنید.",
                "category": "راهنمای انتخاب آرایشگاه",
                "keywords": "انتخاب آرایشگاه, سالن زیبایی خوب, آرایشگر خوب, رزرو آرایشگاه, آرایشگاه آنلاین",
                "meta_title": "چطور یک آرایشگاه خوب انتخاب کنیم؟ | آرایشیار",
                "meta_description": "۷ نکته مهم برای انتخاب آرایشگاه یا سالن زیبایی خوب؛ از تخصص و بهداشت تا قیمت، نظرات مشتریان و رزرو آنلاین.",
                "body": """انتخاب آرایشگاه یا سالن زیبایی مناسب فقط به نزدیک بودن محل آن بستگی ندارد. کیفیت خدمات، تجربه آرایشگر، بهداشت محیط، شفافیت قیمت و نظم در نوبت‌دهی می‌تواند تجربه شما را کاملاً تغییر دهد.

۱. تخصص آرایشگر را بررسی کنید
همه آرایشگرها در تمام خدمات تخصص یکسانی ندارند. ممکن است یک نفر در کوتاهی و اصلاح حرفه‌ای باشد و فرد دیگری در رنگ، کراتین یا خدمات ناخن تجربه بیشتری داشته باشد. پیش از رزرو، خدمات و تخصص فرد موردنظر را ببینید.

۲. لیست خدمات را قبل از مراجعه ببینید
مشاهده خدمات، مدت زمان تقریبی و قیمت به شما کمک می‌کند انتخاب دقیق‌تری داشته باشید و هنگام مراجعه با ابهام کمتری روبه‌رو شوید.

۳. به نظم نوبت‌دهی توجه کنید
انتظار طولانی یکی از تجربه‌های ناخوشایند مراجعه به آرایشگاه است. رزرو آنلاین باعث می‌شود زمان‌های آزاد واقعی را ببینید و ساعت مناسب خودتان را انتخاب کنید.

۴. بهداشت محیط و ابزارها را جدی بگیرید
تمیزی محیط، ابزارها و رعایت اصول بهداشتی به‌خصوص برای خدماتی که تماس مستقیم با پوست دارند اهمیت زیادی دارد.

۵. قیمت را از قبل بدانید
شفاف بودن قیمت خدمات باعث می‌شود تصمیم‌گیری آسان‌تر شود. در بعضی خدمات مثل رنگ مو ممکن است قیمت نهایی با توجه به حجم و شرایط مو تغییر کند، اما بهتر است محدوده قیمت از ابتدا مشخص باشد.

۶. نظرات مشتریان قبلی را بررسی کنید
نظر کاربران می‌تواند دید خوبی درباره کیفیت کار، رفتار پرسنل، نظم و تمیزی مجموعه بدهد. نظراتی که بعد از یک نوبت واقعی ثبت شده‌اند ارزش بیشتری دارند.

۷. مسیر رزرو باید ساده باشد
یک مجموعه حرفه‌ای بهتر است فرآیند مشخصی برای رزرو داشته باشد. در آرایشیار می‌توانید خدمات، آرایشگر و زمان مناسب را ببینید و بدون تماس‌های مکرر نوبت بگیرید.

در نهایت بهترین انتخاب، سالنی است که از نظر تخصص، زمان‌بندی، کیفیت و هزینه با نیاز شما هماهنگ باشد.""",
            },
            {
                "slug": "online-salon-booking-benefits",
                "title": "چرا رزرو آنلاین آرایشگاه بهتر از تماس تلفنی است؟",
                "excerpt": "رزرو آنلاین باعث می‌شود مشتری زمان‌های آزاد را ببیند و صاحب سالن تماس‌های کمتری برای هماهنگی نوبت پاسخ دهد.",
                "category": "رزرو آنلاین",
                "keywords": "رزرو آنلاین آرایشگاه, نوبت آرایشگاه, مدیریت نوبت, آرایشیار",
                "meta_title": "مزایای رزرو آنلاین آرایشگاه | آرایشیار",
                "meta_description": "رزرو آنلاین آرایشگاه چه مزایایی برای مشتری و صاحب سالن دارد؟ کاهش تماس، نمایش ساعت آزاد و مدیریت بهتر نوبت‌ها.",
                "body": """تماس تلفنی سال‌ها روش اصلی گرفتن نوبت آرایشگاه بوده، اما همیشه ساده نیست. ممکن است آرایشگر مشغول کار باشد، مشتری چند بار تماس بگیرد یا ساعت موردنظر هنگام هماهنگی پر شده باشد.

رزرو آنلاین این فرآیند را شفاف‌تر می‌کند. مشتری می‌تواند خدمات موجود، زمان تقریبی هر خدمت و ساعت‌های آزاد را ببیند و بدون منتظر ماندن پشت تلفن نوبت بگیرد.

برای صاحب سالن هم مزیت مهمی دارد. تماس‌های مربوط به سوال «چه ساعتی خالی دارید؟» کمتر می‌شود و زمان بیشتری برای کار اصلی باقی می‌ماند. همچنین نوبت‌ها در یک تقویم مشخص قرار می‌گیرند و احتمال اشتباه در ثبت زمان کاهش پیدا می‌کند.

در سالن‌های چندکارمندی، رزرو آنلاین کمک می‌کند ظرفیت هر کارمند جداگانه مدیریت شود. اگر یک کارمند در ساعت مشخصی نوبت داشته باشد، همان زمان برای او دوباره نمایش داده نمی‌شود.

از طرف دیگر، مشتری می‌تواند قبل از مراجعه اطلاعات لازم را ببیند و انتخاب آگاهانه‌تری داشته باشد. این موضوع به‌خصوص برای خدماتی با مدت زمان متفاوت اهمیت دارد.

آرایشیار با هدف ساده‌تر کردن همین فرآیند طراحی شده است: پیدا کردن آرایشگر، انتخاب خدمت، دیدن زمان آزاد و ثبت نوبت در چند مرحله کوتاه.""",
            },
            {
                "slug": "how-often-should-you-cut-hair",
                "title": "هر چند وقت یک‌بار باید موها را کوتاه کنیم؟",
                "excerpt": "فاصله مناسب بین دو کوتاهی مو به مدل مو، جنس مو، سلامت ساقه و هدف شما از بلند کردن مو بستگی دارد.",
                "category": "مراقبت از مو",
                "keywords": "کوتاهی مو, زمان کوتاهی مو, مراقبت مو, موخوره",
                "meta_title": "هر چند وقت موها را کوتاه کنیم؟ | آرایشیار",
                "meta_description": "فاصله مناسب بین دو کوتاهی مو برای مدل‌های کوتاه، متوسط و بلند و نکاتی برای کنترل موخوره و حفظ فرم مو.",
                "body": """یک پاسخ ثابت برای همه وجود ندارد. زمان مناسب کوتاهی مو به مدل، جنس مو و هدف شما بستگی دارد.

اگر مدل موی کوتاه و دقیق دارید، معمولاً فاصله کوتاه‌تری لازم است تا فرم مدل حفظ شود. مدل‌های متوسط می‌توانند مدت بیشتری بدون اصلاح شکل دوام بیاورند و موهای بلند معمولاً بیشتر برای مرتب کردن انتها و کنترل موخوره کوتاه می‌شوند.

وجود موخوره، خشکی زیاد در انتهای ساقه یا به‌هم‌ریختن فرم مدل می‌تواند نشانه خوبی برای زمان کوتاهی باشد. اگر در حال بلند کردن مو هستید، مرتب کردن مقدار کمی از انتهای آسیب‌دیده می‌تواند ظاهر مو را مرتب‌تر نگه دارد.

استفاده زیاد از ابزارهای حرارتی، دکلره و رنگ مکرر ممکن است ساقه مو را زودتر آسیب‌پذیر کند و نیاز به مراقبت و کوتاهی منظم‌تر را افزایش دهد.

بهتر است درباره فاصله مناسب برای مدل و جنس موی خود با آرایشگر مشورت کنید؛ چون وضعیت هر مو متفاوت است.""",
            },
            {
                "slug": "fade-vs-taper",
                "title": "فرق فید و تیپر در اصلاح مردانه چیست؟",
                "excerpt": "فید و تیپر هر دو تغییر تدریجی طول مو هستند، اما شدت کوتاهی و محدوده اجرای آن‌ها با هم تفاوت دارد.",
                "category": "اصلاح مردانه",
                "keywords": "فید, تیپر, اصلاح مردانه, مدل مو مردانه, fade taper",
                "meta_title": "تفاوت فید و تیپر در اصلاح مردانه | آرایشیار",
                "meta_description": "فید و تیپر چه فرقی دارند؟ تفاوت در میزان کوتاهی، محل محو شدن و انتخاب مناسب برای مدل موی مردانه.",
                "body": """فید و تیپر دو اصطلاح رایج در اصلاح مردانه هستند و گاهی به‌جای هم استفاده می‌شوند، اما دقیقاً یکسان نیستند.

در تیپر، طول مو به‌صورت تدریجی در بخش‌های مشخصی مثل اطراف گوش و پشت گردن کوتاه‌تر می‌شود. تغییر طول معمولاً ملایم‌تر است و بخش بیشتری از مو طول اصلی خود را حفظ می‌کند.

در فید، محو شدن می‌تواند شدیدتر باشد و مو در بخش پایینی سر تا نزدیک پوست کوتاه شود. بسته به محل شروع محوشدن، مدل‌هایی مانند Low Fade، Mid Fade و High Fade داریم.

انتخاب بین این دو به فرم صورت، مدل موی بالای سر، محیط کاری و میزان رسیدگی موردنظر شما بستگی دارد. تیپر معمولاً ظاهر کلاسیک‌تر و محافظه‌کارانه‌تری دارد و فید می‌تواند ظاهر مدرن‌تر و برجسته‌تری ایجاد کند.

اگر مطمئن نیستید کدام مدل برای شما مناسب‌تر است، چند عکس نمونه همراه داشته باشید و قبل از شروع اصلاح با آرایشگر درباره نتیجه موردنظر صحبت کنید.""",
            },
            {
                "slug": "before-hair-keratin",
                "title": "قبل از کراتین مو چه کارهایی باید انجام دهیم؟",
                "excerpt": "قبل از انجام کراتین، سابقه رنگ و دکلره، سلامت مو و نتیجه مورد انتظار را با متخصص در میان بگذارید.",
                "category": "مراقبت از مو",
                "keywords": "کراتین مو, قبل از کراتین, مراقبت مو, صافی مو",
                "meta_title": "قبل از کراتین مو چه کار کنیم؟ | آرایشیار",
                "meta_description": "نکات مهم پیش از کراتین مو؛ بررسی سلامت مو، سابقه رنگ و دکلره، انتخاب متخصص و هماهنگی درباره نتیجه مورد انتظار.",
                "body": """قبل از کراتین مو بهتر است وضعیت مو به‌درستی ارزیابی شود. موهای بسیار آسیب‌دیده، کشسان یا شکننده ممکن است به مراقبت متفاوتی نیاز داشته باشند.

سابقه رنگ، دکلره و مواد شیمیایی قبلی را به متخصص بگویید. این اطلاعات در انتخاب روش و محصول مناسب اهمیت دارد.

درباره نتیجه مورد انتظار نیز شفاف باشید. بعضی افراد صافی کامل می‌خواهند و بعضی بیشتر به دنبال کاهش وز و آسان‌تر شدن حالت‌دهی هستند.

قبل از مراجعه بهتر است دستورالعمل خود سالن را بپرسید؛ چون بسته به محصول مورد استفاده ممکن است توصیه‌ها درباره شست‌وشوی مو متفاوت باشد.

همچنین قیمت، مدت زمان انجام کار و مراقبت‌های بعد از آن را قبل از رزرو بدانید تا برای جلسه زمان کافی در نظر بگیرید.""",
            },
            {
                "slug": "hair-color-maintenance-time",
                "title": "بهترین زمان برای ترمیم رنگ مو چه موقع است؟",
                "excerpt": "زمان ترمیم رنگ مو به سرعت رشد ریشه، نوع رنگ، تفاوت رنگ پایه و وضعیت ساقه مو بستگی دارد.",
                "category": "رنگ مو",
                "keywords": "ترمیم رنگ مو, رنگ ریشه, زمان رنگ مو, مراقبت رنگ مو",
                "meta_title": "بهترین زمان ترمیم رنگ مو | آرایشیار",
                "meta_description": "چه زمانی رنگ ریشه یا رنگ مو را ترمیم کنیم؟ عوامل موثر مثل رشد مو، نوع رنگ و سلامت ساقه را بشناسید.",
                "body": """فاصله مناسب برای ترمیم رنگ مو برای همه یکسان نیست. سرعت رشد مو، رنگ طبیعی، رنگ انتخاب‌شده و تکنیک اجرا روی زمان ترمیم تاثیر دارند.

اگر اختلاف رنگ ریشه و ساقه زیاد باشد، رشد چند سانتی‌متری ریشه زودتر به چشم می‌آید. در بعضی تکنیک‌ها مانند بالیاژ، رشد ریشه طبیعی‌تر دیده می‌شود و فاصله بین دو جلسه می‌تواند بیشتر باشد.

ترمیم بیش از حد و نزدیک به هم، به‌خصوص در موهای دکلره‌شده، می‌تواند فشار بیشتری به ساقه وارد کند. بهتر است سلامت مو در کنار ظاهر رنگ در نظر گرفته شود.

استفاده از شامپوی مناسب موهای رنگ‌شده، کاهش حرارت زیاد و مراقبت از ساقه می‌تواند ماندگاری ظاهر رنگ را بهتر کند.

برای تعیین زمان دقیق، متخصص رنگ با دیدن رشد ریشه و وضعیت ساقه می‌تواند پیشنهاد مناسب‌تری بدهد.""",
            },
            {
                "slug": "choose-nail-salon",
                "title": "راهنمای انتخاب سالن مناسب برای خدمات ناخن",
                "excerpt": "برای خدمات ناخن، بهداشت ابزار، مهارت ناخن‌کار، کیفیت مواد و شفاف بودن خدمات و قیمت اهمیت زیادی دارد.",
                "category": "ناخن",
                "keywords": "سالن ناخن, ناخن کار, مانیکور, پدیکور, کاشت ناخن",
                "meta_title": "راهنمای انتخاب سالن ناخن مناسب | آرایشیار",
                "meta_description": "برای انتخاب سالن ناخن چه نکاتی مهم است؟ بهداشت ابزار، نمونه‌کار، مواد مصرفی، زمان‌بندی و قیمت را بررسی کنید.",
                "body": """در انتخاب سالن برای خدمات ناخن، ظاهر زیبا تنها معیار نیست. بهداشت ابزار و محیط اهمیت زیادی دارد. ابزارهایی که قابل ضدعفونی هستند باید به شکل مناسب تمیز شوند و وسایل یک‌بارمصرف نیز به‌درستی استفاده شوند.

نمونه‌کارهای ناخن‌کار می‌تواند سبک و دقت او را نشان دهد. اگر طرح یا فرم مشخصی مدنظر دارید، قبل از رزرو مطمئن شوید فرد موردنظر در آن سبک تجربه دارد.

نوع خدمت را هم دقیق مشخص کنید؛ مانیکور، پدیکور، ژلیش، ترمیم یا خدمات دیگر زمان و هزینه متفاوتی دارند.

شفاف بودن قیمت و مدت زمان تقریبی خدمت کمک می‌کند برنامه‌ریزی بهتری داشته باشید. رزرو آنلاین نیز می‌تواند انتخاب زمان مناسب و جلوگیری از انتظار طولانی را ساده‌تر کند.""",
            },
            {
                "slug": "how-to-find-your-barber",
                "title": "چطور آرایشگر مناسب خودمان را پیدا کنیم؟",
                "excerpt": "پیدا کردن آرایشگر مناسب ترکیبی از بررسی تخصص، سبک کاری، ارتباط خوب و تجربه چند مراجعه است.",
                "category": "راهنمای مشتری",
                "keywords": "پیدا کردن آرایشگر, آرایشگر مناسب, انتخاب آرایشگر, رزرو آرایشگر",
                "meta_title": "چطور آرایشگر مناسب پیدا کنیم؟ | آرایشیار",
                "meta_description": "برای پیدا کردن آرایشگر مناسب به تخصص، نمونه‌کار، ارتباط، قیمت و نظم نوبت‌دهی توجه کنید.",
                "body": """آرایشگر مناسب کسی است که علاوه بر مهارت فنی، بتواند نیاز و سلیقه شما را درک کند.

اول مشخص کنید دقیقاً چه خدمتی می‌خواهید. کسی که در یک حوزه تخصص دارد لزوماً بهترین انتخاب برای همه خدمات نیست.

نمونه‌کارها را بررسی کنید و ببینید سبک کاری فرد با چیزی که می‌خواهید نزدیک است یا نه. در اولین مراجعه، توضیح دقیق خواسته‌ها و نشان دادن عکس نمونه می‌تواند سوءتفاهم را کمتر کند.

نظم در زمان‌بندی هم مهم است. اگر گرفتن نوبت دشوار یا زمان انتظار همیشه زیاد باشد، حتی کیفیت خوب هم ممکن است تجربه کلی را ضعیف کند.

در آرایشیار می‌توانید آرایشگر یا سالن موردنظر را با شماره موبایل پیدا کنید، خدماتش را ببینید و زمان آزاد رزرو کنید. بعد از چند مراجعه، احتمالاً بهتر می‌توانید تشخیص دهید آیا این فرد انتخاب مناسب و ثابت شماست یا نه.""",
            },
            {
                "slug": "salon-services-and-duration-guide",
                "title": "راهنمای خدمات رایج آرایشگاه و مدت زمان تقریبی آن‌ها",
                "excerpt": "مدت زمان خدمات آرایشگاهی بسته به نوع خدمت، حجم کار و شرایط مو متفاوت است، اما دانستن زمان تقریبی برای برنامه‌ریزی مفید است.",
                "category": "راهنمای خدمات",
                "keywords": "خدمات آرایشگاه, مدت کوتاهی مو, مدت رنگ مو, مانیکور, رزرو سالن",
                "meta_title": "مدت زمان خدمات رایج آرایشگاه | آرایشیار",
                "meta_description": "زمان تقریبی خدماتی مثل کوتاهی، رنگ، هایلایت، مانیکور و پدیکور را بشناسید و برای نوبت خود بهتر برنامه‌ریزی کنید.",
                "body": """مدت زمان خدمات آرایشگاهی ثابت نیست و بسته به حجم مو، تکنیک اجرا، تجربه متخصص و جزئیات درخواست تغییر می‌کند. با این حال دانستن بازه تقریبی برای برنامه‌ریزی روزانه مفید است.

کوتاهی ساده معمولاً از خدمات کوتاه‌تر است، در حالی که رنگ کامل، هایلایت یا خدمات ترکیبی می‌توانند زمان بیشتری نیاز داشته باشند. خدمات ناخن نیز بسته به نوع مانیکور، پدیکور، طراحی یا ترمیم زمان متفاوتی دارند.

در زمان رزرو بهتر است مدت زمان درج‌شده توسط خود سالن را مبنا قرار دهید؛ چون هر مجموعه فرآیند کاری خودش را دارد.

اگر خدمت پیچیده یا تغییر بزرگ مدنظر دارید، ممکن است قبل از شروع نیاز به مشاوره کوتاه باشد. توضیح خواسته در ابتدای کار کمک می‌کند زمان و هزینه بهتر تخمین زده شود.

سامانه رزرو زمانی مفیدتر است که مدت هر خدمت در آن تعریف شده باشد؛ چون سیستم می‌تواند ساعت‌های آزاد واقعی را بر اساس همان مدت محاسبه کند.""",
            },
            {
                "slug": "what-is-arayeshyar",
                "title": "آرایشیار چیست و چطور نوبت آرایشگاه را ساده‌تر می‌کند؟",
                "excerpt": "آرایشیار سامانه‌ای برای پیدا کردن آرایشگر، مشاهده خدمات و زمان‌های آزاد و ثبت نوبت آنلاین است.",
                "category": "آرایشیار",
                "keywords": "آرایشیار, نوبت آرایشگاه, رزرو آنلاین سالن, مدیریت سالن",
                "meta_title": "آرایشیار چیست؟ رزرو آنلاین آرایشگاه و سالن",
                "meta_description": "با آرایشیار آرایشگر یا سالن را پیدا کنید، خدمات و زمان‌های آزاد را ببینید و آنلاین نوبت بگیرید. ابزار مدیریت نوبت برای صاحبان کسب‌وکار.",
                "body": """آرایشیار با هدف ساده‌تر کردن ارتباط بین مشتری و آرایشگر یا سالن طراحی شده است.

برای مشتری، مسیر اصلی ساده است: مجموعه موردنظر را پیدا می‌کند، خدمات را می‌بیند، کارمند و زمان آزاد را انتخاب می‌کند و نوبت ثبت می‌شود. به این ترتیب لازم نیست برای پرسیدن ساعت‌های خالی چند بار تماس بگیرد.

برای صاحب کسب‌وکار، نوبت‌ها، کارکنان، خدمات، اتاق‌ها، شیفت‌ها و زمان‌های کاری در یک پنل مدیریت می‌شوند. در سالن‌های چندکارمندی، ظرفیت هر فرد و خدمت جداگانه قابل مدیریت است.

لیست انتظار نیز می‌تواند برای زمان‌هایی که ظرفیت تکمیل شده کاربرد داشته باشد. اگر بعداً ظرفیت آزاد شود، صاحب مجموعه می‌تواند مشتریان منتظر را مدیریت کند.

هدف آرایشیار این است که رزرو نوبت برای مشتری سریع‌تر و مدیریت برنامه روزانه برای سالن منظم‌تر شود. امکانات جدید نیز به‌مرور بر اساس نیاز کاربران توسعه پیدا می‌کنند.""",
            },
        ]

        for data in posts:
            BlogPost.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    **data,
                    "status": "published",
                    "published_at": timezone.now(),
                },
            )

        self.stdout.write(self.style.SUCCESS(f"   ✓ {len(posts)} مقاله وبلاگ آماده شد"))

    # ═══════════════════════════════════════════════════════════
    #  Summary
    # ═══════════════════════════════════════════════════════════

    def _print_summary(self):
        """خلاصه‌ی داده‌ها."""
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("📊 خلاصه:"))
        self.stdout.write(f"   مخاطبین: {TargetAudience.objects.count()}")
        self.stdout.write(f"   انواع فعالیت: {ActivityType.objects.count()}")
        self.stdout.write(f"   پلن‌ها: {Plan.objects.count()}")
        self.stdout.write(f"   کسب‌وکارها: {Business.objects.count()}")
        self.stdout.write(f"   کارمندها: {Staff.objects.count()}")
        self.stdout.write(f"   ایستگاه‌ها: {Station.objects.count()}")
        self.stdout.write(f"   شیفت‌ها: {StaffSchedule.objects.count()}")
        self.stdout.write(f"   خدمات: {Service.objects.count()}")
        self.stdout.write(f"   خدمات per-staff: {StaffService.objects.count()}")
        self.stdout.write(f"   مشتری‌ها: {User.objects.filter(role=Role.CUSTOMER).count()}")
        self.stdout.write(f"   مقاله‌های وبلاگ: {BlogPost.objects.count()}")
        self.stdout.write("")

        self.stdout.write(self.style.MIGRATE_HEADING("🔗 لینک‌های تستی:"))
        for business in Business.objects.all():
            self.stdout.write(
                f"   {business.name}: http://127.0.0.1:8000/b/{business.slug}/book/"
            )
        self.stdout.write("")

        self.stdout.write(self.style.MIGRATE_HEADING("🔑 حساب‌های تستی — رمز همه: 123456"))
        self.stdout.write("   صاحب آرایشگر علی: 09111111111")
        self.stdout.write("   صاحب سالن سارا:   09122222222")
        self.stdout.write("   صاحب لیزر رز:     09133333333")
        self.stdout.write("   مشتری زهرا:       09190000001")
        self.stdout.write("")