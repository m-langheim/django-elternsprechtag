from django.shortcuts import render, redirect
from dashboard.models import *
from authentication.models import *
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.contrib import admin
from .utils_backup import CustomBackup
from .utils_restore import CustomRestore, async_restore
from django.views import View
from .forms import *
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from .exceptions import BackupNotFound
from .models import *
from django.http import FileResponse
from .helpers import *


class RestoreBackupFromStorageView(FormView):
    template_name = "custom_backup/load_backup.html"
    success_url = reverse_lazy("admin:custom_backup_backup_changelist")
    form_class = RestoreForm
    extra_context = {}

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("custom_backup.can_restore_backup"):
            return super(RestoreBackupFromStorageView, self).dispatch(
                request, *args, **kwargs
            )
        else:
            raise PermissionDenied

    def get(self, request, pk, *args, **kwargs):
        obj = Backup.objects.get(pk=pk)
        if Path(obj.backup_file).is_file():
            self.extra_context["backup"] = obj
            self.extra_context["site_header"] = admin.site.site_header
        else:
            raise BackupNotFound(f"{obj.backup} not found")
        return super(RestoreBackupFromStorageView, self).get(request)

    def form_valid(self, form):
        obj = self.extra_context["backup"]
        restore = CustomRestore()

        if settings.BACKUP_ASYNC:
            task = async_restore.delay(
                tar_path=obj.backup_file,
                silent=True,
                flush=form.cleaned_data["flush"],
                delete_dirs=form.cleaned_data["deletedirs"],
            )
            return render(
                self.request,
                "custom_backup/progress.html",
                {
                    "task_id": task.task_id,
                    "success_url": self.success_url,
                },
            )
        else:
            restore.restore_form_file(
                obj.backup_file,
                silent=True,
                flush=form.cleaned_data["flush"],
                delete_dirs=form.cleaned_data["deletedirs"],
            )
        messages.success(self.request, "backup has been restored")
        return super(RestoreBackupFromStorageView, self).form_valid(form)


class CreateBackupView(FormView):
    template_name = "custom_backup/create_backup.html"
    success_url = reverse_lazy("admin:custom_backup_backup_changelist")
    form_class = CreateForm
    extra_context = {}

    def dispatch(self, request, *args, **kwargs):
        if request.user.has_perm("custom_backup.can_add_backup"):
            return super(CreateBackupView, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        self.extra_context["site_header"] = admin.site.site_header
        return super(CreateBackupView, self).get_context_data()

    def form_valid(self, form):
        backup = CustomBackup(manual=True)
        backup.create_backup_file()
        messages.success(self.request, "backup has been created")
        return super(CreateBackupView, self).form_valid(form)


class DownloadBackupView(View):
    def get(self, request, pk):
        obj = Backup.objects.get(pk=pk)
        response = FileResponse(open(obj.backup_file, "rb"))
        file_name = Path(obj.backup_file).name
        response["Content-Disposition"] = "inline; filename=" + file_name
        return response


class UploadBackupFileView(View):
    def get(self, request):
        form = RestoreFileForm()
        return render(request, "custom_backup/upload_backup.html", {"form": form})

    def post(self, request):
        form = RestoreFileForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data["backup_file"]
            with open(Path(settings.BACKUP_ROOT).joinpath(str(file)), "wb+") as f:
                for chunk in file:
                    f.write(chunk)
            hande_uploaded_file(Path(settings.BACKUP_ROOT).joinpath(str(file)))

            messages.success(request, "The backup was uploaded successfully")
            return redirect("admin:custom_backup_backup_changelist")
        return render(request, "custom_backup/upload_backup.html", {"form": form})
