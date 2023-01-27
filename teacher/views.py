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
# Create your views here.

from django.urls import reverse
from django.contrib import messages


teacher_decorators = [login_required, teacher_required]


@login_required
@teacher_required
def dashboard(request):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(requester=request.user))
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append({'inquiry': inquiry, 'url': reverse(
            'teacher_show_inquiry', args=[urlsafe_base64_encode(force_bytes(inquiry.id))])})

    # Hier werden alle events anhand ihres Datums aufgeteilt
    events = Event.objects.filter(Q(teacher=request.user), Q(occupied=True))
    dates = []

    datetime_objects = events.values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if datetime_object.date() not in dates:
            dates.append(datetime_object.date())

    events_dict = {}
    for date in dates:
        events_dict[str(date)] = events.filter(start__date=date)

    announcements = Announcements.objects.filter(
        Q(user=request.user), Q(read=False))

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
            return Http404("Student not found")
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
        return render(request, "teacher/createInquiry.html", {'form': form, "student": student})

    def post(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            return Http404("Student not found")
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


@method_decorator(teacher_decorators, name='dispatch')
class ProfilePage(View):
    def get(self, request):
        tagConfigurationForm = configureTagsForm(
            initial={'tags': request.user.teacherextradata.tags.all()})
        # print(TeacherExtraData.objects.all().first().image.url)

        context = {
            'tags': request.user.teacherextradata.tags.all(),
            'configure_tags': tagConfigurationForm,
            'change_profile': changeProfileForm(instance=request.user),
            'change_password': changePasswordForm(request.user)
        }
        return render(request, "teacher/profile.html", context)

    def post(self, request):
        user: CustomUser = request.user
        # change the users personal information
        if 'change_profile' in request.POST:
            change_profile_form = changeProfileForm(
                request.POST, request.FILES, instance=user)
            if change_profile_form.is_valid():
                change_profile_form.save()
            return render(request, "teacher/profile.html", {'tags': user.teacherextradata.tags.all(), 'configure_tags': configureTagsForm(
                initial={'tags': user.teacherextradata.tags.all()}), 'change_profile': change_profile_form, 'change_password': changePasswordForm(user)})

        # change the users pasword
        if 'change_password' in request.POST:
            change_password_form = changePasswordForm(
                user, request.POST)
            if change_password_form.is_valid():
                user = change_password_form.save()
                update_session_auth_hash(request, user)

            return render(request, "teacher/profile.html", {'tags': user.teacherextradata.tags.all(), 'configure_tags': configureTagsForm(
                initial={'tags': user.teacherextradata.tags.all()}), 'change_profile': changeProfileForm(instance=user), 'change_password': change_password_form})

        if 'confiure_tags' in request.POST:
            tagConfigurationForm = configureTagsForm(request.POST)
            if tagConfigurationForm.is_valid():
                extraData = user.teacherextradata
                extraData.tags.set(tagConfigurationForm.cleaned_data["tags"])
                extraData.save()

            context = {
                'tags': user.teacherextradata.tags.all(),
                'configure_tags': tagConfigurationForm,
                'change_profile': changeProfileForm(instance=user),
                'change_password': changePasswordForm(user)
            }
            return render(request, "teacher/profile.html", context)
        raise BadRequest


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
        return Http404("Mitteilung nicht gefunden")
    else:
        announcement.read = True
        announcement.save()
        return redirect("teacher_dashboard")


class EventDetailView(View):
    cancel_form = cancelEventForm

    def get(self, request, event_id):
        try:
            event = Event.objects.get(Q(id=event_id), Q(teacher=request.user))
        except Event.DoesNotExist:
            return Http404("Der Termin konnte nicht gefunden werden")
        else:
            cancel_form = self.cancel_form
            return render(request, "teacher/event/detailEvent.html", context={"cancel_event": cancel_form, "event": event})

    def post(self, request, event_id):
        try:
            event = Event.objects.get(Q(id=event_id), Q(teacher=request.user))
        except Event.DoesNotExist:
            return Http404("Der Termin konnte nicht gefunden werden")
        else:
            if 'cancel_event' in request.POST:
                cancel_form = self.cancel_form(request.POST)
                if cancel_form.is_valid():
                    message = cancel_form.cleaned_data["message"]
                    book_other = cancel_form.cleaned_data["book_other_event"]
                    teacher_id = urlsafe_base64_encode(
                        force_bytes(event.teacher.id))
                    if book_other:
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
                    #! Es muss noch die Liste an Schüler:innen wieder geleert werden
                    event.status = 0
                    event.occupied = False
                    event.save()
                    return redirect("teacher_dashboard")
            cancel_form = self.cancel_form
            return render(request, "teacher/event/detailEvent.html", context={"cancel_event": cancel_form, "event": event})


class EventListView(View):
    def get(self, request):
        events = Event.objects.filter(
            Q(teacher=request.user), Q(occupied=True))
        dates = []

        datetime_objects = events.values_list("start", flat=True)
        for datetime_object in datetime_objects:
            if datetime_object.date() not in dates:
                dates.append(datetime_object.date())

        events_dict = {}
        for date in dates:
            events_dict[str(date)] = events.filter(start__date=date)
