from django.shortcuts import render, redirect
from authentication.models import StudentChange, CustomUser
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

import datetime

from .forms import CsvImportForm
from .tasks import *
import csv, io, os

from django.utils.decorators import method_decorator


class StudentListView(ListView):
    paginate_by = 50
    model = Student
    template_name = "administrative/student_list_view.html"


class StudentImportStart(View):
    def get(self, request, *args, **kwargs):
        csv_import = CsvImportForm()
        unapproved_changes = StudentChange.objects.filter(approved=False).exists()
        return render(
            request,
            "administrative/student_import_fileupload.html",
            {"form": csv_import, "unapproved_changes": unapproved_changes},
        )

    def post(self, request, *args, **kwargs):
        csv_import = CsvImportForm(request, request.FILES)

        try:
            csv_file = request.FILES["csv_file"].read().decode("utf-8-sig")
            process_task = process_studentimport_fileupload.delay(csv_file)
            return render(
                request,
                "administrative/student_import_progress.html",
                {
                    "task_id": process_task.task_id,
                    "success_url": reverse("student_import_listchanges"),
                },
            )
        except:
            csv_import.add_error("csv_file", "The file could not be read")
        return render(
            request,
            "administrative/student_import_fileupload.html",
            {"form": csv_import},
        )


class StudentImportListChanges(View):
    def get(self, request, *args, **kwargs):
        unchanged_students = StudentChange.objects.filter(
            Q(operation=0), Q(approved=False)
        )
        new_students = StudentChange.objects.filter(Q(operation=1), Q(approved=False))
        changed_students = StudentChange.objects.filter(
            Q(operation=2), Q(approved=False)
        )
        deleted_students = StudentChange.objects.filter(
            Q(operation=3), Q(approved=False)
        )
        return render(
            request,
            "administrative/student_import_display_changes.html",
            {"unchanged_students": unchanged_students, "new_students": new_students},
        )


class StudentImportApproveAndApplyAll(View):
    def get(self, request):
        changes = StudentChange.objects.filter(approved=False)

        print(list(changes.values_list("pk", flat=True)))

        task = apply_and_approve_student_changes.delay(
            list(changes.values_list("pk", flat=True))
        )

        return render(
            request,
            "administrative/student_import_progress.html",
            {"task_id": task.task_id, "success_url": reverse("student_list_view")},
        )
