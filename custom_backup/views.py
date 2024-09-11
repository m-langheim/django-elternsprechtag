from django.shortcuts import render
from django.http.response import JsonResponse
from django.core.serializers import serialize, deserialize
from dashboard.models import *
from authentication.models import *
from django.contrib.auth.models import Group
from .utils_backup import CustomBackup
from .utils_restore import CustomRestore, async_restore
from .utils_restore_async import restore_async
from django.views import View
from .forms import *
from django.urls import reverse
from pathlib import Path
from django.conf import settings


# Create your views here.
def run_backup(request):
    print(serialize("json", CustomUser.objects.all()))
    group_dict = []
    for group in Group.objects.all():
        group_dict.append(
            {
                "group_name": group.name,
                "group_permissions": [
                    permission.pk for permission in group.permissions.all()
                ],
            }
        )
    print(group_dict)
    backup = CustomBackup()
    print(backup.get_backup_data())
    backup.create_backup_file()
    return JsonResponse(backup.get_backup_data(), safe=False)


class BackupView(View):
    def get(self, request):
        pass


class RestoreView(View):
    def get(self, request):
        form = BackupRestoreForm()
        return render(request, "custom_backup/restore_backup.html", {"form": form})

    def post(self, request):
        form = BackupRestoreForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["backup_file"]

            with open(Path(settings.BACKUP_ROOT).joinpath(str(file)), "wb+") as f:
                for chunk in file:
                    f.write(chunk)

            # restorerer = CustomRestore()
            # restorerer.restore_form_file(Path(settings.BACKUP_ROOT).joinpath(str(file)))
            process_task = async_restore.delay(
                tar_path=str(Path(settings.BACKUP_ROOT).joinpath(str(file)))
            )

            # print(form.cleaned_data)
            # restorerer.restore(data=form.cleaned_data["backup_data"])
            # process_task = restore_async.delay(data=form.cleaned_data["backup_data"])
            return render(
                request,
                "custom_backup/progress.html",
                {
                    "task_id": process_task.task_id,
                    "success_url": reverse("student_import_listchanges"),
                },
            )
        return render(request, "custom_backup/restore_backup.html", {"form": form})
