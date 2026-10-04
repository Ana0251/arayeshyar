"""
URL configuration اپ customers.
"""

from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path(
        "my-businesses/",
        views.my_businesses,
        name="my_businesses",
    ),
    path(
        "my-businesses/<int:business_id>/remove/",
        views.remove_business,
        name="remove_business",
    ),
    path(
        "my-businesses/<int:business_id>/favorite/",
        views.toggle_favorite,
        name="toggle_favorite",
    ),
]