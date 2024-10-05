from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from ..views.backup import *
from custom_backup.views import CreateBackupView
from django.urls import reverse_lazy

urlpatterns = [
    path("", BackupOverviewView.as_view(), name="administrative_backup"),
    path("list/", BackupListView.as_view(), name="administrative_backup_list"),
    path(
        "create/",
        CreateBackupView.as_view(success_url=reverse_lazy("administrative_backup")),
        name="administrative_backup_create",
    ),
]
