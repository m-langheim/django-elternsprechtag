from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from ..views.dashboard import *

urlpatterns = [
    path("events/", include("administrative.urls.events")),
    path("settings/", include("administrative.urls.settings")),
    path("users/", include("administrative.urls.users")),
    path("students/", include("administrative.urls.students")),
    path("", include("administrative.urls.dashboard")),
    # path("", include("administrative.urls.urls")),
]
