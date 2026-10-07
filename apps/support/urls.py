"""
URL configuration اپ support.
"""

from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("support/password-help/", views.password_help, name="password_help"),
    path(
        "support/new/",
        views.new_ticket,
        name="new_ticket",
    ),
    path(
        "support/my-tickets/",
        views.my_tickets,
        name="my_tickets",
    ),
    path(
        "support/tickets/<int:ticket_id>/",
        views.ticket_detail,
        name="ticket_detail",
    ),
    path(
        "support/tickets/<int:ticket_id>/close/",
        views.close_ticket,
        name="close_ticket",
    ),
]