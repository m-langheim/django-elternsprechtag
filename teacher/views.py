from django.shortcuts import render, redirect
from authentication.models import CustomUser, TeacherExtraData
from dashboard.models import Inquiry, Student, Event, Announcements
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from .decorators import teacher_required
from .forms import *
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import BadRequest

import pytz

# pdf gen
from io import BytesIO
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import FileResponse
import datetime
from reportlab.lib.units import cm
from functools import partial
from reportlab.platypus.frames import Frame

# Create your views here.

from django.urls import reverse
from django.contrib import messages
from django.utils import timezone


teacher_decorators = [login_required, teacher_required]


@login_required
@teacher_required
def dashboard(request):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(
        requester=request.user), Q(processed=False))
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append({'inquiry': inquiry, 'url': reverse(
            'teacher_show_inquiry', args=[urlsafe_base64_encode(force_bytes(inquiry.id))])})

    # Hier werden alle events anhand ihres Datums aufgeteilt
    events = Event.objects.filter(Q(teacher=request.user), Q(occupied=True))
    dates = []

    datetime_objects = events.order_by('start').values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in [date.date() for date in dates]:
            # print(datetime_object.astimezone(pytz.UTC).date())
            dates.append(datetime_object.astimezone(pytz.UTC))

    events_dict = {}
    for date in dates:
        #! Spontane Änderung aufgrund von Problemen auf dem Server
        events_dict[str(date.date())] = events.filter(
            Q(start__gte=timezone.datetime.combine(
                date.date(),
                timezone.datetime.strptime("00:00:00", "%H:%M:%S").time()
            )),
            Q(start__lte=timezone.datetime.combine(
                date.date(),
                timezone.datetime.strptime("23:59:59", "%H:%M:%S").time()
            ))).order_by('start')

    announcements = Announcements.objects.filter(
        Q(user=request.user), Q(read=False)).order_by("-created")

    return render(request, "teacher/dashboard.html", {'inquiries': custom_inquiries, 'events': events, "events_dict": events_dict, "announcements": announcements})


@login_required
@teacher_required
def studentList(request):
    search = request.GET.get("q", None)
    page_number = request.GET.get("page")
    if search is None:
        students = Student.objects.all()
    else:
        students = Student.objects.filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search)).order_by('id')
    paginator = Paginator(students, 25)
    page_obj = paginator.get_page(page_number)
    print(page_obj)
    return render(request, "teacher/studentList.html", {'page_obj': page_obj})


@method_decorator(teacher_decorators, name='dispatch')
class DetailStudent(View):
    def get(self, request):
        return render(request, "teacher/student.html")


@method_decorator(teacher_decorators, name='dispatch')
class InquiryView(View):
    form_class = editInquiryForm

    def get(self, request, id):
        try:
            inquiry = Inquiry.objects.get(Q(type=0), Q(id__exact=force_str(
                urlsafe_base64_decode(id))), Q(requester=request.user))
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            print(inquiry.respondent)
            initial = {'reason': inquiry.reason,
                       'student': inquiry.students.first,
                       'parent': inquiry.respondent,
                       'event': inquiry.event}
            form = self.form_class(initial=initial)
            print(inquiry)
            return render(request, "teacher/inquiry.html", {'form': form, "student": inquiry.students.first, "f_inquiry_id": urlsafe_base64_encode(force_bytes(inquiry.id))})

    def post(self, request, id):
        try:
            inquiry = Inquiry.objects.get(Q(type=0), Q(id__exact=force_str(
                urlsafe_base64_decode(id))))
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            initial = {'reason': inquiry.reason,
                       'student': inquiry.students.first,
                       'parent': inquiry.respondent,
                       'event': inquiry.event}
            form = self.form_class(request.POST, initial=initial)
            if form.is_valid():
                inquiry.reason = form.cleaned_data['reason']
                inquiry.save()
                messages.success(request, "Änderungen angenommen")
                return redirect('teacher_dashboard')
            return render(request, "teacher/inquiry.html", {'form': form, "student": inquiry.students.first, "f_inquiry_id": urlsafe_base64_encode(force_bytes(inquiry.id))})


@method_decorator(teacher_decorators, name="dispatch")
class DeleteInquiryView(View):
    def get(self, request, inquiryID):
        try:
            inquiry = Inquiry.objects.get(Q(type=0), Q(id__exact=force_str(
                urlsafe_base64_decode(inquiryID))), Q(requester=request.user))
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            inquiry.delete()
            return redirect("teacher_dashboard")


