from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student, Tag
from .models import Event, Inquiry, SiteSettings, Announcements
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

from .forms import BookForm, cancelEventForm, EditEventForm
from .decorators import lead_started, parent_required
from django.contrib import messages
from django.http import Http404

from django.conf import settings
import pytz

from .utils import check_inquiry_reopen

from general_tasks.utils import EventPDFExport
import datetime
from django.http import FileResponse

import logging

# Create your views here.

parent_decorators = [login_required, parent_required]


@login_required
@parent_required
def public_dashboard(request):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(respondent=request.user))
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append(
            {
                "inquiry": inquiry,
                "url": reverse(
                    "inquiry_detail_view",
                    args=[urlsafe_base64_encode(force_bytes(inquiry.id))],
                ),
            }
        )

    # Hier werden alle events anhand ihres Datums aufgeteilt
    events = Event.objects.filter(Q(parent=request.user), Q(occupied=True))
    dates = []

    datetime_objects = events.order_by("start").values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in [
            date.date() for date in dates
        ]:
            # print(datetime_object.astimezone(pytz.UTC).date())
            dates.append(datetime_object.astimezone(pytz.UTC))

    events_dict = {}
    for date in dates:
        #! Spontane Änderung aufgrund von Problemen auf dem Server
        events_dict[str(date.date())] = events.filter(
            Q(
                start__gte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                )
            ),
            Q(
                start__lte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                )
            ),
        ).order_by("start")

    announcements = Announcements.objects.filter(
        Q(user=request.user), Q(read=False)
    ).order_by("-created")

    return render(
        request,
        "dashboard/public_dashboard.html",
        {
            "inquiries": custom_inquiries,
            "events_dict": events_dict,
            "events": events,
            "announcements": announcements,
        },
    )


@login_required
@parent_required
def search(request):
    teachers = CustomUser.objects.filter(role=1)
    teacherExtraData = TeacherExtraData.objects.all()
    request_search = request.GET.get("q", None)
    state = 0
    result = []
    page_number = request.GET.get("page")

    if request_search is None:
        print("Keine Frage")
        result = teachers
    # elif request_search.startswith("#"):
    #     request_search = request_search[1:]
    #     tags = Tag.objects.filter(
    #         Q(name__icontains=request_search) | Q(synonyms__icontains=request_search)
    #     ).order_by(
    #         "name"
    #     )  # get a list of all matching tags

    #     for tag in tags:
    #         extraData = teacherExtraData.filter(tags=tag)

    #         for data in extraData:
    #             teacher = data.teacher
    #             if not teacher in result:
    #                 result.append(teacher)
    # else:
    #     for data in (
    #         teachers.filter(last_name__icontains=request_search)
    #         .order_by("first_name")
    #         .order_by("last_name")
    #     ):
    #         if not data in result:
    #             result.append(data)
    #     # result = teachers.filter(last_name__icontains=request_search)
    #     for data in teacherExtraData.filter(acronym__icontains=request_search):
    #         if not data.teacher in result:
    #             result.append(data.teacher)
    else:
        search_split = str(request_search).split()
        if len(search_split) == 0:
            result = teachers
        else:
            search_teacher_name = CustomUser.objects.none()
            search_extradata_acronym = CustomUser.objects.none()
            search_tags = Tag.objects.none()
            for key in search_split:
                print(key, "Key")
                queryset_name = CustomUser.objects.filter(
                    Q(is_active=True), Q(role=1)
                ).filter(Q(first_name__icontains=key) | Q(last_name__icontains=key))

                queryset_tags = Tag.objects.filter(
                    Q(name__icontains=key) | Q(synonyms__icontains=key)
                )

                search_tags = search_tags.union(search_tags, queryset_tags)

                queryset_acronym = TeacherExtraData.objects.filter(
                    acronym__icontains=key
                )

                search_extradata_acronym = search_extradata_acronym.union(
                    search_extradata_acronym, queryset_acronym
                )

                if search_teacher_name.intersection(
                    search_teacher_name, queryset_name
                ).exists():
                    print("Exists")
                    search_teacher_name = search_teacher_name.intersection(
                        search_teacher_name, queryset_name
                    )
                else:
                    search_teacher_name = search_teacher_name.union(
                        search_teacher_name, queryset_name
                    )

                print(queryset_name, queryset_acronym, queryset_tags)
            # search_teacher = CustomUser.objects.none()
            search_teacher = []
            search_extradata_tags = TeacherExtraData.objects.none()
            search_extradata = TeacherExtraData.objects.none()

            for tag in search_tags:
                new_extradata = TeacherExtraData.objects.filter(tags=tag)
                search_extradata_tags = search_extradata_tags.union(
                    search_extradata_tags, new_extradata
                )

            search_extradata = search_extradata.union(
                search_extradata_acronym, search_extradata_tags
            )

            # TODO: Hier sollte es auch mit Union gemacht werden, um weiterhin ein Queryset zu erhalten, welches sortiert werden kann und damit nur die Übereinstimmungen zwischen mehreren Querysets genommen werden und somit nach möglichkeit eine eindeutige Lehrerwahl entsteht
            for extradata in search_extradata:
                if not extradata.teacher in search_teacher:
                    search_teacher.append(extradata.teacher)
            for teacher in search_teacher_name:
                if not teacher in search_teacher:
                    search_teacher.append(teacher)
            # print(search_teacher)

            # for extradata in search_extradata:
            #     new_teacher = extradata.teacher
            #     search_teacher = search_teacher.union(search_teacher, new_teacher)
            #     print(search_teacher)
            # print(search_extradata_tags, search_extradata_acronym, search_extradata)
            result = search_teacher
    custom_result = []

    for teacher in result:
        teacher_id = urlsafe_base64_encode(force_bytes(teacher.id))
        custom_result.append(
            {
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "email": teacher.email,
                "url": reverse("event_teacher_list", args=[teacher_id]),
            }
        )  # notwendig um den Url parameter zu dem queryset hinzu zu fügen
    # return render(request, 'dashboard/search.html', {'teachers': result, 'search': request_search})

    paginator = Paginator(custom_result, 25)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/search.html",
        {"teachers": page_obj, "state": state, "request_search": request_search},
    )


