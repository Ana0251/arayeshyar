"""
فرم‌های اپ business.

شامل ۱۰ فرم برای مدیریت کسب‌وکار، خدمات، ایستگاه‌ها،
ساعت کاری، روز تعطیل، ساعات خاص، وقفه، و درخواست تغییر.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.widgets import JalaliDateInput, JalaliTimeInput
from apps.core.utils.phone import normalize_phone
from apps.accounts.models import User
from .constants import ProfileField
from .models import (
    ActivityType,
    Break,
    Payment,
    Business,
    DayOff,
    Plan,
    ProfileChangeRequest,
    Service,
    Staff,
    StaffSchedule,
    StaffService,
    SpecialWorkingHours,
    Station,
    TargetAudience,
    WorkingHours,
)


# ═══════════════════════════════════════════════════════════════
#  Helper — کلاس‌های مشترک Tailwind
# ═══════════════════════════════════════════════════════════════


INPUT_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 "
    "outline-none transition"
)

TEXTAREA_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 "
    "outline-none transition resize-none"
)

CHECKBOX_CLASS = (
    "w-5 h-5 rounded border-black/20 text-accent focus:ring-accent/20"
)

SELECT_CLASS = (
    "w-full px-4 py-3 rounded-xl border border-black/10 bg-white "
    "focus:border-accent focus:ring-2 focus:ring-accent/20 "
    "outline-none transition"
)


# ═══════════════════════════════════════════════════════════════
#  BusinessProfileForm
# ═══════════════════════════════════════════════════════════════


class BusinessProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل و اطلاعات تماس صاحب کسب‌وکار."""

    login_email = forms.EmailField(
        label=_("ایمیل (اختیاری)"),
        required=False,
        disabled=False,
        help_text=_("برای ورود استفاده نمی‌شود؛ برای بازیابی حساب و اعلان‌های آینده نگهش می‌داریم."),
        widget=forms.EmailInput(attrs={"class": INPUT_CLASS, "dir": "ltr"}),
    )
    mobile = forms.CharField(
        label=_("شماره موبایل مدیر / ورود"),
        required=True,
        max_length=15,
        help_text=_("این شماره شناسه ورود شماست و برای جست‌وجو و تماس هم استفاده می‌شود."),
        widget=forms.TextInput(attrs={
            "class": INPUT_CLASS,
            "placeholder": "09123456789",
            "dir": "ltr",
            "inputmode": "numeric",
        }),
    )

    class Meta:
        model = Business
        fields = [
            "name",
            "owner_name",
            "landline",
            "region",
            "address",
            "bio",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: سالن زیبایی سارا"}
            ),
            "owner_name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: سارا محمدی"}
            ),
            "landline": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "dir": "ltr",
                    "placeholder": "021-88776655",
                }
            ),
            "region": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: ونک"}
            ),
            "address": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "خیابان، کوچه، پلاک"}
            ),
            "bio": forms.Textarea(
                attrs={
                    "class": TEXTAREA_CLASS,
                    "rows": 4,
                    "placeholder": "مثلاً: ۱۰ سال سابقه، متخصص اصلاح کلاسیک",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.owner_id:
            self.fields["login_email"].initial = self.instance.owner.email
            self.fields["mobile"].initial = self.instance.owner.phone or ""

    def clean_login_email(self):
        email = (self.cleaned_data.get("login_email") or "").strip().lower()
        if not email:
            return ""
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk and self.instance.owner_id:
            qs = qs.exclude(pk=self.instance.owner_id)
        if qs.exists():
            raise forms.ValidationError(_("این ایمیل قبلاً برای حساب دیگری ثبت شده."))
        return email

    def clean_mobile(self):
        raw = (self.cleaned_data.get("mobile") or "").strip()
        if not raw:
            return ""
        normalized = normalize_phone(raw)
        if not normalized:
            raise forms.ValidationError(_("شماره موبایل نامعتبره. فرمت صحیح: 09XXXXXXXXX"))
        qs = User.objects.filter(phone=normalized)
        if self.instance and self.instance.pk and self.instance.owner_id:
            qs = qs.exclude(pk=self.instance.owner_id)
        if qs.exists():
            raise forms.ValidationError(_("این شماره موبایل قبلاً برای حساب دیگری ثبت شده."))
        return normalized


class AvatarForm(forms.ModelForm):
    """فرم آپلود آواتار (جداگانه برای upload)."""

    class Meta:
        model = Business
        fields = ["avatar"]
        widgets = {
            "avatar": forms.FileInput(
                attrs={
                    "class": "hidden",
                    "accept": "image/*",
                    "id": "avatar-input",
                }
            ),
        }


# ═══════════════════════════════════════════════════════════════
#  ServiceForm
# ═══════════════════════════════════════════════════════════════


class ServiceForm(forms.ModelForm):
    """فرم افزودن/ویرایش خدمت."""

    class Meta:
        model = Service
        fields = ["station", "name", "duration", "price", "is_active"]
        widgets = {
            "station": forms.Select(attrs={"class": SELECT_CLASS}),
            "name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: کوتاهی مو"}
            ),
            "duration": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASS,
                    "min": 5,
                    "max": 600,
                    "step": 5,
                    "placeholder": "مثلاً: 30",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASS,
                    "min": 0,
                    "step": 10000,
                    "placeholder": "اختیاری — ۰ بذار اگه نمی‌خوای نمایش بدی",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }

    def __init__(self, *args, business=None, show_station=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business

        if business:
            self.fields["station"].queryset = business.stations.filter(
                is_active=True,
            ).order_by("order", "name")

        if not show_station:
            self.fields.pop("station", None)
        else:
            self.fields["station"].empty_label = "انتخاب اتاق / ایستگاه"
            self.fields["station"].label = _("اتاق / ایستگاه")

    def clean_station(self):
        station = self.cleaned_data.get("station")
        if self.business and station and station.business_id != self.business.id:
            raise forms.ValidationError(_("اتاق انتخاب‌شده متعلق به این کسب‌وکار نیست."))
        return station

    def clean_duration(self) -> int:
        """مدت باید بین ۵ و ۶۰۰ باشه."""
        duration = self.cleaned_data["duration"]
        if duration < 5:
            raise forms.ValidationError(_("مدت خدمت نباید کمتر از ۵ دقیقه باشه."))
        if duration > 600:
            raise forms.ValidationError(_("مدت خدمت نباید بیشتر از ۶۰۰ دقیقه باشه."))
        return duration


# ═══════════════════════════════════════════════════════════════
#  StationForm
# ═══════════════════════════════════════════════════════════════


class StationForm(forms.ModelForm):
    """
    فرم افزودن/ویرایش ایستگاه.

    ─── نکته: ───
    staff_members به‌صورت M2M هست و توی فرم اصلی نیست.
    برای انتساب کارمند به ایستگاه، از فرم جداگانه استفاده میشه.
    """

    class Meta:
        model = Station
        fields = ["name", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: اتاق رنگ"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }


# ═══════════════════════════════════════════════════════════════
#  WorkingHoursForm
# ═══════════════════════════════════════════════════════════════


class WorkingHoursForm(forms.ModelForm):
    """فرم افزودن برنامه هفتگی."""

    class Meta:
        model = WorkingHours
        fields = ["weekday", "start_time", "end_time", "is_active"]
        widgets = {
            "weekday": forms.Select(attrs={"class": SELECT_CLASS}),
            "start_time": JalaliTimeInput(),   # ← ← ← صریح
            "end_time": JalaliTimeInput(),     # ← ← ← صریح
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }


    def clean(self) -> dict:
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError(
                _("ساعت پایان باید بعد از ساعت شروع باشه.")
            )

        return cleaned


# ═══════════════════════════════════════════════════════════════
#  DayOffForm
# ═══════════════════════════════════════════════════════════════


class DayOffForm(forms.ModelForm):
    """فرم افزودن روز تعطیل."""

    class Meta:
        model = DayOff
        fields = ["date", "reason"]
        widgets = {
            "date": JalaliDateInput(),   # ← ← ← صریح
            "reason": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "مثلاً: مرخصی، عید، سفر",
                }
            ),
        }


