"""
Data migration — انتقال Service.staff_members (M2M) به StaffService.

─── منطق: ───
برای هر Service:
- اگه staff_members داره
- برای هر Staff:
  - یه StaffService بساز (staff, service, station, price=0)
"""

from django.db import migrations


def migrate_staff_members(apps, schema_editor):
    """انتقال داده از M2M به StaffService."""
    Service = apps.get_model("business", "Service")
    StaffService = apps.get_model("business", "StaffService")

    created_count = 0

    for service in Service.objects.prefetch_related("staff_members").all():
        # ─── station اجباری ───
        if not service.station_id:
            continue

        for staff in service.staff_members.all():
            _, created = StaffService.objects.get_or_create(
                staff=staff,
                service=service,
                station_id=service.station_id,
                defaults={
                    "price": 0,  # از Service.price استفاده میشه
                    "is_active": True,
                },
            )
            if created:
                created_count += 1

    print(f"\n   ✓ {created_count} StaffService ساخته شد.")


def reverse_migrate(apps, schema_editor):
    """Rollback — همه‌ی StaffService ها رو پاک کن."""
    StaffService = apps.get_model("business", "StaffService")
    StaffService.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("business", "0008_add_staff_service"),  # ← اسم دقیق migration قبلی
    ]

    operations = [
        migrations.RunPython(migrate_staff_members, reverse_migrate),
    ]