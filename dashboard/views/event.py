from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student, Tag
from ..models import Event, Inquiry, SiteSettings, Announcements
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.views import View
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator

from django.shortcuts import get_object_or_404
from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from ..forms import BookForm, cancelEventForm, EditEventForm
from ..decorators import lead_started, parent_required
from django.contrib import messages
from django.http import Http404

from django.conf import settings
import pytz

from ..utils import check_inquiry_reopen, check_parent_book_event_allowed

from general_tasks.utils import EventPDFExport
import datetime
from django.http import FileResponse

import logging

from ..helpers import create_event_date_dict, event_date_dict_add_book_information

# Create your views here.

parent_decorators = [login_required, parent_required]


@login_required
@parent_required
# man erhält eine Liste mit allen freien Terminen des Lehrers
def bookEventTeacherList(request, teacher_id):
    teacher = get_object_or_404(
        CustomUser.objects.filter(role=1),
        id__exact=force_str(urlsafe_base64_decode(teacher_id)),
    )
    events = Event.objects.filter(Q(teacher=teacher))

    events_dt_dict = event_date_dict_add_book_information(
        request.user, create_event_date_dict(events)
    )

    personal_booked_events = events.filter(Q(occupied=True), Q(parent=request.user))

    tags = TeacherExtraData.objects.get(teacher=teacher).tags.all().order_by("name")

    image = TeacherExtraData.objects.filter(Q(teacher=teacher))[0].image.url

    parent_can_book_event = check_parent_book_event_allowed(
        parent=request.user, teacher=teacher
    )

    return render(
        request,
        "dashboard/events/teacher.html",
        {
            "teacher": teacher,
            "events": events,
            "personal_booked_events": personal_booked_events,
            "events_dt_dict": events_dt_dict,
            "tags": tags,
            "image": image,
            "parent_can_book_event": parent_can_book_event,
        },
    )


