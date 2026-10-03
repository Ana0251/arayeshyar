"""
URL configuration اپ accounts.
"""

from django.urls import path

from .views import auth

app_name = "accounts"

urlpatterns = [
    # ─── ورود با OTP ───
    path("login/", auth.login_phone, name="login_phone"),
    path("login/otp/", auth.login_otp, name="login_otp"),
    path("login/resend/", auth.resend_otp, name="resend_otp"),
    # ─── خروج ───
    path("logout/", auth.logout_view, name="logout"),
]