@method_decorator(teacher_decorators, name='dispatch')
class CreateInquiryView(View):

    def get(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            raise Http404("Student not found")
        else:
            # redirect the user if an inquiry already exists ==> prevent the userr to create a new one
            inquiry = Inquiry.objects.filter(Q(type=0), Q(
                students=student), Q(requester=request.user))
            if inquiry:
                messages.info(
                    request, "Sie haben bereits eine Anfrage für dieses Kind erstellt. Im folgenden haben Sie die Möglichkeit diese Anfrage zu bearbeiten.")
                return redirect('teacher_show_inquiry', id=urlsafe_base64_encode(force_bytes(inquiry.first().id)))

            # let the user create a new inquiry
            parent = CustomUser.objects.filter(
                Q(role=0), Q(students=student)).first
            initial = {'student': student, 'parent': parent}
            form = createInquiryForm(initial=initial)

            if len(Event.objects.filter(Q(teacher=request.user), Q(student=student))) != 0:
                messages.warning(
                    request, "Sie haben bereits einen Termin mit diesem Kind.")

        return render(request, "teacher/createInquiry.html", {'form': form, "student": student})

    def post(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            raise Http404("Student not found")
        else:
            # redirect the user if an inquiry already exists ==> prevent the userr to create a new one
            inquiry = Inquiry.objects.filter(Q(type=0), Q(
                students=student), Q(requester=request.user))
            if inquiry:
                messages.info(
                    request, "Sie haben bereits eine Anfrage für dieses Kind erstellt. Im folgenden haben Sie die Möglichkeit diese Anfrage zu bearbeiten.")
                return redirect('teacher_show_inquiry', id=urlsafe_base64_encode(force_bytes(inquiry.first().id)))

            # let the user create a new inquiry
            parent = CustomUser.objects.filter(
                Q(role=0), Q(students=student)).first
            initial = {'student': student, 'parent': parent}
            form = createInquiryForm(request.POST, initial=initial)
            if form.is_valid():
                inquiry = Inquiry.objects.create(
                    requester=request.user, respondent=form.cleaned_data["parent"], reason=form.cleaned_data["reason"], type=0)
                inquiry.students.set([form.cleaned_data["student"]])
                messages.success(request, "Anfrage erstellt")
                return redirect('teacher_dashboard')
        return render(request, "teacher/createInquiry.html", {'form': form, "student": student})


@login_required
@teacher_required
def confirm_event(request, event):
    try:
        event = Event.objects.get(Q(teacher=request.user), Q(id=event))
    except Event.DoesNotExist:
        messages.error(request, "Dieser Termin konnte nicht gefunden werden")
    else:
        event.status = 1
        event.occupied = True
        event.save()
        inquiry = event.inquiry_set.all().first()
        inquiry.processed = True
        inquiry.save()
    return redirect("teacher_dashboard")


@login_required
@teacher_required
def markAnnouncementRead(request, announcement_id):
    try:
        announcement = Announcements.objects.get(Q(id__exact=force_str(
            urlsafe_base64_decode(announcement_id))))
    except Announcements.DoesNotExist:
        raise Http404("Mitteilung nicht gefunden")
    else:
        announcement.read = True
        announcement.save()
        return redirect("teacher_dashboard")


@login_required
@teacher_required
def create_event_PDF(request):
    buff = BytesIO()
    doc = SimpleDocTemplate(buff, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm,
                            title="Export Events")
    styles = getSampleStyleSheet()
    elements = []

    events = Event.objects.filter(Q(teacher=request.user))
    dates = []

    datetime_objects = events.order_by('start').values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in dates:
            dates.append(timezone.localtime(datetime_object).date())

    events_dct = {}
    for date in dates:
        events_dct[str(date)] = events.filter(start__date=date)

    date_style = ParagraphStyle('date_style',
                                fontName="Helvetica-Bold",
                                fontSize=14,
                                spaceBefore=7,
                                spaceAfter=3
                                )

    for date in dates:
        elements.append(Paragraph(str(date.strftime("%d.%m.%Y")), date_style))
        elements.append(Spacer(0, 5))

        events_per_date = events.filter(Q(start__date=date))
        for event_per_date in events_per_date:
            t = str(timezone.localtime(
                event_per_date.start).time().strftime("%H:%M"))
            s = ""
            if len(event_per_date.student.all()) == 0:
                s = "/"
            else:
                for student in event_per_date.student.all():
                    s += "{} {}; ".format(student.first_name,
                                          student.last_name)
                s = s[:-2]

            elements.append(Paragraph(f"{t}  |  {s}", styles["Normal"]))
            elements.append(Spacer(0, 5))

    def header_and_footer(canvas, doc):
        header_footer_style = ParagraphStyle('header_footer_stlye',
                                             alignment=TA_CENTER,
                                             )
        header_content = Paragraph(str(datetime.datetime.now().strftime(
            "%Y-%m-%d_%H:%M:%S")) + "_" + str(request.user.last_name),  header_footer_style)
        footer_content = Paragraph(
            "Alle Angaben ohne Gewähr<br /><br />-{}-".format(canvas.getPageNumber()),  header_footer_style)

        canvas.saveState()

        header_content.wrap(doc.width,  doc.topMargin)
        header_content.drawOn(
            canvas, doc.leftMargin,  doc.height + doc.bottomMargin + doc.topMargin - 1*cm)

        footer_content.wrap(doc.width,  doc.bottomMargin)
        footer_content.drawOn(canvas, doc.leftMargin,  1*cm)

        canvas.restoreState()

    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height,  id='normal')

    template = PageTemplate(id='test', frames=frame,
                            onPage=partial(header_and_footer))

    doc.addPageTemplates([template])
    doc.build(elements)
    buff.seek(0)
    return FileResponse(buff, as_attachment=False, filename=f'events_{datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.pdf')


@method_decorator(teacher_decorators, name='dispatch')
class EventDetailView(View):
    cancel_form = cancelEventForm

    def get(self, request, event_id):
        try:
            event = Event.objects.get(Q(id=event_id), Q(teacher=request.user))
        except Event.DoesNotExist:
            raise Http404("Der Termin konnte nicht gefunden werden")
        else:
            cancel_form = self.cancel_form
            return render(request, "teacher/event/detailEvent.html", context={"cancel_event": cancel_form, "event": event})

    def post(self, request, event_id):
        try:
            event = Event.objects.get(Q(id=event_id), Q(teacher=request.user))
        except Event.DoesNotExist:
            raise Http404("Der Termin konnte nicht gefunden werden")
        else:
            if 'cancel_event' in request.POST:
                cancel_form = self.cancel_form(request.POST)
                if cancel_form.is_valid():
                    message = cancel_form.cleaned_data["message"]
                    book_other = cancel_form.cleaned_data["book_other_event"]

                    if book_other:
                        teacher_id = urlsafe_base64_encode(
                            force_bytes(event.teacher.id))
                        Announcements.objects.create(
                            announcement_type=1,
                            user=event.parent, message='%s %s hat Ihren Termin abgesagt und folgende Nachricht für Sie hinterlassen: %s \nUnter dem angegebenen Link buchen Sie bitte einen neuen Termin' % (
                                event.teacher.first_name, event.teacher.last_name, message),
                            action_name="Termine ansehen",
                            action_link=reverse(
                                "event_teacher_list", args=[teacher_id])
                        )
                    else:
                        Announcements.objects.create(
                            announcement_type=1,
                            user=event.parent, message='%s %s hat Ihren Termin abgesagt und folgende Nachricht für Sie hinterlassen: %s' % (
                                event.teacher.first_name, event.teacher.last_name, message),
                        )

                    event.parent = None
                    event.status = 0
                    event.occupied = False
                    event.student.clear()
                    event.save()
                    return redirect("teacher_dashboard")
            cancel_form = self.cancel_form
            return render(request, "teacher/event/detailEvent.html", context={"cancel_event": cancel_form, "event": event})


@method_decorator(teacher_decorators, name='dispatch')
class EventListView(View):
    def get(self, request):
        events = Event.objects.filter(
            Q(teacher=request.user), Q(occupied=True))
        dates = []

        datetime_objects = events.order_by('start').values_list("start", flat=True)
        for datetime_object in datetime_objects:
            if timezone.localtime(datetime_object).date() not in [date.date() for date in dates]:
                # print(datetime_object.astimezone(pytz.UTC).date())
                dates.append(datetime_object.astimezone(pytz.UTC))

        events_dict = {}
        for date in dates:
            #! Spontane Änderung aufgrund von Problemen auf dem Server
            events_dict[str(date.date())] = events.filter(
                Q(start__gte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("00:00:00", "%H:%M:%S").time()
                )),
                Q(start__lte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("23:59:59", "%H:%M:%S").time()
                ))).order_by('start')