@login_required
@parent_required
# man erhält eine Liste mit allen freien Terminen des Lehrers
def bookEventTeacherList(request, teacher_id):
    try:
        teacher = CustomUser.objects.filter(role=1).get(
            id__exact=force_str(urlsafe_base64_decode(teacher_id))
        )  # get the teacher for the id
    except CustomUser.DoesNotExist:
        raise Http404("Lehrer wurde nicht gefunden")
    except CustomUser.MultipleObjectsReturned:
        print("Error")
    else:
        # events = []
        # for event in Event.objects.filter(Q(teacher=teacher)):
        #     events.append({'event': event, 'url': reverse ('book_event_per_id', args=[event.id]), 'occupied': event.occupied}) ???? wofür das ganze????

        events = Event.objects.filter(Q(teacher=teacher))

        # personal_booked_events = []
        # for event in Event.objects.filter(Q(occupied=True), Q(parent=request.user)):
        #     personal_booked_events.append({'event': event, 'url': reverse('event_per_id', args=[event.id])})

        personal_booked_events = events.filter(Q(occupied=True), Q(parent=request.user))

        events_dt = Event.objects.filter(Q(teacher=teacher))

        dates = []
        datetime_objects = events_dt.order_by("start").values_list("start", flat=True)
        for datetime_object in datetime_objects:
            if timezone.localtime(datetime_object).date() not in [
                date.date() for date in dates
            ]:
                # print(datetime_object.astimezone(pytz.UTC).date())
                dates.append(datetime_object.astimezone(pytz.UTC))

        events_dt_dict = {}
        # print(Event.objects.filter(Q(teacher=teacher)).order_by(
        #     'start').values_list("start", flat=True))
        # print("DATES", dates)
        for date in dates:
            # print("TIME", timezone.datetime.combine(date.date(),
            #       timezone.datetime.strptime("00:00:00", "%H:%M:%S").time()))

            #! Spontane Änderung aufgrund von Problemen auf dem Server
            events_dt_dict[str(date.date())] = Event.objects.filter(
                Q(teacher=teacher),
                Q(
                    start__gte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                    )
                ),
                Q(
                    start__lte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                    )
                ),
            ).order_by("start")

        # print(events_dt_dict)

        tags = TeacherExtraData.objects.get(teacher=teacher).tags.all().order_by("name")

        image = TeacherExtraData.objects.filter(Q(teacher=teacher))[0].image.url

        booked_times = []
        for event in Event.objects.filter(
            Q(parent=request.user), Q(occupied=True)
        ).values_list("start", flat=True):
            time = timezone.localtime(event)
            booked_times.append(time)

    return render(
        request,
        "dashboard/events/teacher.html",
        {
            "teacher": teacher,
            "events": events,
            "personal_booked_events": personal_booked_events,
            "events_dt": events_dt,
            "events_dt_dict": events_dt_dict,
            "tags": tags,
            "image": image,
            "booked_times": booked_times,
        },
    )


