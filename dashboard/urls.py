from django.urls import path
from .views import *

urlpatterns = [
    path('', public_dashboard, name='home'),
    path('search/', public_dashboard, name='search')
]
