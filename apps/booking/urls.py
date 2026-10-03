"""
URL configuration اپ booking.
"""

from django.urls import path

from .views import (
    add_manual_appointment,
    book_appointment,
    book_by_slug,
    cancel_my_appointment,
    convert_waiting_to_appointment,
    delete_appointment,
    join_waiting_list,
    manage_waiting_list,
    my_appointments,
    my_waiting,
    update_status,
    update_waiting_status,
)

app_name = "booking"

urlpatterns = [
    # ═══════════════════════════════════════════════════════════
    #  Public Booking
    # ═══════════════════════════════════════════════════════════
    path(
        "b/<uslug:slug>/",
        book_by_slug,
        name="book_by_slug",
    ),
    path(
        "b/<uslug:slug>/book/",
        book_appointment,
        name="book",
    ),
    path(
        "b/<uslug:slug>/waiting/",
        join_waiting_list,
        name="join_waiting_list",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Customer — نوبت‌ها و لیست انتظار
    # ═══════════════════════════════════════════════════════════
    path(
        "my-appointments/",
        my_appointments,
        name="my_appointments",
    ),
    path(
        "my-appointments/<int:appointment_id>/cancel/",
        cancel_my_appointment,
        name="cancel_my_appointment",
    ),
    path(
        "my-waiting/",
        my_waiting,
        name="my_waiting",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Owner — مدیریت نوبت‌ها
    # ═══════════════════════════════════════════════════════════
    path(
        "appointment/<int:appointment_id>/status/<str:new_status>/",
        update_status,
        name="update_status",
    ),
    path(
        "appointment/<int:appointment_id>/delete/",
        delete_appointment,
        name="delete_appointment",
    ),
    path(
        "manual-book/",
        add_manual_appointment,
        name="add_manual_appointment",
    ),

    # ═══════════════════════════════════════════════════════════
    #  Owner — لیست انتظار
    # ═══════════════════════════════════════════════════════════
    path(
        "waiting-list/",
        manage_waiting_list,
        name="manage_waiting_list",
    ),
    path(
        "waiting-list/<int:item_id>/status/<str:new_status>/",
        update_waiting_status,
        name="update_waiting_status",
    ),
    path(
        "waiting-list/<int:item_id>/convert/",
        convert_waiting_to_appointment,
        name="convert_waiting_to_appointment",
    ),
]