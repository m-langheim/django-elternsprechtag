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
class StudentListView(SingleTableView):
    model = Student
    table_class = StudentTable
    paginate_by = 75
    template_name = "administrative/student/student_list_view.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student_search"] = StudentDirectSelectForm()
        context["unapproved_changes"] = StudentChange.objects.filter(
            approved=False
        ).exists()
        context["unsend_up_users"] = Upcomming_User.objects.filter(
            email_send=False
        ).exists()
        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get("student", None):
            print(request.GET.get("student", None))
            return redirect("student_details_view", pk=request.GET.get("student", None))
        return super().get(request, *args, **kwargs)


@method_decorator(login_staff, name="dispatch")
class StudentImportStart(View):
    def get(self, request, *args, **kwargs):
        csv_import = CsvImportForm()
        unapproved_changes = StudentChange.objects.filter(approved=False).exists()
        return render(
            request,
            "administrative/student/student_import_fileupload.html",
            {"form": csv_import, "unapproved_changes": unapproved_changes},
        )

    def post(self, request, *args, **kwargs):
        csv_import = CsvImportForm(request, request.FILES)

        try:
            csv_file = request.FILES["csv_file"].read().decode("utf-8-sig")
            process_task = process_studentimport_fileupload.delay(csv_file)
            return render(
                request,
                "administrative/progress.html",
                {
                    "task_id": process_task.task_id,
                    "success_url": reverse("student_import_listchanges"),
                },
            )
        except:
            csv_import.add_error("csv_file", "The file could not be read")
        return render(
            request,
            "administrative/student/student_import_fileupload.html",
            {"form": csv_import},
        )


@method_decorator(login_staff, name="dispatch")
class StudentImportListChanges(View):
    def get(self, request, *args, **kwargs):
        if not StudentChange.objects.filter(approved=False).exists():
            messages.info(request, "Es gibt keine offenen Änderungen")
            return redirect("student_list_view")

        unchanged_students = StudentChange.objects.filter(
            Q(operation=0), Q(approved=False)
        )
        unchanged_students_table = StudentChangeTable(unchanged_students)
        new_students = StudentChange.objects.filter(Q(operation=1), Q(approved=False))
        new_students_table = StudentChangeTable(new_students)
        changed_students = StudentChange.objects.filter(
            Q(operation=2), Q(approved=False)
        )
        changed_students_table = StudentChangeTable(changed_students)
        deleted_students = StudentChange.objects.filter(
            Q(operation=3), Q(approved=False)
        )
        deleted_students_table = StudentChangeTable(deleted_students)
        return render(
            request,
            "administrative/student/student_import_display_changes.html",
            {
                "unchanged_students": unchanged_students,
                "unchanged_students_table": unchanged_students_table,
                "new_students": new_students,
                "new_students_table": new_students_table,
                "changed_students": changed_students,
                "changed_students_table": changed_students_table,
                "delete_students": deleted_students,
                "delete_students_table": deleted_students_table,
            },
        )


@method_decorator(login_staff, name="dispatch")
class StudentImportCancel(View):
    def get(self, request):
        latest_changes = StudentChange.objects.filter(
            Q(approved=False), Q(applied=False)
        )

        latest_changes.all().delete()

        return redirect("student_import_filepload")


@method_decorator(login_staff, name="dispatch")
class StudentImportApproveAndApplyAll(View):
    def get(self, request):
        changes = StudentChange.objects.filter(approved=False)

        task = apply_and_approve_student_changes.delay(
            list(changes.values_list("pk", flat=True))
        )

        return render(
            request,
            "administrative/progress.html",
            {"task_id": task.task_id, "success_url": reverse("student_list_view")},
        )


@method_decorator(login_staff, name="dispatch")
class StudentImportApproveAndApplyWithOperation(View):
    def get(self, request, operation):
        changes = StudentChange.objects.filter(
            Q(approved=False), Q(operation=operation)
        )

        task = apply_and_approve_student_changes.delay(
            list(changes.values_list("pk", flat=True))
        )

        return render(
            request,
            "administrative/progress.html",
            {
                "task_id": task.task_id,
                "success_url": reverse("student_import_listchanges"),
            },
        )


@method_decorator(login_staff, name="dispatch")
class StudentImportApproveAndApply(View):
    def get(self, request, pk):
        try:
            change = StudentChange.objects.get(Q(approved=False), Q(pk=pk))

            task = apply_and_approve_student_changes.delay([change.pk])

            return render(
                request,
                "administrative/progress.html",
                {
                    "task_id": task.task_id,
                    "success_url": reverse("student_import_listchanges"),
                },
            )
        except StudentChange.DoesNotExist:
            messages.error(request, "Der Änderungseintrag konnte nicht gefunden werden")

            return redirect("student_import_listchanges")


