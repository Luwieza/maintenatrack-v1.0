from django.urls import path
from . import views

app_name = "maintenance"

urlpatterns = [
    path("", views.log_list, name="log_list"),
    path("logs/new/", views.log_create, name="log_create"),
    path("logs/<int:pk>/", views.log_detail, name="log_detail"),
    path("accounts/signup/", views.signup, name="signup"),
]
