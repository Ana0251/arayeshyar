from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name="BlogPost",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
        ("title",models.CharField(max_length=180,verbose_name="عنوان")),
        ("slug",models.SlugField(allow_unicode=True,blank=True,max_length=210,unique=True,verbose_name="اسلاگ")),
        ("excerpt",models.CharField(blank=True,max_length=320,verbose_name="خلاصه")),
        ("body",models.TextField(verbose_name="متن مقاله")),
        ("category",models.CharField(blank=True,max_length=80,verbose_name="دسته‌بندی")),
        ("keywords",models.CharField(blank=True,help_text="با ویرگول جدا کن",max_length=300,verbose_name="کلمات کلیدی")),
        ("featured_image",models.ImageField(blank=True,null=True,upload_to="blog/",verbose_name="تصویر شاخص")),
        ("meta_title",models.CharField(blank=True,max_length=70,verbose_name="Meta title")),
        ("meta_description",models.CharField(blank=True,max_length=170,verbose_name="Meta description")),
        ("status",models.CharField(choices=[("draft","پیش‌نویس"),("published","منتشرشده")],db_index=True,default="draft",max_length=12,verbose_name="وضعیت")),
        ("published_at",models.DateTimeField(blank=True,db_index=True,null=True,verbose_name="تاریخ انتشار")),
        ("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),
        ("author",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="blog_posts",to=settings.AUTH_USER_MODEL)),
    ],options={"verbose_name":"مقاله","verbose_name_plural":"مقالات","ordering":["-published_at","-created_at"]})]
