"""ورود با شماره موبایل و رمز عبور + ساخت حساب اولیه صاحب کسب‌وکار."""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.utils.requests import get_client_ip
from ..constants import Role
from ..forms import BusinessSignupForm, CustomerSignupForm, PhonePasswordLoginForm, ChangePasswordForm
from ..models import CustomerProfile, User

SESSION_NEXT_KEY = "auth_next_url"


def _safe_next(request):
    value = request.GET.get("next") or request.POST.get("next")
    if value and url_has_allowed_host_and_scheme(value, {request.get_host()}, require_https=request.is_secure()):
        request.session[SESSION_NEXT_KEY] = value
        return value
    return request.session.get(SESSION_NEXT_KEY)


def _intent_from_next(next_url):
    return "business" if next_url and next_url.startswith("/register") else "login"


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    next_url = _safe_next(request)
    if request.user.is_authenticated:
        return _redirect_logged_in_user(request)

    form = PhonePasswordLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(request, username=form.cleaned_data["phone"], password=form.cleaned_data["password"])
        if user is None:
            messages.error(request, _("شماره موبایل یا رمز عبور اشتباهه."))
        elif not user.is_active:
            messages.error(request, _("این حساب غیرفعاله. با پشتیبانی تماس بگیر."))
        else:
            login(request, user)
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=["last_login_ip"])
            messages.success(request, _("خوش اومدی! ✅"))
            return _redirect_logged_in_user(request)

    return render(request, "accounts/login.html", {
        "form": form,
        "auth_intent": _intent_from_next(next_url),
        "next_url": next_url or "",
    })


@require_http_methods(["GET", "POST"])
def register_customer_account(request: HttpRequest) -> HttpResponse:
    """ثبت‌نام مستقل مشتری با موبایل و رمز؛ ایمیل اختیاری است."""
    next_url = _safe_next(request)
    if request.user.is_authenticated:
        return _redirect_logged_in_user(request)

    form = CustomerSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            phone=form.cleaned_data["phone"],
            password=form.cleaned_data["password"],
            email=form.cleaned_data.get("email"),
            role=Role.CUSTOMER,
            is_active=True,
        )
        profile, profile_created = CustomerProfile.objects.get_or_create(user=user)
        full_name = form.cleaned_data["full_name"].strip()
        if profile.full_name != full_name:
            profile.full_name = full_name
            profile.save(update_fields=["full_name", "updated_at"])
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login_ip"])
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.set_expiry(60 * 60 * 24 * 30)
        messages.success(request, _("حسابت ساخته شد. خوش اومدی! ✅"))
        return _redirect_logged_in_user(request)

    return render(request, "accounts/register_customer.html", {
        "form": form,
        "next_url": next_url or "",
    })


@require_http_methods(["GET", "POST"])
def register_business_account(request: HttpRequest) -> HttpResponse:
    """فقط حساب ورود صاحب مجموعه را می‌سازد؛ ادامه اطلاعات در wizard کسب‌وکار است."""
    if request.user.is_authenticated:
        if hasattr(request.user, "business"):
            return redirect("business:dashboard")
        return redirect("business:register_start")

    form = BusinessSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            phone=form.cleaned_data["phone"],
            password=form.cleaned_data["password"],
            email=form.cleaned_data.get("email"),
            role=Role.CUSTOMER,  # بعد از finalize ثبت کسب‌وکار به BUSINESS_OWNER تبدیل می‌شود.
        )
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login_ip"])
        login(request, user)
        messages.success(request, _("حساب ساخته شد. حالا اطلاعات آرایشگر یا سالن رو تکمیل کن. ✅"))
        return redirect("business:register_start")

    return render(request, "accounts/register_business.html", {"form": form})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        logout(request)
    messages.success(request, _("با موفقیت خارج شدی."))
    return redirect("core:home")


def _redirect_logged_in_user(request):
    next_url = request.session.pop(SESSION_NEXT_KEY, None)
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("business:dashboard") if request.user.is_business_owner else redirect("core:home")


@require_http_methods(["GET", "POST"])
def change_password(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next={request.path}")

    form = ChangePasswordForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        request.user.set_password(form.cleaned_data["new_password"])
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        messages.success(request, _("رمز عبور با موفقیت تغییر کرد. ✅"))
        return redirect("accounts:change_password")

    return render(request, "accounts/change_password.html", {"form": form})
