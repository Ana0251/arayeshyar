"""
Load Test با Locust.
"""

import random

from locust import HttpUser, between, task


PUBLIC_PROFILE_URLS = [
    "/b/آرایشگر-علی/",
    "/b/سالن-زیبایی-سارا/",
    "/b/کلینیک-لیزر-رز/",
]


class GuestUser(HttpUser):
    """کاربر مهمان."""
    wait_time = between(1, 3)
    weight = 5

    @task(5)
    def home(self):
        self.client.get("/", name="صفحه اصلی")

    @task(3)
    def public_profiles(self):
        url = random.choice(PUBLIC_PROFILE_URLS)
        self.client.get(url, name="پروفایل عمومی")

    @task(2)
    def login_page(self):
        self.client.get("/auth/login/", name="صفحه لاگین")

    @task(1)
    def pwa_files(self):
        self.client.get("/manifest.webmanifest", name="Manifest")
        self.client.get("/sw.js", name="Service Worker")


class PublicProfileReader(HttpUser):
    """خواننده‌ی پروفایل عمومی."""
    wait_time = between(1, 4)
    weight = 10

    @task(10)
    def view_profiles(self):
        url = random.choice(PUBLIC_PROFILE_URLS)
        self.client.get(url, name="خواندن پروفایل")

    @task(2)
    def view_qr(self):
        self.client.get("/b/آرایشگر-علی/qr/", name="QR Code")

    @task(1)
    def view_home(self):
        self.client.get("/", name="صفحه اصلی")