from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from .views import *

urlpatterns = [
    path("", run_backup, name="run_ackup"),
    path("restore/", RestoreView.as_view(), name="run_ackup"),
]