# ═══════════════════════════════════════════════════════════════
#  SpecialWorkingHoursForm
# ═══════════════════════════════════════════════════════════════


class SpecialWorkingHoursForm(forms.ModelForm):
    """فرم افزودن ساعت خاص."""

    class Meta:
        model = SpecialWorkingHours
        fields = ["date", "start_time", "end_time", "note"]
        widgets = {
            "date": JalaliDateInput(),         # ← ← ← صریح
            "start_time": JalaliTimeInput(),   # ← ← ← صریح
            "end_time": JalaliTimeInput(),     # ← ← ← صریح
            "note": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: فقط صبح بازم"}
            ),
        }


    def clean(self) -> dict:
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError(
                _("ساعت پایان باید بعد از ساعت شروع باشه.")
            )

        return cleaned


# ═══════════════════════════════════════════════════════════════
#  BreakForm
# ═══════════════════════════════════════════════════════════════


class BreakForm(forms.ModelForm):
    """فرم افزودن وقفه استراحت."""

    class Meta:
        model = Break
        fields = ["start_time", "end_time", "label", "is_active"]
        widgets = {
            "start_time": JalaliTimeInput(),   # ← ← ← صریح
            "end_time": JalaliTimeInput(),     # ← ← ← صریح
            "label": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "مثلاً: ناهار، نماز",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }

    def clean(self) -> dict:
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError(
                _("ساعت پایان باید بعد از ساعت شروع باشه.")
            )

        return cleaned

