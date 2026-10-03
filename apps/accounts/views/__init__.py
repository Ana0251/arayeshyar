"""Views اپ accounts."""

from .auth import (
    login_otp,
    login_phone,
    logout_view,
    resend_otp,
)

__all__ = [
    "login_phone",
    "login_otp",
    "resend_otp",
    "logout_view",
]