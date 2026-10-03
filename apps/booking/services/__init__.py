"""
سرویس‌های اپ booking.

منطق اصلی:
- AvailabilityService — محاسبه اسلات‌های آزاد
- BookingService — ایجاد/لغو نوبت
- WaitingListService — مدیریت لیست انتظار
"""

from .availability import AvailabilityService, SlotInfo
from .booking import (
    BookingError,
    BookingService,
    BusinessNotActiveError,
    CustomerBlockedError,
    DuplicateBookingError,
    SlotNotAvailableError,
)
from .waiting_list import WaitingListService

__all__ = [
    # Availability
    "AvailabilityService",
    "SlotInfo",
    # Booking
    "BookingService",
    "BookingError",
    "BusinessNotActiveError",
    "CustomerBlockedError",
    "SlotNotAvailableError",
    "DuplicateBookingError",
    # Waiting List
    "WaitingListService",
]