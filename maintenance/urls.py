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

    # Auth
    path("accounts/signup/", views.signup, name="signup"),
]
