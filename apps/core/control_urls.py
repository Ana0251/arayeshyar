from django.urls import path
from . import platform_admin as views

app_name = "control"
urlpatterns = [
    path("password-requests/", views.control_password_requests, name="password_requests"),
    path("password-requests/<int:request_id>/action/", views.control_password_request_action, name="password_request_action"),
    path("blog/", views.control_blog, name="blog"),
    path("blog/new/", views.control_blog_create, name="blog_create"),
    path("blog/<int:post_id>/edit/", views.control_blog_edit, name="blog_edit"),
    path("blog/<int:post_id>/delete/", views.control_blog_delete, name="blog_delete"),

    path("", views.control_dashboard, name="dashboard"),
    path("businesses/", views.control_businesses, name="businesses"),
    path("businesses/<int:business_id>/", views.control_business_detail, name="business_detail"),
    path("businesses/<int:business_id>/<str:action>/", views.control_business_action, name="business_action"),
    path("customers/", views.control_customers, name="customers"),
    path("customers/<int:customer_id>/", views.control_customer_detail, name="customer_detail"),
    path("users/<int:user_id>/reset-password/", views.control_reset_password, name="reset_password"),
    path("appointments/", views.control_appointments, name="appointments"),
]
