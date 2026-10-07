from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[("support","0001_initial"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name="PasswordResetRequest",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
        ("created_at",models.DateTimeField(auto_now_add=True,db_index=True,verbose_name="تاریخ ایجاد")),
        ("updated_at",models.DateTimeField(auto_now=True,verbose_name="آخرین ویرایش")),
        ("phone",models.CharField(db_index=True,max_length=15,verbose_name="شماره موبایل")),
        ("full_name",models.CharField(blank=True,max_length=120,verbose_name="نام")),
        ("note",models.TextField(blank=True,max_length=1000,verbose_name="توضیحات")),
        ("status",models.CharField(choices=[("open","باز"),("done","انجام شد"),("rejected","رد شد")],db_index=True,default="open",max_length=10,verbose_name="وضعیت")),
        ("handled_at",models.DateTimeField(blank=True,null=True,verbose_name="زمان رسیدگی")),
        ("handled_by",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="handled_password_reset_requests",to=settings.AUTH_USER_MODEL,verbose_name="رسیدگی‌کننده")),
        ("user",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="password_reset_requests",to=settings.AUTH_USER_MODEL,verbose_name="کاربر مرتبط")),
    ],options={"verbose_name":"درخواست بازیابی رمز","verbose_name_plural":"درخواست‌های بازیابی رمز","ordering":["-created_at"]})]
