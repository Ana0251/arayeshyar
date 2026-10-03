"""Views اپ booking."""

from .book import book_appointment
from .customer import (
    cancel_my_appointment,
    my_appointments,
    my_waiting,
)
from .owner import (
    add_manual_appointment,
    delete_appointment,
    update_status,
)
from .waiting import (
    convert_waiting_to_appointment,
    join_waiting_list,
    manage_waiting_list,
    update_waiting_status,
)

__all__ = [
    # Public booking
    "book_appointment",
    # Customer
    "my_appointments",
    "my_waiting",
    "cancel_my_appointment",
    "join_waiting_list",
    # Owner
    "update_status",
    "delete_appointment",
    "add_manual_appointment",
    # Waiting management
    "manage_waiting_list",
    "update_waiting_status",
    "convert_waiting_to_appointment",
]