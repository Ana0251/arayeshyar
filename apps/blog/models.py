from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

class BlogPost(models.Model):
    STATUS_CHOICES = [("draft", "پیش‌نویس"), ("published", "منتشرشده")]
    title = models.CharField("عنوان", max_length=180)
    slug = models.SlugField("اسلاگ", max_length=210, unique=True, allow_unicode=True, blank=True)
    excerpt = models.CharField("خلاصه", max_length=320, blank=True)
    body = models.TextField("متن مقاله")
    category = models.CharField("دسته‌بندی", max_length=80, blank=True)
    keywords = models.CharField("کلمات کلیدی", max_length=300, blank=True, help_text="با ویرگول جدا کن")
    featured_image = models.ImageField("تصویر شاخص", upload_to="blog/", blank=True, null=True)
    meta_title = models.CharField("Meta title", max_length=70, blank=True)
    meta_description = models.CharField("Meta description", max_length=170, blank=True)
    status = models.CharField("وضعیت", max_length=12, choices=STATUS_CHOICES, default="draft", db_index=True)
    published_at = models.DateTimeField("تاریخ انتشار", null=True, blank=True, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="blog_posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "post"
            slug = base
            n = 2
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"; n += 1
            self.slug = slug
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == "published" and self.published_at and self.published_at <= timezone.now()

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})
