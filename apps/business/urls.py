"""
URL configuration اپ business.
"""

from django.urls import path

from apps.business.views.analytics import analytics

from .views import (
    # Public
    business_profile_public,
    qr_code,
    share_page,
    # Dashboard
    dashboard,
    
    my_plan,
    buy_plan,
    cancel_payment,
    
    # Profile
    delete_avatar,
    edit_profile,
    # Changes
    cancel_change_request,
    my_change_requests,
    # Register
    register_activity,
    register_audience,
    register_business_info,
    register_done,
    register_salon_type,
    register_services,
    register_stations,
    register_start,
    # Services
    delete_service,
    edit_service,
    manage_services,
    # Stations
    delete_station,
    edit_station,
    manage_stations,
    # Hours
    delete_working_hours,
    manage_hours,
    # Days Off
    delete_day_off,
    manage_days_off,
    # Special Hours
    delete_special_hours,
    manage_special_hours,
    # Breaks
    delete_break,
    manage_breaks,
    
    delete_staff_schedule,
    edit_staff_schedule, 
    manage_staff_schedules,
)

app_name = "business"

urlpatterns = [
    # ═══════════════════════════════════════════════════════════
    #  Public
    # ═══════════════════════════════════════════════════════════
    path("b/<uslug:slug>/", business_profile_public, name="public_profile"),
    path("b/<uslug:slug>/qr/", qr_code, name="qr_code"),

    # ═══════════════════════════════════════════════════════════
    #  Dashboard
    # ═══════════════════════════════════════════════════════════
    path("business/dashboard/", dashboard, name="dashboard"),
    path("business/share/", share_page, name="share"),

    # ═══════════════════════════════════════════════════════════
    #  Profile
    # ═══════════════════════════════════════════════════════════
    path("business/profile/edit/", edit_profile, name="edit_profile"),
    path(
        "business/profile/avatar/delete/",
        delete_avatar,
        name="delete_avatar",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Change Requests
    # ═══════════════════════════════════════════════════════════
    path(
        "business/change-requests/",
        my_change_requests,
        name="my_change_requests",
    ),
    path(
        "business/change-requests/<int:request_id>/cancel/",
        cancel_change_request,
        name="cancel_change_request",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Register
    # ═══════════════════════════════════════════════════════════
    path("register/", register_start, name="register_start"),
    path(
        "register/audience/",
        register_audience,
        name="register_audience",
    ),
    path(
        "register/salon-type/",
        register_salon_type,
        name="register_salon_type",
    ),
    path(
        "register/activity/",
        register_activity,
        name="register_activity",
    ),
    path(
        "register/stations/",
        register_stations,
        name="register_stations",
    ),
    path(
        "register/services/",
        register_services,
        name="register_services",
    ),
    path(
        "register/info/",
        register_business_info,
        name="register_info",
    ),
    path("register/done/", register_done, name="register_done"),

    # ═══════════════════════════════════════════════════════════
    #  Services
    # ═══════════════════════════════════════════════════════════
    path("business/services/", manage_services, name="manage_services"),
    path(
        "business/services/<int:service_id>/edit/",
        edit_service,
        name="edit_service",
    ),
    path(
        "business/services/<int:service_id>/delete/",
        delete_service,
        name="delete_service",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Stations
    # ═══════════════════════════════════════════════════════════
    path("business/stations/", manage_stations, name="manage_stations"),
    path(
        "business/stations/<int:station_id>/edit/",
        edit_station,
        name="edit_station",
    ),
    path(
        "business/stations/<int:station_id>/delete/",
        delete_station,
        name="delete_station",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Hours
    # ═══════════════════════════════════════════════════════════
    path("business/hours/", manage_hours, name="manage_hours"),
    path(
        "business/hours/<int:hours_id>/delete/",
        delete_working_hours,
        name="delete_working_hours",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Days Off
    # ═══════════════════════════════════════════════════════════
    path("business/days-off/", manage_days_off, name="manage_days_off"),
    path(
        "business/days-off/<int:day_off_id>/delete/",
        delete_day_off,
        name="delete_day_off",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Special Hours
    # ═══════════════════════════════════════════════════════════
    path(
        "business/special-hours/",
        manage_special_hours,
        name="manage_special_hours",
    ),
    path(
        "business/special-hours/<int:special_id>/delete/",
        delete_special_hours,
        name="delete_special_hours",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Breaks
    # ═══════════════════════════════════════════════════════════
    path("business/breaks/", manage_breaks, name="manage_breaks"),
    path(
        "business/breaks/<int:break_id>/delete/",
        delete_break,
        name="delete_break",
    ),
    # ─── پلن و پرداخت ───
    path("business/my_plan/", my_plan, name="my_plan"),
    path("business/buy_plan/", buy_plan, name="buy_plan"),
    path(
        "business/payments/<int:payment_id>/cancel/",
        cancel_payment,
        name="cancel_payment",
    ),
    
    path("business/analytics/", analytics, name="analytics"),
    
    # ═══════════════════════════════════════════════════════════
    #  Staff Schedules (شیفت کارمندها)
    # ═══════════════════════════════════════════════════════════
    path(
        "business/staff-schedules/",
        manage_staff_schedules,
        name="manage_staff_schedules",
    ),
    path(
        "business/staff-schedules/<int:schedule_id>/delete/",
        delete_staff_schedule,
        name="delete_staff_schedule",
    ),
    path(
        "business/staff-schedules/<int:schedule_id>/edit/",
        edit_staff_schedule,
        name="edit_staff_schedule",
    ),
]