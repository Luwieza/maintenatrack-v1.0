# maintenance/urls.py
"""
URL configuration for the maintenance app.

Routes:
- Home & About
- Maintenance Logs (list, detail, create)
- Authentication (signup)
"""

from django.urls import path
from . import views

app_name = "maintenance"

urlpatterns = [
    # Content pages
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),

    # Logs
    path("logs/", views.log_list, name="log_list"),
    path("logs/new/", views.log_create, name="log_create"),
    path("logs/<int:pk>/", views.log_detail, name="log_detail"),
    path("logs/<int:pk>/edit/", views.log_update, name="log_update"),
    path("logs/<int:pk>/delete/", views.log_delete, name="log_delete"),

    # Auth
    path("accounts/signup/", views.signup, name="signup"),

    # Equipment
    path("equipment/add/", views.add_equipment, name="add_equipment"),
    path("equipment/<int:pk>/delete/",
         views.equipment_delete, name="equipment_delete"),

    # Debug/Test
    path("test/", views.test_railway, name="test_railway"),

]
