"""
Views احراز هویت.

شامل:
- login_phone  → مرحله ۱: گرفتن شماره
- login_otp    → مرحله ۲: تأیید کد
- resend_otp   → ارسال مجدد
- logout_view  → خروج
"""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.utils.phone import mask_phone

from ..forms import LoginOTPForm, LoginPhoneForm
from ..models import User
from ..services import (
    OTPCooldownError,
    OTPError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPRateLimitError,
    send_otp,
    verify_otp,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════

SESSION_PHONE_KEY = "auth_pending_phone"
SESSION_NEXT_KEY = "auth_next_url"


# ═══════════════════════════════════════════════════════════════
#  Login Phone — مرحله ۱
# ═══════════════════════════════════════════════════════════════


@require_http_methods(["GET", "POST"])
def login_phone(request: HttpRequest) -> HttpResponse:
    """
    مرحله ۱: گرفتن شماره موبایل.

    ─── GET: ───
    نمایش فرم

    ─── POST: ───
    1. اعتبارسنجی فرم
    2. ارسال OTP
    3. ذخیره‌ی phone در session
    4. redirect به login_otp
    """
    # ─── اگه لاگینه، redirect ───
    if request.user.is_authenticated:
        return _redirect_logged_in_user(request)

    # ─── ذخیره‌ی next_url از ?next= یا referer ───
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        request.session[SESSION_NEXT_KEY] = next_url

    if request.method == "POST":
        form = LoginPhoneForm(request.POST)

        if form.is_valid():
            phone = form.cleaned_data["phone"]

            try:
                send_otp(phone, request=request)

                # ─── ذخیره در session ───
                request.session[SESSION_PHONE_KEY] = phone
                request.session.modified = True

                logger.info(f"OTP sent to {phone}")

                messages.success(
                    request,
                    _("کد ورود به شماره %(phone)s ارسال شد.") % {
                        "phone": phone
                    },
                )
                return redirect("accounts:login_otp")

            except OTPCooldownError as exc:
                messages.warning(request, str(exc))
            except OTPRateLimitError as exc:
                messages.error(request, str(exc))
            except OTPError as exc:
                messages.error(request, str(exc))
            except Exception:
                logger.exception(f"Failed to send OTP to {phone}")
                messages.error(
                    request,
                    _("خطا در ارسال کد. لطفاً دوباره امتحان کنید."),
                )
        else:
            # ─── خطاهای فرم توی template نمایش داده میشن ───
            pass
    else:
        form = LoginPhoneForm()

    return render(
        request,
        "accounts/login_phone.html",
        {"form": form},
    )


# ═══════════════════════════════════════════════════════════════
#  Login OTP — مرحله ۲
# ═══════════════════════════════════════════════════════════════


@require_http_methods(["GET", "POST"])
def login_otp(request: HttpRequest) -> HttpResponse:
    """
    مرحله ۲: تأیید کد ۶ رقمی.

    ─── چرا این view؟ ───
    کاربر شماره رو وارد کرده، OTP فرستاده شده.
    حالا باید کد رو وارد کنه.

    ─── نکته: ───
    phone از session میاد، نه از URL.
    """
    # ─── اگه لاگینه، redirect ───
    if request.user.is_authenticated:
        return _redirect_logged_in_user(request)

    # ─── اگه شماره توی session نیست، برگرد به مرحله ۱ ───
    phone = request.session.get(SESSION_PHONE_KEY)
    if not phone:
        messages.error(
            request,
            _("لطفاً اول شماره موبایلت رو وارد کن."),
        )
        return redirect("accounts:login_phone")

    if request.method == "POST":
        form = LoginOTPForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]

            try:
                # ─── تأیید OTP ───
                verify_otp(phone, code)

                # ─── پیدا یا ساخت کاربر ───
                user, created = User.objects.get_or_create(
                    phone=phone,
                    defaults={
                        "role": "customer",
                        "is_active": True,
                    },
                )

                if not user.is_active:
                    messages.error(
                        request,
                        _("حساب شما غیرفعاله. با پشتیبانی تماس بگیرید."),
                    )
                    return redirect("accounts:login_phone")

                # ─── لاگین ───
                login(
                    request,
                    user,
                    backend="apps.accounts.backends.OTPBackend",
                )

                # ─── IP ───
                user.last_login_ip = _get_client_ip(request)
                user.save(update_fields=["last_login_ip"])

                # ─── پاک کردن session ───
                next_url = request.session.pop(SESSION_NEXT_KEY, None)
                request.session.pop(SESSION_PHONE_KEY, None)

                logger.info(f"User {phone} logged in")

                if created:
                    messages.success(
                        request,
                        _("خوش آمدی! حساب کاربریت ساخته شد. ✅"),
                    )
                else:
                    messages.success(
                        request,
                        _("خوش آمدی %(name)s! ✅")
                        % {"name": user.display_name},
                    )

                # ─── redirect ───
                if next_url:
                    return redirect(next_url)

                # ─── redirect بر اساس نقش ───
                if user.is_business_owner:
                    return redirect("business:dashboard")
                return redirect("core:home")

            except OTPMaxAttemptsError as exc:
                messages.error(request, str(exc))
                return redirect("accounts:login_phone")

            except OTPInvalidError as exc:
                messages.error(request, str(exc))
                # ─── فرم رو با خطا نمایش بده ───

            except Exception:
                logger.exception(f"OTP verification failed for {phone}")
                messages.error(
                    request,
                    _("خطای غیرمنتظره. لطفاً دوباره امتحان کنید."),
                )
    else:
        form = LoginOTPForm()

    return render(
        request,
        "accounts/login_otp.html",
        {
            "form": form,
            "phone": phone,
            "phone_masked": mask_phone(phone),
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Resend OTP
# ═══════════════════════════════════════════════════════════════


@require_POST
def resend_otp(request: HttpRequest) -> HttpResponse:
    """ارسال مجدد کد."""
    phone = request.session.get(SESSION_PHONE_KEY)

    if not phone:
        messages.error(request, _("لطفاً اول شماره موبایلت رو وارد کن."))
        return redirect("accounts:login_phone")

    try:
        send_otp(phone, request=request)
        messages.success(request, _("کد جدید ارسال شد."))
    except OTPCooldownError as exc:
        messages.warning(request, str(exc))
    except OTPRateLimitError as exc:
        messages.error(request, str(exc))
    except OTPError as exc:
        messages.error(request, str(exc))
    except Exception:
        logger.exception(f"Failed to resend OTP to {phone}")
        messages.error(request, _("خطا در ارسال کد. دوباره امتحان کنید."))

    return redirect("accounts:login_otp")


# ═══════════════════════════════════════════════════════════════
#  Logout
# ═══════════════════════════════════════════════════════════════


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """خروج."""
    if request.user.is_authenticated:
        logger.info(f"User {request.user.phone} logged out")
        logout(request)

    messages.success(request, _("با موفقیت خارج شدی."))
    return redirect("core:home")


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _redirect_logged_in_user(request: HttpRequest) -> HttpResponse:
    """کاربر لاگین‌شده رو به جای مناسب بفرست."""
    user = request.user

    # ─── next_url ───
    next_url = request.session.pop(SESSION_NEXT_KEY, None)
    if next_url:
        return redirect(next_url)

    # ─── بر اساس نقش ───
    if user.is_business_owner:
        return redirect("business:dashboard")
    return redirect("core:home")


def _get_client_ip(request: HttpRequest) -> str | None:
    """گرفتن IP کاربر."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")