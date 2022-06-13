from django.urls import path
from .views import register_help

urlpatterns = [
    path('register/', register_help, name="help_register")
]