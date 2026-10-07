"""Views اپ business."""

from .breaks import delete_break, manage_breaks
from .changes import cancel_change_request, my_change_requests
from .dashboard import dashboard
from .days_off import delete_day_off, manage_days_off
from .hours import delete_working_hours, manage_hours
from .profile import delete_avatar, edit_profile
from .public import business_profile_public, qr_code, share_page
from .register import (
    register_activity,
    register_audience,
    register_business_info,
    register_done,
    register_salon_type,
    register_services,
    register_stations,
    register_start,
)

from .staff import manage_staff, edit_staff, toggle_staff
from .staff_schedules import (
    delete_staff_schedule,
    edit_staff_schedule,
    manage_staff_schedules,
)
from .payment import buy_plan, cancel_payment, my_plan
from .services import delete_service, edit_service, manage_services
from .special_hours import delete_special_hours, manage_special_hours
from .stations import delete_station, edit_station, manage_stations
from .analytics import analytics

__all__ = [
    # Public
    "business_profile_public",
    "qr_code",
    "share_page",
    # Dashboard
    "dashboard",
    # Profile
    "edit_profile",
    "delete_avatar",
    # Changes
    "my_change_requests",
    "cancel_change_request",
    # Register
    "register_start",
    "register_audience",
    "register_salon_type",
    "register_activity",
    "register_stations",
    "register_services",
    "register_business_info",
    "register_done",
    # Services
    "manage_services",
    "edit_service",
    "delete_service",
    # Stations
    "manage_stations",
    "edit_station",
    "delete_station",
    # Hours
    "manage_hours",
    "delete_working_hours",
    # Days Off
    "manage_days_off",
    "delete_day_off",
    # Special Hours
    "manage_special_hours",
    "delete_special_hours",
    # Breaks
    "manage_breaks",
    "delete_break",
    "my_plan",
    "buy_plan",
    "cancel_payment",
    
    "analytics",
    
    "manage_staff",
    "edit_staff",
    "toggle_staff",
    "manage_staff_schedules",
    "edit_staff_schedule", 
    "delete_staff_schedule",
]
from .customers import manage_customers, customer_detail, toggle_customer_block
