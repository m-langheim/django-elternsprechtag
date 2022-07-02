from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('register/<user_token>/<key_token>/', register),
    path('login/', auth_views.LoginView.as_view(template_name='authentication/login.html', authentication_form=CustomAuthForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='authentication/logout.html'), name='logout')
]
