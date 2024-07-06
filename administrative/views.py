from typing import Dict
from django.shortcuts import render, redirect
from authentication.models import StudentChange, CustomUser, Upcomming_User
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
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

import datetime

from .forms import *
from .tasks import *
from .utils import *
from .tables import *
from .filters import *
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from general_tasks.tasks import async_send_mail

from django.contrib.admin.views.decorators import staff_member_required

from dashboard.models import Event, EventChangeFormula
from dashboard.tasks import async_create_events_special

import csv, io, os

from django.utils.decorators import method_decorator

login_staff = [login_required, staff_member_required]


@method_decorator(login_staff, name="dispatch")
class AdministrativeDashboard(View):
    def get(self, request, *args, **kwargs):
        return render(request, "administrative/administrative_dashboard.html")


@method_decorator(login_staff, name="dispatch")
class StudentListView(SingleTableView):
    model = Student
    table_class = StudentTable
    paginate_by = 75
    template_name = "administrative/student/student_list_view.html"


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
@method_decorator(permission_required("dashboard.approve_disapprove"), name="dispatch")
class AdministrativeFormulaApprovalView(View):
    def get(self, request):
        formulars = EventChangeFormula.objects.filter(
            Q(date__gte=timezone.now()), Q(status=1)
        )
        formulars_table = EventFormularActionTable(formulars)

        approved_formulars_table = EventFormularOldTable(
            EventChangeFormula.objects.filter(Q(status=2) | Q(status=3))
        )

        upcomming_formulars_table = EventFormularUpcommingTable(
            EventChangeFormula.objects.filter(Q(date__gte=timezone.now()), Q(status=0))
        )

        formular_form = EventChangeFormularForm()

        return render(
            request,
            "administrative/time_slots/overview.html",
            {
                "action_table": formulars_table,
                "upcomming_table": upcomming_formulars_table,
                "approved_formulars_table": approved_formulars_table,
                "change_formular": formular_form,
            },
        )


@method_decorator(login_staff, name="dispatch")
class EditTimeSlotView(View):
    def get(self, request, pk):
        try:
            formula = EventChangeFormula.objects.get(pk=pk)
        except:
            messages.error(request, "Somethin went wrong.")
        else:
            form = EventChangeFormulaEditForm(instance=formula)
            return render(
                request,
                "administrative/time_slots/edit_time_slots.html",
                {"form": form},
            )

    def post(self, request, pk):
        try:
            formula = EventChangeFormula.objects.get(pk=pk)
        except:
            messages.error(request, "Somethin went wrong.")
        else:
            form = EventChangeFormulaEditForm(request.POST, instance=formula)

            if form.is_valid():
                form.save()
                return redirect("administrative_event_formular_view")
            return render(
                request,
                "administrative/time_slots/edit_time_slots.html",
                {"form": form},
            )


# class EventsListView(View):
#     def get(self, request):
#         events = Event.objects.filter(start__gte=timezone.now())
#         events_table = Eventstable(events)
#         events_table.paginate(page=request.GET.get("page", 1), per_page=25)

#         formular_form = EventChangeFormularForm()

#         return render(
#             request,
#             "administrative/time_slots/events_table.html",
#             {"events_table": events_table, "change_formular": formular_form},
#         )


@method_decorator(login_staff, name="dispatch")
class EventsListView(SingleTableMixin, FilterView):
    table_class = Eventstable
    template_name = "administrative/time_slots/events_table.html"
    model = Event
    filterset_class = EventFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["change_formular"] = EventChangeFormularForm()
        # context["filter"].form.helper = EventFilterFormHelper()
        # print(context["filter"].form)
        return context

    def get_queryset(self, *args, **kwargs):
        return Event.objects.filter(start__gte=timezone.now()).all()


@method_decorator(login_staff, name="dispatch")
class EventBlockView(View):
    def get(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            messages.error(request, "Das gesuchte Event konnte nicht gefunden werden.")
            return redirect("..")
        else:
            event.occupied = True
            event.status = 1
            event.save()
            return redirect("..")


@method_decorator(login_staff, name="dispatch")
class EventChangeFormularAddView(View):
    def post(self, request):
        form = EventChangeFormularForm(request.POST)

        if form.is_valid():
            date = form.cleaned_data["date"]
            teachers = form.cleaned_data["teacher"]

            for teacher in teachers:
                EventChangeFormula.objects.create(teacher=teacher, date=date)
            return redirect("administrative_event_formular_view")


@method_decorator(login_staff, name="dispatch")
class EventChangeFormularApproveView(View):
    def get(self, request, formular_id):
        try:
            formula = EventChangeFormula.objects.get(pk=formular_id)
        except EventChangeFormula.DoesNotExist:
            messages.error(
                request, "Das gegebene Formular konnte nicht gefunden werden"
            )
            return redirect("administrative_event_formular_view")
        else:
            if formula.status != 1:
                messages.warning(
                    request,
                    "Sie können diesen Antrag nicht ablehnen, da er sich hierzu im falschen Status befindet.",
                )
                return redirect("administrative_event_formular_view")

            if not formula.no_events:
                async_create_events_special.delay(
                    [formula.teacher.id],
                    formula.date.strftime("%Y-%m-%d"),
                    formula.start_time.strftime("%H:%M:%S"),
                    formula.end_time.strftime("%H:%M:%S"),
                )

            formula.status = 2
            formula.save()

            messages.success(request, "Die Termine werden nun erstellt.")

            return redirect("administrative_event_formular_view")


@method_decorator(login_staff, name="dispatch")
class EventChangeFormularDisapproveView(View):
    def get(self, request, formular_id):
        try:
            formula = EventChangeFormula.objects.get(pk=formular_id)
        except EventChangeFormula.DoesNotExist:
            messages.error(
                request, "Das gegebene Formular konnte nicht gefunden werden"
            )
            return redirect("administrative_event_formular_view")
        else:
            if formula.status != 1:
                messages.warning(
                    request,
                    "Sie können diesen Antrag nicht ablehnen, da er sich hierzu im falschen Status befindet.",
                )
                return redirect("administrative_event_formular_view")

            formula.status = 3
            formula.save()

            messages.success(request, "Die Termine werden nun erstellt.")

            return redirect("administrative_event_formular_view")


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
        form = CsvImportForm()
        return render(
            request, "administrative/users/teachers/teacher_import.html", {"form": form}
        )

    def post(self, request, *args, **kwargs):
        csv_import = CsvImportForm(request, request.FILES)

        try:
            csv_file = request.FILES["csv_file"].read().decode("utf-8-sig")
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
            csv_import.add_error("csv_file", "The file could not be read")
        return render(
            request,
            "administrative/users/teachers/teacher_import.html",
            {"form": csv_import},
        )


@method_decorator(login_staff, name="dispatch")
class SettingsView(View):
    def get(self, request, *args, **kwargs):
        instance = SiteSettings.objects.all().first()
        edit_form = SettingsEditForm(instance=instance)
        return render(
            request, "administrative/settings/settings_edit.html", {"form": edit_form}
        )
