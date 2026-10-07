from django.urls import path
from .views import auth

app_name = "accounts"
urlpatterns = [
    path("login/", auth.login_view, name="login"),
    # alias برای لینک‌های قدیمی تا چیزی نشکند
    path("login/phone-password/", auth.login_view, name="login_email"),
    path("register/", auth.register_customer_account, name="register_customer"),
    path("register-business/", auth.register_business_account, name="register_business"),
    path("password/change/", auth.change_password, name="change_password"),
    path("logout/", auth.logout_view, name="logout"),
]