# ═══════════════════════════════════════════════════════════════
#  ProfileChangeRequestForm
# ═══════════════════════════════════════════════════════════════


class ProfileChangeRequestForm(forms.Form):
    """
    فرم ثبت درخواست تغییر فیلد حساس.

    ─── نکته: ───
    این فرم توسط کاربر پر میشه و به ادمین میره.
    """

    field_name = forms.ChoiceField(
        label=_("فیلد مورد تغییر"),
        choices=ProfileField.choices,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    new_value_text = forms.CharField(
        label=_("مقدار جدید"),
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "class": TEXTAREA_CLASS,
                "rows": 3,
                "placeholder": "مقدار جدید رو وارد کن",
            }
        ),
    )
    new_value_file = forms.FileField(
        label=_("فایل جدید (اگه فیلد فایله)"),
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "w-full px-4 py-3 rounded-xl border border-black/10 bg-white",
                "accept": "image/*",
            }
        ),
    )


# ═══════════════════════════════════════════════════════════════
#  BusinessSearchForm
# ═══════════════════════════════════════════════════════════════


class BusinessSearchForm(forms.Form):
    """فرم جستجوی کسب‌وکار (برای مشتری)."""

    q = forms.CharField(
        label=_("جستجو"),
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "جستجوی نام، منطقه یا آدرس...",
            }
        ),
    )
    region = forms.CharField(
        label=_("منطقه"),
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASS,
                "placeholder": "مثلاً: ونک",
            }
        ),
    )


# ═══════════════════════════════════════════════════════════════
#  Register Forms (چندمرحله‌ای)
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
#  Register Forms (چندمرحله‌ای)
# ═══════════════════════════════════════════════════════════════


class RegisterAudienceForm(forms.Form):
    """مرحله ۱: انتخاب مخاطب."""

    audience_id = forms.IntegerField(widget=forms.HiddenInput)


class RegisterSalonTypeForm(forms.Form):
    """مرحله ۲: سالن داری یا شخصی؟"""

    is_salon = forms.CharField(
        max_length=5,
        widget=forms.HiddenInput,
    )

    def clean_is_salon(self) -> bool:
        """تبدیل رشته به bool."""
        val = self.cleaned_data["is_salon"]
        return val == "yes"


class RegisterActivityForm(forms.Form):
    """مرحله ۳: نوع فعالیت."""

    activity_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput,
    )
    other_activity = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.HiddenInput,
    )

    def clean(self) -> dict:
        cleaned = super().clean()
        activity_id = cleaned.get("activity_id")
        other_activity = (cleaned.get("other_activity") or "").strip()

        if not activity_id and not other_activity:
            raise forms.ValidationError(
                _("لطفاً یه فعالیت انتخاب کن یا نام فعالیتت رو بنویس.")
            )

        return cleaned


