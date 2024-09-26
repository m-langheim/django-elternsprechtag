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
from ..forms_helpers import get_students_choices_for_event
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from general_tasks.tasks import async_send_mail

from django.contrib.admin.views.decorators import staff_member_required

from dashboard.models import Event, EventChangeFormula, Announcements, Inquiry
from dashboard.tasks import async_create_events_special, apply_event_change_formular

from dashboard.utils import check_inquiry_reopen

import csv, io, os

from django.utils.decorators import method_decorator

login_staff = [login_required, staff_member_required]


@method_decorator(login_staff, name="dispatch")
@method_decorator(permission_required("dashboard.approve_disapprove"), name="dispatch")
class AdministrativeFormulaApprovalView(View):
    def get(self, request):
        formulars = EventChangeFormula.objects.filter(
            Q(date__gte=timezone.now()), Q(status=1)
        )
        formulars_table = EventFormularActionTable(formulars)

        approved_formulars_table = EventFormularOldTable(
            EventChangeFormula.objects.filter(Q(date__gte=timezone.now())).filter(
                Q(status=2) | Q(status=3)
            )
        )

        upcomming_formulars_table = EventFormularUpcommingTable(
            EventChangeFormula.objects.filter(Q(date__gte=timezone.now()), Q(status=0))
        )

        formular_form = EventChangeFormularForm()

        dates = DayEventGroup.objects.filter(date__gte=timezone.now()).order_by("date")
        date_context = []
        for date in dates:
            date_context.append(
                {
                    "date": date.date,
                    "id": force_str(urlsafe_base64_encode(force_bytes(date.id))),
                }
            )

        return render(
            request,
            "administrative/time_slots/overview.html",
            {
                "action_table": formulars_table,
                "action_table_entries": formulars.count(),
                "upcomming_table": upcomming_formulars_table,
                "upcomming_table_entries": EventChangeFormula.objects.filter(
                    Q(status=0), Q(date__gte=timezone.now())
                ).count(),
                "approved_formulars_table": approved_formulars_table,
                "closed_table_entries": EventChangeFormula.objects.filter(
                    Q(status=2) | Q(status=3)
                ).count(),
                "change_formular": formular_form,
                "change_formular_new": EventAddNewDateForm(),
                "dates": date_context,
            },
        )


@method_decorator(login_staff, name="dispatch")
@method_decorator(permission_required("dashboard.approve_disapprove"), name="dispatch")
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


@method_decorator(login_staff, name="dispatch")
class EventsListView(SingleTableMixin, FilterView):
    table_class = Eventstable
    template_name = "administrative/time_slots/events_table.html"
    model = Event
    filterset_class = EventFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates = DayEventGroup.objects.filter(date__gte=timezone.now()).order_by("date")
        date_context = []
        for date in dates:
            date_context.append(
                {
                    "date": date.date,
                    "id": force_str(urlsafe_base64_encode(force_bytes(date.id))),
                }
            )
        context["change_formular"] = EventChangeFormularForm()
        context["dates"] = date_context
        context["change_formular_new"] = EventAddNewDateForm()
        return context

    def get_queryset(self, *args, **kwargs):
        return Event.objects.filter(start__gte=timezone.now()).all()


