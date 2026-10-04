"""
Management command برای تست Race Condition.

─── هدف: ───
شبیه‌سازی چند کاربر همزمان که می‌خوان همون ساعت رو رزرو کنن.

─── انتظار: ───
فقط ۱ نفر موفق بشه، بقیه SlotNotAvailableError بگیرن.

─── استفاده: ───
    python manage.py test_race
    python manage.py test_race --concurrent=20
    python manage.py test_race --cleanup
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import time as dt_time, timedelta
from threading import Lock

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment
from apps.booking.services import BookingService, SlotNotAvailableError
from apps.business.models import (
    ActivityType,
    Business,
    Plan,
    Service,
    Staff,
    StaffService,
    Station,
    TargetAudience,
    WorkingHours,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Counter (Thread-safe)
# ═══════════════════════════════════════════════════════════════


class Counter:
    """Counter thread-safe."""

    def __init__(self):
        self.lock = Lock()
        self.success = 0
        self.slot_unavailable = 0
        self.other_errors = 0
        self.errors = []

    def record_success(self):
        with self.lock:
            self.success += 1

    def record_slot_unavailable(self, exc):
        with self.lock:
            self.slot_unavailable += 1
            if len(self.errors) < 5:
                self.errors.append(f"SlotNotAvailable: {exc}")

    def record_other_error(self, exc):
        with self.lock:
            self.other_errors += 1
            if len(self.errors) < 5:
                self.errors.append(f"{type(exc).__name__}: {exc}")


# ═══════════════════════════════════════════════════════════════
#  Command
# ═══════════════════════════════════════════════════════════════


class Command(BaseCommand):
    help = "تست Race Condition — چند کاربر همزمان"

    def add_arguments(self, parser):
        parser.add_argument(
            "--concurrent",
            type=int,
            default=10,
            help="تعداد کاربران همزمان (پیش‌فرض: 10)",
        )
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="پاک کردن داده‌های تستی بعد از پایان",
        )

    def handle(self, *args, **options):
        concurrent = options["concurrent"]
        cleanup = options["cleanup"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"🧪 تست Race Condition با {concurrent} کاربر همزمان"
            )
        )
        self.stdout.write("")

        # ═══════════════════════════════════════════════════════════
        #  آماده‌سازی داده‌های تستی
        # ═══════════════════════════════════════════════════════════
        self.stdout.write("📋 آماده‌سازی داده‌های تستی...")

        try:
            business, service, staff, customers, target_start = self._setup_data(concurrent)
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"❌ خطا در آماده‌سازی: {exc}")
            )
            import traceback

            traceback.print_exc()
            return

        self.stdout.write(f"   ✅ کسب‌وکار: {business.name}")
        self.stdout.write(f"   ✅ خدمت: {service.name} ({service.duration} دقیقه)")
        self.stdout.write(f"   ✅ کارمند: {staff.name}")
        self.stdout.write(f"   ✅ مشتری‌ها: {len(customers)} نفر")
        self.stdout.write(f"   ✅ زمان هدف: {target_start}")
        self.stdout.write("")

        # ─── چک: نوبت‌های قبلی ───
        existing = Appointment.objects.filter(
            business=business,
            start_at=target_start,
        ).exclude(status=AppointmentStatus.CANCELLED).count()

        if existing > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ {existing} نوبت قبلی توی این ساعت هست. پاک می‌کنیم..."
                )
            )
            Appointment.objects.filter(
                business=business,
                start_at=target_start,
            ).delete()

        # ═══════════════════════════════════════════════════════════
        #  اجرای همزمان
        # ═══════════════════════════════════════════════════════════
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"🚀 شروع {concurrent} درخواست همزمان..."
            )
        )
        self.stdout.write("")

        counter = Counter()
        start_time = time.time()

        # ─── برای اطمینان: همه‌ی threadها همزمان شروع بشن ───
        barrier = __import__("threading").Barrier(concurrent)

        def attempt_booking(customer):
            """یه تلاش برای رزرو."""
            # ─── بستن connection جداگانه برای هر thread ───
            try:
                barrier.wait(timeout=5)
            except Exception:
                pass

            try:
                bs = BookingService(business)
                appt = bs.create_appointment(
                    customer=customer,
                    service=service,
                    start_at=target_start,
                    staff=staff,
                )
                counter.record_success()
                return ("success", appt.pk)
            except SlotNotAvailableError as exc:
                counter.record_slot_unavailable(exc)
                return ("slot_unavailable", str(exc))
            except Exception as exc:
                counter.record_other_error(exc)
                return ("other_error", str(exc))

        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [
                executor.submit(attempt_booking, customer)
                for customer in customers
            ]

            for future in as_completed(futures):
                try:
                    future.result(timeout=30)
                except Exception as exc:
                    counter.record_other_error(exc)

        elapsed = time.time() - start_time

        # ═══════════════════════════════════════════════════════════
        #  نتیجه
        # ═══════════════════════════════════════════════════════════
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("📊 نتیجه:"))
        self.stdout.write(f"   ⏱️ زمان: {elapsed:.2f} ثانیه")
        self.stdout.write(f"   ✅ موفق: {counter.success}")
        self.stdout.write(f"   🚫 SlotNotAvailable: {counter.slot_unavailable}")
        self.stdout.write(f"   ⚠️ خطای دیگه: {counter.other_errors}")
        self.stdout.write("")

        # ─── چک نهایی: تعداد نوبت‌های ایجادشده ───
        actual_count = Appointment.objects.filter(
            business=business,
            start_at=target_start,
        ).exclude(status=AppointmentStatus.CANCELLED).count()

        self.stdout.write(f"   📌 نوبت‌های واقعی توی DB: {actual_count}")
        self.stdout.write("")

        # ─── نمایش خطاها ───
        if counter.errors:
            self.stdout.write(self.style.WARNING("📝 نمونه خطاها:"))
            for err in counter.errors:
                self.stdout.write(f"   - {err}")
            self.stdout.write("")

        # ═══════════════════════════════════════════════════════════
        #  تحلیل
        # ═══════════════════════════════════════════════════════════
        if actual_count == 1 and counter.success == 1:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅✅✅ تست موفق! فقط ۱ نوبت ساخته شد. "
                    "Race Condition درست کار می‌کنه."
                )
            )
        elif actual_count > 1:
            self.stdout.write(
                self.style.ERROR(
                    f"❌❌❌ باگ Race Condition! {actual_count} نوبت ساخته شد. "
                    f"باید فقط ۱ باشه."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ نتیجه‌ی غیرمنتظره: {actual_count} نوبت، "
                    f"{counter.success} موفق."
                )
            )

        # ═══════════════════════════════════════════════════════════
        #  پاک‌سازی
        # ═══════════════════════════════════════════════════════════
        if cleanup:
            self.stdout.write("")
            self.stdout.write("🧹 پاک‌سازی...")
            Appointment.objects.filter(business=business).delete()
            self.stdout.write("   ✅ نوبت‌ها پاک شدن.")

    # ═══════════════════════════════════════════════════════════════
    #  Setup
    # ═══════════════════════════════════════════════════════════════

    def _setup_data(self, count):
        """آماده‌سازی داده‌های تستی."""
        # ─── Plan ───
        trial_plan = Plan.objects.filter(slug="trial").first()
        if not trial_plan:
            trial_plan = Plan.objects.create(
                slug="trial",
                name="دوره تست",
                icon="🎁",
                price=0,
                duration_days=30,
                is_paid=False,
            )

        # ─── TargetAudience ───
        audience, _ = TargetAudience.objects.get_or_create(
            slug="test-audience",
            defaults={"name": "تست", "icon": "🧪"},
        )

        # ─── ActivityType ───
        activity, _ = ActivityType.objects.get_or_create(
            slug="test-activity",
            defaults={"name": "تست", "icon": "🧪", "is_salon": False},
        )

        # ─── Owner ───
        owner, _ = User.objects.get_or_create(
            phone="09120000001",
            defaults={
                "role": Role.BUSINESS_OWNER,
                "is_active": True,
            },
        )
        owner.set_unusable_password()
        owner.save()

        # ─── Business ───
        business, _ = Business.objects.get_or_create(
            owner=owner,
            defaults={
                "target_audience": audience,
                "activity_type": activity,
                "is_salon": False,
                "name": "کسب‌وکار تست Race",
                "owner_name": "تست",
                "region": "تست",
                "address": "تست",
                "plan": trial_plan,
                "plan_expires_at": timezone.localdate() + timedelta(days=30),
                "is_active": True,
                "auto_confirm": True,
            },
        )

        # ─── Station ───
        station, _ = Station.objects.get_or_create(
            business=business,
            name="محل کار",
            defaults={"order": 0},
        )

        # ─── Staff ───
        staff, _ = Staff.objects.get_or_create(
            business=business,
            is_owner=True,
            defaults={
                "name": business.owner_name,
                "phone": owner.phone,
            },
        )

        # ─── Service ───
        service, _ = Service.objects.get_or_create(
            business=business,
            station=station,
            name="خدمت تست",
            defaults={
                "duration": 30,
                "price": 100_000,
                "is_active": True,
            },
        )

        # ─── StaffService ───
        StaffService.objects.get_or_create(
            staff=staff,
            service=service,
            station=station,
            defaults={"price": 0, "is_active": True},
        )

        # ─── WorkingHours (شنبه تا چهارشنبه ۹-۲۱) ───
        for weekday in range(0, 5):
            WorkingHours.objects.get_or_create(
                business=business,
                station=None,
                weekday=weekday,
                defaults={
                    "start_time": dt_time(9, 0),
                    "end_time": dt_time(21, 0),
                    "is_active": True,
                },
            )

        # ─── زمان هدف: فردا ساعت ۱۰:۰۰ ───
        tomorrow = timezone.localdate() + timedelta(days=1)

        # ─── فردا باید توی روزهای کاری باشه ───
        # ─── اگه جمعه بود، برو شنبه ───
        while tomorrow.weekday() == 4:  # 4 = Friday in Python
            tomorrow += timedelta(days=1)

        from datetime import datetime

        naive = datetime.combine(tomorrow, dt_time(10, 0))
        target_start = timezone.make_aware(
            naive,
            timezone.get_current_timezone(),
        )

        # ─── مشتری‌ها ───
        customers = []
        for i in range(count):
            phone = f"0919000{str(i).zfill(4)}"[:11]
            customer, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "role": Role.CUSTOMER,
                    "is_active": True,
                },
            )
            if created:
                customer.set_unusable_password()
                customer.save()
            customers.append(customer)

        return business, service, staff, customers, target_start