@method_decorator(parent_required, name="dispatch")
# hier werden final die Termine dann gebucht
class bookEventView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        inquiry = None

        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")

        parent_can_book_event = check_parent_book_event_allowed(
            parent=request.user, event=event
        )

        if not parent_can_book_event:
            messages.error(
                request,
                "You are not allowed to book this event. Please choose a different event if possible.",
            )
            return redirect(
                "event_teacher_list",
                urlsafe_base64_encode(force_bytes(event.teacher.id)),
            )

        # Ab hier verändert, um Anfragen zu zu lassen
        inquiry_id_get = request.GET.get("inquiry")
        if inquiry_id_get:
            try:
                inquiry = Inquiry.objects.get(
                    Q(respondent=request.user),
                    Q(id=force_str(urlsafe_base64_decode(inquiry_id_get))),
                    Q(type=0),
                    Q(base_event=event.get_base_event()),
                )
            except Inquiry.DoesNotExist:
                # Es ist ein Fehler passiert, deswegen wird die "standard" Variante ausgeführt
                messages.error(
                    request,
                    "Die angegebene Anfrage konnte leider nicht gefunden werden.",
                )
                form = BookForm(instance=event, request=request)
                teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
                back_url = reverse("event_teacher_list", args=[teacher_id])
            else:
                form = BookForm(instance=event, request=request, inquiry=inquiry)
                back_url = reverse("inquiry_detail_view", args=[inquiry_id_get])
        else:
            # Das event wurde nicht über eine Anfrage aufgerufen
            form = BookForm(instance=event, request=request)
            teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
            back_url = reverse("event_teacher_list", args=[teacher_id])
        if event.lead_status == 2:
            messages.info(
                request,
                "Dieser Termin ist derzeit in der Verfügbarkeit eingeschränkt. Aus diesem Grund müssen Sie mindestens einen der markierten Lernenden zur Buchung des Termins anwählen.",
            )
        return render(
            request,
            "dashboard/events/book.html",
            {
                "event": event,
                "book_form": form,
                "back_url": back_url,
                "inquiry": inquiry,
            },
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        inquiry = None
        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")

        parent_can_book_event = check_parent_book_event_allowed(
            parent=request.user, event=event
        )
        if not parent_can_book_event:
            messages.error(
                request,
                "You are not allowed to book this event. Please choose a different event if possible.",
            )
            return redirect(
                "event_teacher_list",
                urlsafe_base64_encode(force_bytes(event.teacher.id)),
            )

        # , initial={"choices": event.student}
        # form = BookForm(request.POST, instance=event, request=request)

        inquiry_id_get = request.GET.get("inquiry")
        if inquiry_id_get:
            try:
                inquiry = Inquiry.objects.get(
                    Q(respondent=request.user),
                    Q(id=force_str(urlsafe_base64_decode(inquiry_id_get))),
                    Q(type=0),
                    Q(base_event=event.get_base_event()),
                )
            except Inquiry.DoesNotExist:
                # Es ist ein Fehler passiert, deswegen wird die "standard" Variante ausgeführt
                messages.error(
                    request,
                    "Die angegebene Anfrage konnte leider nicht gefunden werden.",
                )
                form = BookForm(request.POST, instance=event, request=request)
            else:
                form = BookForm(
                    request.POST,
                    instance=event,
                    request=request,
                    inquiry=inquiry,
                )
        else:
            # Das event wurde nicht über eine Anfrage aufgerufen
            form = BookForm(request.POST, instance=event, request=request)

        if form.is_valid() and parent_can_book_event:
            students = []
            for student in form.cleaned_data["all_students"]:
                students.append(student)
            # ? validation of students needed or given through the form
            inquiry = Inquiry.objects.create(
                type=1,
                event=event,
                requester=request.user,
                respondent=event.teacher,
                reason="",
                base_event=event.get_base_event(),
            )
            inquiry.students.set(students)
            inquiry.save()
            event.parent = request.user
            event.status = 2
            event.student.set(students)
            event.occupied = True
            event.save()
            messages.success(request, "Angefragt")
            return redirect("event_per_id", event_id=event.id)

        teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
        url = reverse("event_teacher_list", args=[teacher_id])

        return render(
            request,
            "dashboard/events/book.html",
            {"event": event, "book_form": form, "back_url": url, "inquiry": inquiry},
        )


# Der Inquiry View wurde einmal neu gemacht, muss jetzt noch weiter so ergänzt werden, damit er schön aussieht
@method_decorator(parent_required, name="dispatch")
class InquiryView(View):
    def get(self, request, inquiry_id):
        inquiry = get_object_or_404(
            Inquiry.objects.filter(
                Q(requester=request.user) | Q(respondent=request.user)
            ),
            type=0,
            id=force_str(urlsafe_base64_decode(inquiry_id)),
        )

        teacher_id = urlsafe_base64_encode(force_bytes(inquiry.requester.id))

        if inquiry.processed:  # Die Anfrage wurde bereits bearbeitet
            messages.info(
                request,
                "You have already fullfilled the inquiry. No further action is needed.",
            )
            return redirect("home")

        events = Event.objects.filter(Q(teacher=inquiry.requester))

        events_dt_dict = event_date_dict_add_book_information(
            request.user, create_event_date_dict(events)
        )

        return render(
            request,
            "dashboard/inquiry.html",
            {
                "inquiry_id": inquiry_id,
                "inquiry": inquiry,
                "events": events,
                "events_dt_dict": events_dt_dict,
                "teacher_id": teacher_id,
            },
        )


@method_decorator(parent_required, name="dispatch")
class EventView(View):
    cancel_form = cancelEventForm

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, parent=request.user)
        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")
        elif not event.occupied:
            return redirect("book_event_per_id", event_id)

        edit_form = EditEventForm(
            instance=event,
            request=request,
        )

        if event.lead_status == 2:
            messages.info(
                request,
                "Dieser Termin ist derzeit in der Verfügbarkeit eingeschränkt. Aus diesem Grund müssen Sie mindestens einen der markierten Lernenden zur Buchung des Termins anwählen.",
            )
        return render(
            request,
            "dashboard/events/view.html",
            {
                "event": event,
                "cancel_form": self.cancel_form,
                "teacher_id": urlsafe_base64_encode(force_bytes(event.teacher.id)),
                "edit_form": edit_form,
            },
        )

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, parent=request.user)

        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")
        elif not event.occupied:
            return redirect("book_event_per_id", event_id)

        edit_form = EditEventForm(
            request.POST,
            instance=event,
            request=request,
        )

        if edit_form.is_valid():
            students = []
            for student in edit_form.cleaned_data["all_students"]:
                model_student = get_object_or_404(Student, id=student)
                students.append(model_student)
            # ? validation of students needed or given through the form
            # Hier wird überprüft, ob es eine Anfrage gab, für die das bearbeitete Event zuständig war
            check_inquiry_reopen(request.user, event.teacher)
            event.parent = request.user
            event.status = 2
            event.student.set(students)
            event.occupied = True
            event.save()
            messages.success(request, "Geändert")

        return render(
            request,
            "dashboard/events/view.html",
            {
                "event": event,
                "cancel_form": self.cancel_form,
                "teacher_id": urlsafe_base64_encode(force_bytes(event.teacher.id)),
                "edit_form": edit_form,
            },
        )


class CancelEventView(View):
    def get(self, request, event_id):
        return redirect("event_per_id", event_id)

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, parent=request.user)

        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")
        cancel_form = cancelEventForm(request.POST)
        edit_form = EditEventForm(
            instance=event,
            request=request,
            # teacher=event.teacher,
            # event=event,
            initial={"student": [student.id for student in event.student.all()]},
        )
        if cancel_form.is_valid():
            message = cancel_form.cleaned_data["message"]

            Announcements.objects.create(
                announcement_type=1,
                user=event.teacher,
                message="%s %s hat einen Termin abgesagt und folgende Nachricht hinterlassen: \n %s"
                % (request.user.first_name, request.user.last_name, message),
            )
            # Hier wird überprüft, ob es eine Anfrage gab, für die das bearbeitete Event zuständig war
            check_inquiry_reopen(request.user, event.teacher)

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
            messages.success(request, "Der Termin wurde erfolgreich abgesagt")
            return redirect("home")
        return render(
            request,
            "dashboard/events/view.html",
            {
                "event": event,
                "cancel_form": self.cancel_form,
                "teacher_id": urlsafe_base64_encode(force_bytes(event.teacher.id)),
                "edit_form": edit_form,
            },
        )


@login_required
def create_event_PDF(request):
    pdf_generator = EventPDFExport(request.user.id)
    return FileResponse(
        pdf_generator.print_events(),
        as_attachment=False,
        filename=f'events_{datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.pdf',
        content_type="application/pdf",
    )
