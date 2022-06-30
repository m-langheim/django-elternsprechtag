from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('register/<user_token>/<key_token>/', register),
    path('login/', auth_views.LoginView.as_view(template_name='authentication/login.html'), name='login'),
]
