from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from ..views.dashboard import *

urlpatterns = [
    path("", AdministrativeDashboard.as_view(), name="administrative_dashboard"),
]
