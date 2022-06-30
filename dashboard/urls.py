from django.urls import path
from .views import *

urlpatterns = [
    path('', public_dashboard, name='home')
]
