"""
URL configuration اپ core.
"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("", views.home, name="home"),
    path("health/", views.health_check, name="health_check"),
    path("about/", views.about, name="about"),
    path("offline/", views.offline_view, name="offline"),
]