from typing import Dict
from django.shortcuts import render, redirect
from authentication.models import StudentChange, CustomUser, Upcomming_User
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404

import datetime

from ..forms import *
from ..tasks import *
from ..utils import *
from ..tables import *
from ..filters import *
from custom_backup.models import *
from custom_backup.utils_backup import CustomBackup
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from general_tasks.tasks import async_send_mail
from django.urls import reverse_lazy
from django.contrib.admin.views.decorators import staff_member_required

from dashboard.models import Event, EventChangeFormula
from dashboard.tasks import async_create_events_special, apply_event_change_formular

from django_tables2 import SingleTableView
from django.views.generic import FormView
import csv, io, os
from custom_backup.forms import *
from django.utils.decorators import method_decorator

login_staff = [login_required, staff_member_required]


class BackupOverviewView(View):
    def get(self, request):
        backups = Backup.objects.all().order_by("-created_at")[:5]
        backup_table = BackupTable(backups, orderable=False)
        upload_form = RestoreFileForm()
        create_backup_form = CreateForm()
        return render(
            request,
            "administrative/backup_template/backup_overview.html",
            {
                "backup_table": backup_table,
                "upload_form": upload_form,
                "create_backup_form": create_backup_form,
            },
        )


class BackupListView(SingleTableMixin, FilterView):
    template_name = "administrative/backup_template/backup_list.html"
    table_class = BackupTable
    queryset = Backup.objects.all().order_by("-created_at")
    paginate_by = 25
    filterset_class = BackupFilter


# class CreateBackupView(FormView):
#     template_name = "custom_backup/create_backup.html"
#     success_url = reverse_lazy("administrative_backup")
#     form_class = CreateForm
#     extra_context = {}

#     def dispatch(self, request, *args, **kwargs):
#         return super(CreateBackupView, self).dispatch(request, *args, **kwargs)

#     def form_valid(self, form):
#         backup = CustomBackup(manual=True)
#         backup.create_backup_file()
#         messages.success(self.request, "backup has been created")
#         return super(CreateBackupView, self).form_valid(form)