class RegisterBusinessInfoForm(forms.ModelForm):
    """مرحله ۵: اطلاعات پایه کسب‌وکار + شماره تماس مدیر."""

    owner_phone = forms.CharField(
        label=_("شماره موبایل مدیر"),
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": INPUT_CLASS,
            "type": "tel",
            "inputmode": "numeric",
            "autocomplete": "tel",
            "dir": "ltr",
            "placeholder": "09123456789",
        }),
        help_text=_("این شماره شناسه ورود مدیر و شماره تماس مجموعه است."),
    )

    class Meta:
        model = Business
        fields = [
            "name",
            "owner_name",
            "landline",
            "region",
            "address",
            "bio",
            "avatar",
            "business_license",
            "entrance_photo",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "اسم سالن یا اسم خودت"}
            ),
            "owner_name": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "اسم صاحب کسب‌وکار"}
            ),
            "landline": forms.TextInput(
                attrs={"class": INPUT_CLASS, "dir": "ltr"}
            ),
            "region": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: ونک"}
            ),
            "address": forms.TextInput(
                attrs={"class": INPUT_CLASS, "placeholder": "خیابان، کوچه، پلاک"}
            ),
            "bio": forms.Textarea(
                attrs={"class": TEXTAREA_CLASS, "rows": 3}
            ),
            "avatar": forms.FileInput(
                attrs={"class": "hidden", "accept": "image/*", "id": "avatar-input"}
            ),
            "business_license": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-black/10 bg-white",
                    "accept": "image/*",
                }
            ),
            "entrance_photo": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-black/10 bg-white",
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, is_salon: bool = False, user=None, **kwargs):
        """
        ─── پارامتر is_salon: ───
        اگه سالن نباشه، فیلدهای پروانه کسب و عکس ورودی اختیاری میشن.
        """
        super().__init__(*args, **kwargs)
        self.is_salon = is_salon
        self.user = user
        if user and user.phone and not self.is_bound:
            self.fields["owner_phone"].initial = user.phone

        if not is_salon:
            self.fields["business_license"].required = False
            self.fields["entrance_photo"].required = False

    def clean_owner_phone(self):
        phone = normalize_phone((self.cleaned_data.get("owner_phone") or "").strip())
        if not phone:
            raise forms.ValidationError(_("شماره موبایل معتبر نیست. فرمت صحیح: 09XXXXXXXXX"))
        qs = User.objects.filter(phone=phone)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError(_("این شماره موبایل قبلاً برای حساب دیگری ثبت شده."))
        return phone
            
# ═══════════════════════════════════════════════════════════════
#  PaymentForm
# ═══════════════════════════════════════════════════════════════


class PaymentForm(forms.ModelForm):
    """
    فرم ثبت پرداخت (کارت به کارت).

    ─── نکته: ───
    plan از FK به Plan میاد.
    """

    class Meta:
        model = Payment
        fields = ["plan", "receipt", "tracking_code", "customer_note"]
        widgets = {
            "plan": forms.Select(attrs={"class": SELECT_CLASS}),
            "receipt": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-xl border border-black/10 bg-white",
                    "accept": "image/*",
                    "id": "receipt-input",
                }
            ),
            "tracking_code": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "dir": "ltr",
                    "placeholder": "مثلاً: 123456789",
                }
            ),
            "customer_note": forms.Textarea(
                attrs={
                    "class": TEXTAREA_CLASS,
                    "rows": 2,
                    "placeholder": "مثلاً: از شماره ۰۹۱۲... پرداخت کردم",
                }
            ),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business

        # ─── فقط پلن‌های پولی ───
        self.fields["plan"].queryset = Plan.objects.filter(
            is_active=True,
            is_paid=True,
        ).order_by("order", "price")

        # ─── label فارسی ───
        self.fields["plan"].label_from_instance = lambda p: (
            f"{p.icon} {p.name} — {p.price:,} تومان"
        )

    def clean_receipt(self):
        receipt = self.cleaned_data.get("receipt")
        if not receipt:
            raise forms.ValidationError(_("آپلود رسید الزامیه."))
        return receipt
    
    