@method_decorator(login_staff, name="dispatch")
class EventDetailView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        edit_form = EventEditForm(instance=event)

        add_student_form = EventAddStudentForm(instance=event)

        choices = get_students_choices_for_event(event)

        return render(
            request,
            "administrative/events/event_edit.html",
            {
                "form": edit_form,
                "event": event,
                "add_student_form": add_student_form,
                "choices": choices,
            },
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        edit_form = EventEditForm(instance=event, data=request.POST)

        add_student_form = EventAddStudentForm(instance=event)

        if edit_form.is_valid():
            edit_form.save()

        edit_form = EventEditForm(instance=event)

        choices = get_students_choices_for_event(event)

        return render(
            request,
            "administrative/events/event_edit.html",
            {
                "form": edit_form,
                "event": event,
                "add_student_form": add_student_form,
                "choices": choices,
            },
        )

@method_decorator(login_staff, name="dispatch")
class EventAddStudentView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        form = EventAddStudentForm(instance=event)

        return render(
            request,
            "administrative/events/event_edit.html",
            {"form": form, "event": event},
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        form = EventAddStudentForm(instance=event, data=request.POST)

        if form.is_valid():
            form.save()

            return redirect("administrative_event_detail_view", event_id)

        return render(
            request,
            "administrative/events/event_edit.html",
            {"form": form, "event": event},
        )

@method_decorator(login_staff, name="dispatch")
class EventClearView(View):
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        parent = event.parent

        Announcements.objects.create(
            announcement_type=1,
            user=event.teacher,
            message="The portal organizer has canceled an event. Now others are able to book this event again.",
        )

        # Hier wird die vom Elternteil möglicherweise gestellte anfrage als bearbeitet angezeigt
        inquiries = Inquiry.objects.filter(
            Q(type=1),
            Q(requester=request.user),
            Q(respondent=event.teacher),
            Q(event=event),
            Q(processed=False),
        )
        inquiries.update(processed=True)

        event.parent = None
        event.status = 0
        event.occupied = False
        event.student.clear()
        event.save()

        check_inquiry_reopen(parent, event.teacher)

        return redirect("administrative_event_detail_view", event_id)


@method_decorator(login_staff, name="dispatch")
class EventBlockView(View):
    def get(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            messages.error(request, "Das gesuchte Event konnte nicht gefunden werden.")
            return redirect("..")
        else:
            event.lead_status = 0
            event.lead_manual_override = True
            event.save()
            return redirect("..")


@method_decorator(login_staff, name="dispatch")
class EventChangeFormularAddView(View):
    def post(self, request, event_group_id):
        day_group = get_object_or_404(
            DayEventGroup, id=force_str(urlsafe_base64_decode(event_group_id))
        )

        form = EventChangeFormularForm(request.POST)

        if form.is_valid():
            date = day_group.date
            teachers = form.cleaned_data["teacher"]

            for teacher in teachers:
                teacher_event_group, created = TeacherEventGroup.objects.get_or_create(
                    day_group=day_group,
                    lead_start=day_group.lead_start,
                    lead_inquiry_start=day_group.lead_inquiry_start,
                    teacher=teacher,
                )
                EventChangeFormula.objects.get_or_create(
                    teacher=teacher,
                    date=date,
                    day_group=day_group,
                    teacher_event_group=teacher_event_group,
                    status=0,
                )
            return redirect("administrative_event_formular_view")


@method_decorator(login_staff, name="dispatch")
class EventAddNewDateAndFormularsView(View):
    def post(self, request):
        form = EventAddNewDateForm(request.POST)

        if form.is_valid():
            base_event = form.cleaned_data["base_event"]
            date = form.cleaned_data["date"]
            teachers = form.cleaned_data["teacher"]

            if not base_event:
                base_event = BaseEventGroup.objects.create(
                    lead_start=form.cleaned_data["lead_start"],
                    lead_inquiry_start=form.cleaned_data["lead_inquiry_start"],
                )

            day_group, created = DayEventGroup.objects.get_or_create(
                base_event=base_event,
                date=date,
                lead_start=form.cleaned_data["lead_start"],
                lead_inquiry_start=form.cleaned_data["lead_inquiry_start"],
            )

            for teacher in teachers:
                teacher_event_group, created = TeacherEventGroup.objects.get_or_create(
                    day_group=day_group,
                    lead_start=day_group.lead_start,
                    lead_inquiry_start=day_group.lead_inquiry_start,
                    teacher=teacher,
                )
                EventChangeFormula.objects.get_or_create(
                    teacher=teacher,
                    date=date,
                    day_group=day_group,
                    teacher_event_group=teacher_event_group,
                    status=0,
                )
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
                # async_create_events_special.delay(
                #     [formula.teacher.id],
                #     formula.date.strftime("%Y-%m-%d"),
                #     formula.start_time.strftime("%H:%M:%S"),
                #     formula.end_time.strftime("%H:%M:%S"),
                # )
                apply_event_change_formular.delay(formula.id)

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
