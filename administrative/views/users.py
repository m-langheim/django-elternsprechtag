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
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from general_tasks.tasks import async_send_mail

from django.contrib.admin.views.decorators import staff_member_required

from dashboard.models import Event, EventChangeFormula
from dashboard.tasks import async_create_events_special, apply_event_change_formular

import csv, io, os

from django.utils.decorators import method_decorator

login_staff = [login_required, staff_member_required]


@method_decorator(login_staff, name="dispatch")
class ParentTableView(View):
    def get(self, request):
        parents = CustomUser.objects.filter(role=0)
        parents_table = ParentsTable(parents)

        return render(
            request,
            "administrative/users/parents/parents_overview.html",
            {"parents_table": parents_table},
        )


@method_decorator(login_staff, name="dispatch")
class TeacherTableView(View):
    def get(self, request):
        teachers = CustomUser.objects.filter(role=1)
        teachers_table = TeachersTable(teachers)

        return render(
            request,
            "administrative/users/teachers/teachers_overview.html",
            {"teachers_table": teachers_table},
        )


@method_decorator(login_staff, name="dispatch")
class ParentEditView(View):
    def get(self, request, parent_id):
        try:
            parent = CustomUser.objects.get(Q(pk=parent_id), Q(role=0))
        except:
            messages.error(request, "Das Elternteil konnte nicht gefunden werden.")
        else:
            form = ParentEditForm(instance=parent)
            return render(
                request,
                "administrative/users/parents/parent_edit.html",
                {"form": form, "parent": parent},
            )

    def post(self, request, parent_id):
        try:
            parent = CustomUser.objects.get(Q(pk=parent_id), Q(role=0))
        except:
            messages.error(request, "Das Elternteil konnte nicht gefunden werden.")
        else:
            form = ParentEditForm(request.POST, instance=parent)
            if form.is_valid():
                form.save()
            return render(
                request,
                "administrative/users/parents/parent_edit.html",
                {"form": form, "parent": parent},
            )


@method_decorator(login_staff, name="dispatch")
class TeacherEditView(View):
    def get(self, request, pk):
        try:
            teacher = CustomUser.objects.get(Q(pk=pk), Q(role=1))
        except:
            messages.error(request, "Something went wrong")
        else:
            print(teacher.teacherextradata.tags.all())
            teacher_form = TeacherEditForm(
                initial={
                    "first_name": teacher.first_name,
                    "last_name": teacher.last_name,
                    "email": teacher.email,
                    "acronym": teacher.teacherextradata.acronym,
                    "tags": teacher.teacherextradata.tags.all(),
                }
            )
            return render(
                request,
                "administrative/users/teachers/teacher_edit.html",
                {"form": teacher_form},
            )

    def post(self, request, pk):
        try:
            teacher = CustomUser.objects.get(Q(pk=pk), Q(role=1))
        except:
            messages.error(request, "Something went wrong")
        else:
            teacher_form = TeacherEditForm(
                request.POST,
                initial={
                    "first_name": teacher.first_name,
                    "last_name": teacher.last_name,
                    "email": teacher.email,
                    "acronym": teacher.teacherextradata.acronym,
                    "tags": teacher.teacherextradata.tags.all(),
                },
            )

            if teacher_form.is_valid():
                teacher.first_name = teacher_form.cleaned_data["first_name"]
                teacher.last_name = teacher_form.cleaned_data["last_name"]
                teacher.email = teacher_form.cleaned_data["email"]
                teacher.save()

                extra_data = teacher.teacherextradata
                extra_data.acronym = teacher_form.cleaned_data["acronym"]
                extra_data.save()

                messages.success(
                    request, "Die Änderungen wurden erfolgreich übernommen."
                )

            return render(
                request,
                "administrative/users/teachers/teacher_edit.html",
                {"form": teacher_form},
            )


@method_decorator(login_staff, name="dispatch")
class TeacherImportView(View):
    def get(self, request):
        bulk_form = TeacherImportForm()
        return render(
            request,
            "administrative/users/teachers/teacher_import.html",
            {"form": bulk_form},
        )

    def post(self, request, *args, **kwargs):
        form = TeacherImportForm(request.POST, request.FILES)

        if form.is_valid():
            if form.cleaned_data["csv_file"]:
                try:
                    csv_file = form.cleaned_data["csv_file"].read().decode("utf-8-sig")
                    process_task = proccess_teacher_file_import.delay(csv_file)
                    return render(
                        request,
                        "administrative/progress.html",
                        {
                            "task_id": process_task.task_id,
                            "success_url": reverse("teachers_table"),
                        },
                    )
                except:
                    form.add_error("csv_file", "The file could not be read")
            elif form.cleaned_data["teacher_email"]:
                email = form.cleaned_data["teacher_email"]
                if not CustomUser.objects.filter(
                    Q(email=email), Q(role=1), Q(is_active=True)
                ):
                    register_new_teacher(email)
                    messages.success(request, "Lehrkraft wurde hinzugefügt")
                    return redirect("teachers_table")
            else:
                form.add_error(
                    "csv_file",
                    error="Es muss mindestens eines der Felder ausgefüllt werden.",
                )
        return render(
            request,
            "administrative/users/teachers/teacher_import.html",
            {"form": form},
        )