class StaffScheduleForm(forms.ModelForm):
    """فرم افزودن/ویرایش شیفت کارمند."""

    class Meta:
        model = StaffSchedule
        fields = ["staff", "weekday", "start_time", "end_time", "is_active"]
        widgets = {
            "staff": forms.Select(attrs={"class": SELECT_CLASS}),
            "weekday": forms.Select(attrs={"class": SELECT_CLASS}),
            "start_time": JalaliTimeInput(),
            "end_time": JalaliTimeInput(),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }

    def __init__(self, *args, business=None, station=None, **kwargs):
        """
        ─── نکته: ───
        - business: برای فیلتر کارمندها
        - station: برای ست کردن توی save
        """
        super().__init__(*args, **kwargs)
        self.business = business
        self.station = station

        if business:
            qs = Staff.objects.filter(business=business, is_active=True)
            if station:
                eligible_ids = StaffService.objects.filter(
                    staff__business=business,
                    station=station,
                    is_active=True,
                ).values_list("staff_id", flat=True)
                qs = qs.filter(pk__in=eligible_ids)
                if self.instance and self.instance.pk and self.instance.staff_id:
                    qs = Staff.objects.filter(
                        business=business,
                        pk__in=set(eligible_ids) | {self.instance.staff_id},
                    )
            self.fields["staff"].queryset = qs.distinct().order_by("order", "name")

    def clean(self) -> dict:
        """اعتبارسنجی."""
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError(
                _("ساعت پایان باید بعد از ساعت شروع باشه.")
            )

        return cleaned
    
# ═══════════════════════════════════════════════════════════════
#  StaffService Form
# ═══════════════════════════════════════════════════════════════


class StaffServiceForm(forms.ModelForm):
    """فرم افزودن/ویرایش خدمت کارمند."""

    class Meta:
        model = StaffService
        fields = ["staff", "price", "is_active"]
        widgets = {
            "staff": forms.Select(attrs={"class": SELECT_CLASS}),
            "price": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASS,
                    "min": 0,
                    "step": 10000,
                    "placeholder": "۰ = قیمت پیش‌فرض خدمت",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }

    def __init__(self, *args, business=None, station=None, service=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        self.station = station
        self.service = service

        if business:
            self.fields["staff"].queryset = Staff.objects.filter(
                business=business,
                is_active=True,
            ).order_by("order", "name")
# ═══════════════════════════════════════════════════════════════
#  Staff Management Form
# ═══════════════════════════════════════════════════════════════

class StaffManagementForm(forms.ModelForm):
    """فرم افزودن/ویرایش کارمند همراه با تخصیص خدمات."""

    services = forms.ModelMultipleChoiceField(
        label=_("خدمات قابل ارائه"),
        queryset=Service.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("خدماتی را که این کارمند ارائه می‌دهد انتخاب کن."),
    )

    class Meta:
        model = Staff
        fields = ["name", "phone", "avatar", "bio", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "مثلاً: سارا محمدی"}),
            "phone": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "09123456789", "dir": "ltr", "inputmode": "numeric"}),
            "avatar": forms.ClearableFileInput(attrs={"class": INPUT_CLASS, "accept": "image/*"}),
            "bio": forms.Textarea(attrs={"class": TEXTAREA_CLASS, "rows": 3, "placeholder": "مثلاً: متخصص رنگ و لایت"}),
            "is_active": forms.CheckboxInput(attrs={"class": CHECKBOX_CLASS}),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        if business:
            self.fields["services"].queryset = Service.objects.filter(
                business=business,
                is_active=True,
                station__is_active=True,
            ).select_related("station").order_by("station__order", "station__name", "order", "name")
            self.fields["services"].label_from_instance = (
                lambda service: f"{service.name} — {service.station.name}"
            )

        if self.instance and self.instance.pk:
            self.fields["services"].initial = Service.objects.filter(
                staff_services__staff=self.instance,
                staff_services__is_active=True,
            ).distinct()

    def clean_phone(self):
        from apps.core.utils.phone import normalize_phone
        raw = (self.cleaned_data.get("phone") or "").strip()
        if not raw:
            return ""
        normalized = normalize_phone(raw)
        if not normalized:
            raise forms.ValidationError(_("شماره موبایل نامعتبره. فرمت صحیح: 09XXXXXXXXX"))
        return normalized
