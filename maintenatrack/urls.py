# URLs (project + app)
from django.contrib import admin
from django.urls import path
from django.urls import path, include 

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout/password views
    path("", include("maintenance.urls", namespace="maintenance")),
]