@method_decorator(login_staff, name="dispatch")
class StudentImportRemoveEntry(View):
    def get(self, request, pk):
        change = get_object_or_404(StudentChange, approved=False, pk=pk)
        student = change.student
        change.delete()
        messages.success(
            request, f"The change on {str(student)}´s account was successfully removed."
        )
        return redirect("student_import_listchanges")


@method_decorator(login_staff, name="dispatch")
class StudentChangeEditView(View):
    def get(self, request, pk):
        change = get_object_or_404(StudentChange, approved=False, pk=pk)

        form = EditStudentChangesForm(instance=change)

        return render(
            request, "administrative/student/edit_student_changes.html", {"form": form}
        )

    def post(self, request, pk):
        change = get_object_or_404(StudentChange, approved=False, pk=pk)

        form = EditStudentChangesForm(instance=change, data=request.POST)

        if form.is_valid():
            form.save()

            messages.success(request, "The student change was successfully editied.")

            return redirect("student_import_listchanges")

        return render(
            request, "administrative/student/edit_student_changes.html", {"form": form}
        )


@method_decorator(login_staff, name="dispatch")
class StudentEdit(View):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            messages.error(request, "The entry could not be found.")
            return redirect("student_list_view")
        else:
            student_edit_form = AdminStudentEditForm(
                initial={
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "child_email": student.child_email,
                    "class_name": student.class_name,
                }
            )

            # student_edit_form = AdminStudentEditForm()

            print(AdminStudentEditForm())

            return render(
                request,
                "administrative/student/student_edit.html",
                {"form": student_edit_form, "student": student},
            )

    def post(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            messages.error(request, "The entry could not be found.")
            return redirect("student_list_view")
        else:
            student_edit_form = AdminStudentEditForm(request.POST)

            if student_edit_form.is_valid():
                change_object = StudentChange.objects.create(
                    operation=2,
                    student=student,
                    first_name=student_edit_form.cleaned_data["first_name"],
                    last_name=student_edit_form.cleaned_data["last_name"],
                    child_email=student_edit_form.cleaned_data["child_email"],
                    class_name=student_edit_form.cleaned_data["class_name"],
                )
                change_object.save()

                return redirect("student_list_view")

            # student_edit_form = AdminStudentEditForm()

            return render(
                request,
                "administrative/student/student_edit.html",
                {"form": student_edit_form, "student": student},
            )


@method_decorator(login_staff, name="dispatch")
class StudentDetailView(View):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            messages.error(request, "The entry could not be found.")
            return redirect("student_list_view")
        else:
            parent = student.parent()
            if parent:
                return render(
                    request,
                    "administrative/student/student_detail_view.html",
                    {"student": student, "parent": parent},
                )
            else:
                one_time_login, created = Upcomming_User.objects.get_or_create(
                    student=student
                )

                return render(
                    request,
                    "administrative/student/student_detail_view.html",
                    {
                        "student": student,
                        "one_time_login": one_time_login,
                        "sign_up_url": str(os.environ.get("PUBLIC_URL"))
                        + "/register/"
                        + str(one_time_login.user_token)
                        + "/"
                        + str(one_time_login.access_key)
                        + "/",
                    },
                )


@method_decorator(login_staff, name="dispatch")
class UpcommingUserSendRegistrationMail(View):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
            up_user = Upcomming_User.objects.get(student=student)
        except:
            messages.warning(request, "Es ist etwas schief gelaufen")
            return redirect("..")
        else:
            if (
                up_user.created + timezone.timedelta(days=15) < timezone.now()
                or up_user.email_send
            ):
                up_user.delete()

                up_user = Upcomming_User.objects.create(student=student)
                up_user.save()

            email_subject = "Registration link for the parent consultation day"
            email_str_body = render_to_string(
                "authentication/email/register_parent/register_parent_child_email.txt",
                {
                    "user": up_user,  # ggf kann man das nicht so machen
                    "otp": up_user.otp,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + "/register/"
                    + str(up_user.user_token)
                    + "/"
                    + str(up_user.access_key)
                    + "/",
                },
            )
            email_html_body = render_to_string(
                "authentication/email/register_parent/register_parent_child_email.html",
                {
                    "user": up_user,  # ggf kann man das nicht so machen
                    "otp": up_user.otp,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + "/register/"
                    + str(up_user.user_token)
                    + "/"
                    + str(up_user.access_key)
                    + "/",
                    "template_text_bottom": "Use the following One-Time-Password when signing up: <strong>"
                    + up_user.otp
                    + "</strong>.",
                    "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                },
            )  #!Hier habe ich ein wenig gefuscht; dies wird gerade nicht genutzt!

            # async_send_mail.delay(
            #     email_subject,
            #     email_str_body,
            #     up_user.student.child_email,
            #     email_html_body=email_html_body,
            # )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                up_user.student.child_email,
            )  #! Hier wird keine HTML versandt
            up_user.email_send = True
            up_user.save()
            messages.success(request, "Die Registrieungsmail wurde versendet.")
            return redirect("student_details_view", student.pk)


@method_decorator(login_staff, name="dispatch")
class ResetStudentParentRelationshipView(View):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except:
            messages.error(request, "Der Schüler konnte nicht gefunden werden.")
        else:
            reset_student_parent_relationship(student)
            return redirect("..")


@method_decorator(login_staff, name="dispatch")
class ManualParentRegistration(View):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except:
            messages.error(request, "Der Schüler konnte nicht gefunden werden.")
        else:
            form = ControlParentCreationForm(initial={"student": student})
            return render(
                request,
                "administrative/student/manual_parent_registration_create.html",
                {
                    "form": form,
                    "student": student,
                    "validators": password_validators_help_text_html,
                },
            )

    def post(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except:
            messages.error(request, "Der Schüler konnte nicht gefunden werden.")
        else:
            form = ControlParentCreationForm(request.POST, initial={"student": student})
            if form.is_valid():
                parent = CustomUser.objects.create(
                    email=form.cleaned_data["email"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    role=0,
                )
                parent.set_password(form.cleaned_data["password"])
                parent.students.add(student)
                parent.save()

                try:
                    up_user = Upcomming_User.objects.filter(student=student)
                except Upcomming_User.DoesNotExist:
                    pass
                else:
                    up_user.delete()

                messages.success(
                    request,
                    "The parent was successfully created and the student added.",
                )

                return redirect("student_details_view", student.pk)

            return render(
                request,
                "administrative/student/manual_parent_registration_create.html",
                {
                    "form": form,
                    "student": student,
                    "validators": password_validators_help_text_html,
                },
            )


@method_decorator(login_staff, name="dispatch")
class ManualParentAddStudent(View):
    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except:
            messages.error(request, "Der Schüler konnte nicht gefunden werden.")
        else:
            form = ControlParentAddStudent(initial={"student": student})
            return render(
                request,
                "administrative/student/manual_parent_registration_add.html",
                {"form": form, "student": student},
            )

    def post(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
        except:
            messages.error(request, "Der Schüler konnte nicht gefunden werden.")
        else:
            form = ControlParentAddStudent(request.POST, initial={"student": student})
            if form.is_valid():
                parent: CustomUser = form.cleaned_data["parent"]

                parent.students.add(student)
                parent.save()

                try:
                    up_user = Upcomming_User.objects.filter(student=student)
                except Upcomming_User.DoesNotExist:
                    pass
                else:
                    up_user.delete()

                messages.success(
                    request,
                    "The student was successfully added to the parent.",
                )

                return redirect("student_details_view", student.pk)

            return render(
                request,
                "administrative/student/manual_parent_registration_add.html",
                {"form": form, "student": student},
            )

@method_decorator(login_staff, name="dispatch")
class UpcommingUserBatchSendView(View):
    def get(self, request):
        form = UpcommingUserBatchSendForm()

        return render(
            request,
            "administrative/administrative_form_fallback.html",
            {
                "form": form,
                "title": _("Batch send upcomming user"),
                "back_url": reverse("student_list_view"),
            },
        )

    def post(self, request):
        form = UpcommingUserBatchSendForm(data=request.POST)

        if form.is_valid():
            # relevant_students = Student.objects.filter(
            #     pk__in=list(
            #         Upcomming_User.objects.all().values_list("student", flat=True)
            #     )
            # ).exclude(
            #     pk__in=list(
            #         form.cleaned_data["exclude_students"].values_list("pk", flat=True)
            #     )
            # )
            print(form.cleaned_data["resend"], form.cleaned_data["exclude_students"])
            if form.cleaned_data["resend"]:
                up_users = Upcomming_User.objects.all()
            else:
                up_users = Upcomming_User.objects.filter(email_send=False)
            student_list = Student.objects.filter(
                pk__in=list(up_users.values_list("student", flat=True))
            ).exclude(
                pk__in=list(
                    list(
                        form.cleaned_data["exclude_students"].values_list(
                            "pk", flat=True
                        )
                    )
                )
            )
            print(student_list)
            process_task = batch_send_upcomming_user_registration_link.delay(
                exclude_pks=list(
                    form.cleaned_data["exclude_students"].values_list("pk", flat=True)
                ),
                resend=form.cleaned_data["resend"],
            )

            return render(
                request,
                "administrative/progress.html",
                {
                    "task_id": process_task.task_id,
                    "success_url": reverse("student_list_view"),
                },
            )

        return render(
            request,
            "administrative/administrative_form_fallback.html",
            {
                "form": form,
                "title": _("Batch send upcomming user"),
                "back_url": reverse("student_list_view"),
            },
        )
