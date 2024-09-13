from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("", run_backup),
    path("create/", login_required(CreateBackupView.as_view()), name="create_backup"),
    path(
        "<pk>/restore/", RestoreBackupFromStorageView.as_view(), name="restore_backup"
    ),
    path("<pk>/download/", DownloadBackupView.as_view(), name="download_backup"),
]