@method_decorator(parent_required, name="dispatch")
# hier werden final die Termine dann gebucht
class bookEventView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")

        # Ab hier verändert, um Anfragen zu zu lassen
        inquiry_id_get = request.GET.get("inquiry")
        if inquiry_id_get:
            try:
                inquiry = Inquiry.objects.get(
                    Q(respondent=request.user),
                    Q(id=force_str(urlsafe_base64_decode(inquiry_id_get))),
                    Q(type=0),
                )
            except Inquiry.DoesNotExist:
                # Es ist ein Fehler passiert, deswegen wird die "standard" Variante ausgeführt
                messages.error(
                    request,
                    "Die angegebene Anfrage konnte leider nicht gefunden werden.",
                )
                form = BookForm(request=request, teacher=event.teacher)
                teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
                back_url = reverse("event_teacher_list", args=[teacher_id])
            else:
                form = BookForm(
                    request=request,
                    teacher=event.teacher,
                    initial={
                        "student": [student.id for student in inquiry.students.all()]
                    },
                )
                back_url = reverse("inquiry_detail_view", args=[inquiry_id_get])
        else:
            # Das event wurde nicht über eine Anfrage aufgerufen
            form = BookForm(request=request, teacher=event.teacher)
            teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
            back_url = reverse("event_teacher_list", args=[teacher_id])

        booked_times = []
        for b_times in Event.objects.filter(
            Q(parent=request.user), Q(occupied=True)
        ).values_list("start", flat=True):
            time = timezone.localtime(b_times)
            booked_times.append(time)

        return render(
            request,
            "dashboard/events/book.html",
            {
                "event": event,
                "book_form": form,
                "back_url": back_url,
                "booked_times": booked_times,
            },
        )

    def post(self, request, event_id):
        # try:
        #     event = Event.objects.get(id=event_id)
        # except Event.MultipleObjectsReturned:
        #     print("error")
        # except Event.DoesNotExist:
        #     raise Http404("This event was not found")
        # else:
        event = get_object_or_404(Event, id=event_id)
        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")
        # , initial={"choices": event.student}
        form = BookForm(request.POST, request=request, teacher=event.teacher)
        if form.is_valid():
            students = []
            for student in form.cleaned_data["student"]:
                try:
                    model_student = Student.objects.get(id=student)
                except Student.DoesNotExist:
                    raise Http404("Error")
                else:
                    students.append(model_student)
            # ? validation of students needed or given through the form
            inquiry = Inquiry.objects.create(
                type=1,
                event=event,
                requester=request.user,
                respondent=event.teacher,
                reason="",
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

        booked_times = []
        for b_times in Event.objects.filter(
            Q(parent=request.user), Q(occupied=True)
        ).values_list("start", flat=True):
            time = timezone.localtime(b_times)
            booked_times.append(time)

        return render(
            request,
            "dashboard/events/book.html",
            {
                "event": event,
                "book_form": form,
                "teacher_url": url,
                "booked_times": booked_times,
            },
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
            return render(
                request,
                "dashboard/inquiry_answered.html",
                {
                    "inquiry_id": inquiry_id,
                    "inquiry": inquiry,
                    "teacher_id": teacher_id,
                },
            )

        # form = InquiryForm(
        #     request=request, selected_student=inquiry.students.first, teacher=inquiry.requester, parent=inquiry.respondent)

        events = Event.objects.filter(Q(teacher=inquiry.requester))

        events_dt = Event.objects.filter(Q(teacher=inquiry.requester))
        dates = []
        datetime_objects = events_dt.order_by("start").values_list("start", flat=True)
        for datetime_object in datetime_objects:
            if timezone.localtime(datetime_object).date() not in [
                date.date() for date in dates
            ]:
                # print(datetime_object.astimezone(pytz.UTC).date())
                dates.append(datetime_object.astimezone(pytz.UTC))

        events_dt_dict = {}
        for date in dates:
            events_dt_dict[str(date.date())] = events.filter(
                Q(
                    start__gte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                    )
                ),
                Q(
                    start__lte=timezone.datetime.combine(
                        date.date(),
                        timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                    )
                ),
            ).order_by("start")

        booked_times = []
        for b_times in Event.objects.filter(
            Q(parent=request.user), Q(occupied=True)
        ).values_list("start", flat=True):
            time = timezone.localtime(b_times)
            booked_times.append(time)

        return render(
            request,
            "dashboard/inquiry.html",
            {
                "inquiry_id": inquiry_id,
                "inquiry": inquiry,
                "events": events,
                "events_dt": events_dt,
                "events_dt_dict": events_dt_dict,
                "teacher_id": teacher_id,
                "booked_times": booked_times,
            },
        )

    # def post(self, request, inquiry_id):
    #     inquiry = get_object_or_404(Inquiry.objects.filter(Q(requester=request.user) | Q(respondent=request.user)), type=0, id=force_str(
    #         urlsafe_base64_decode(inquiry_id)))

    #     if inquiry.processed:  # Die Anfrage wurde bereits bearbeitet
    #         return render(request, "dashboard/error/inquiry_ocupied.html")

    #     form = InquiryForm(request.POST,
    #                        request=request, selected_student=inquiry.students.first, teacher=inquiry.requester, parent=inquiry.respondent)
    #     if form.is_valid():
    #         event = form.cleaned_data['event']
    #         event.parent = inquiry.respondent
    #         students = form.cleaned_data['student']

    #         event.student.set(students)
    #         event.occupied = True
    #         event.save()
    #         messages.success(request, "Gebucht")
    #         return redirect('home')
    #     return render(request, "dashboard/inquiry.html", {'reason': inquiry, 'form': form})


@method_decorator(parent_required, name="dispatch")
class EventView(View):
    cancel_form = cancelEventForm

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, parent=request.user)
        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")
        edit_form = EditEventForm(
            request=request,
            teacher=event.teacher,
            event=event,
            initial={"student": [student.id for student in event.student.all()]},
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

        edit_form = EditEventForm(
            request=request,
            teacher=event.teacher,
            event=event,
            initial={"student": [student.id for student in event.student.all()]},
        )
        cancel_form = self.cancel_form()

        # Es wurde die Cancel-Form zurück gegeben
        if "cancel_event" in request.POST:
            cancel_form = self.cancel_form(request.POST)
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
                try:
                    inquiry = Inquiry.objects.get(
                        Q(type=1),
                        Q(requester=request.user),
                        Q(respondent=event.teacher),
                        Q(event=event),
                        Q(processed=False),
                    )
                except Inquiry.DoesNotExist:
                    pass
                except Inquiry.MultipleObjectsReturned:
                    inquiries = inquiry = Inquiry.objects.filter(
                        Q(type=1),
                        Q(requester=request.user),
                        Q(respondent=event.teacher),
                        Q(event=event),
                        Q(processed=False),
                    )
                    for inquiry in inquiries:
                        inquiry.processed = True
                        inquiry.save()

                        logger = logging.getLogger(__name__)
                        logger.warn(
                            "Es waren mehrere unbeantwortete Inquiries verfügbar."
                        )
                else:
                    inquiry.processed = True
                    inquiry.save()

                event.parent = None
                event.status = 0
                event.occupied = False
                event.student.clear()
                event.save()
                messages.success(request, "Der Termin wurde erfolgreich abgesagt")
                return redirect("home")

        # Es wurde die Book-Form zurück gegeben
        if "edit_event" in request.POST:
            edit_form = EditEventForm(
                request.POST, request=request, teacher=event.teacher, event=event
            )

            if edit_form.is_valid():
                students = []
                for student in edit_form.cleaned_data["student"]:
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


@login_required
def markAnnouncementRead(request, announcement_id):
    announcement = get_object_or_404(
        Announcements,
        id__exact=force_str(urlsafe_base64_decode(announcement_id)),
        user=request.user,
    )
    announcement.read = True
    announcement.save()
    return redirect("..")


@login_required
def markAllAnnouncementsRead(request):
    announcements = Announcements.objects.filter(Q(user=request.user), Q(read=False))
    for announcement in announcements:
        announcement.read = True
        announcement.save()
    messages.success(request, "Alle Mitteilungen wurden als gelesen markiert.")
    return redirect("..")


def impressum(request):
    try:
        settings = SiteSettings.objects.first()
    except SiteSettings.DoesNotExist:
        raise Http404("Es wurden keine Einstellungen für diese Seite gefunden.")
    else:
        return redirect(settings.impressum)


@login_required
def create_event_PDF(request):
    pdf_generator = EventPDFExport(request.user.id)
    return FileResponse(
        pdf_generator.print_events(),
        as_attachment=False,
        filename=f'events_{datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.pdf',
        content_type="application/pdf",
    )


@method_decorator(login_required, name="dispatch")
class AnnouncementsAllUsers(ListView):
    model = Announcements

    template_name = "dashboard/announcements/announcements_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super(AnnouncementsAllUsers, self).get_queryset(*args, **kwargs)
        qs = qs.filter(Q(user=self.request.user), Q(read=False))
        qs = qs.order_by("-created")
        return qs
