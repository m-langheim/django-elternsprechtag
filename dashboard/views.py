from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student, Tag
from .models import Event, Inquiry, SiteSettings, Announcements
from django.db.models import Q
from django.utils import timezone
from django.views import View
from django.utils.decorators import method_decorator

from django.shortcuts import get_object_or_404
from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from .forms import BookForm, cancelEventForm, EditEventForm
from .decorators import lead_started, parent_required
from django.contrib import messages
from django.http import Http404

from .utils import check_inquiry_reopen

# Create your views here.

parent_decorators = [login_required, parent_required]


@login_required
@parent_required
def public_dashboard(request):

    inquiries = Inquiry.objects.filter(Q(type=0), Q(respondent=request.user))
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append({'inquiry': inquiry, 'url': reverse(
            'inquiry_detail_view', args=[urlsafe_base64_encode(force_bytes(inquiry.id))])})

    # Hier werden alle events anhand ihres Datums aufgeteilt
    events = Event.objects.filter(Q(parent=request.user), Q(occupied=True))
    dates = []

    datetime_objects = events.values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in dates:
            dates.append(timezone.localtime(datetime_object).date())

    events_dict = {}
    for date in dates:
        events_dict[str(date)] = events.filter(start__date=date)

    announcements = Announcements.objects.filter(
        Q(user=request.user), Q(read=False))

    return render(request, 'dashboard/public_dashboard.html', {'inquiries': custom_inquiries, "events_dict": events_dict, 'events': events, "announcements": announcements})


@ login_required
@ parent_required
def search(request):
    teachers = CustomUser.objects.filter(role=1)
    teacherExtraData = TeacherExtraData.objects.all()
    request_search = request.GET.get('q', None)
    state = 0
    if request_search is None:
        state = 0
    elif request_search.startswith('#'):
        request_search = request_search[1:]
        tags = Tag.objects.filter(Q(name__icontains=request_search) | Q(
            synonyms__icontains=request_search))  # get a list of all matching tags

        result = []
        for tag in tags:
            extraData = teacherExtraData.filter(tags=tag)

            for data in extraData:
                teacher = data.teacher
                if not teacher in result:
                    result.append(teacher)
        state = 1
    else:
        result = []
        for data in teachers.filter(last_name__icontains=request_search):
            if not data in result:
                result.append(data)
        # result = teachers.filter(last_name__icontains=request_search)
        for data in teacherExtraData.filter(acronym__icontains=request_search):
            if not data.teacher in result:
                result.append(data.teacher)
        state = 2

    custom_result = []

    for teacher in result:
        teacher_id = urlsafe_base64_encode(force_bytes(teacher.id))
        custom_result.append({'first_name': teacher.first_name,
                             'last_name': teacher.last_name, 'email': teacher.email, 'url': reverse('event_teacher_list', args=[teacher_id])})  # notwendig um den Url parameter zu dem queryset hinzu zu fügen
    # return render(request, 'dashboard/search.html', {'teachers': result, 'search': request_search})
    return render(request, 'dashboard/search.html', {'teachers': custom_result, 'state': state, 'request_search': request_search})


@ login_required
@ parent_required
# man erhält eine Liste mit allen freien Terminen des Lehrers
def bookEventTeacherList(request, teacher_id):

    try:
        teacher = CustomUser.objects.filter(role=1).get(id__exact=force_str(
            urlsafe_base64_decode(teacher_id)))  # get the teacher for the id
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

        personal_booked_events = events.filter(
            Q(occupied=True), Q(parent=request.user))

        events_dt = Event.objects.filter(Q(teacher=teacher))
        
        dates = []
        datetime_objects = events_dt.values_list("start", flat=True)
        for datetime_object in datetime_objects:
            if datetime_object.date() not in dates:
                dates.append(datetime_object.date())

        events_dt_dict = {}
        for date in dates:
            events_dt_dict[str(date)] = Event.objects.filter(
                Q(teacher=teacher), Q(start__date=date)).order_by('start')

        tags = TeacherExtraData.objects.get(
            teacher=teacher).tags.all().order_by('name')

        image = TeacherExtraData.objects.filter(
            Q(teacher=teacher))[0].image.url

        booked_times = []
        for event in Event.objects.filter(Q(parent=request.user), Q(occupied=True)).values_list("start", flat=True):
            time = timezone.localtime(event)
            booked_times.append(time)

    return render(request, 'dashboard/events/teacher.html', {'teacher': teacher, 'events': events, 'personal_booked_events': personal_booked_events, 'events_dt': events_dt, 'events_dt_dict': events_dt_dict, 'tags': tags, 'image': image, 'booked_times': booked_times})


@method_decorator(parent_required, name='dispatch')
# hier werden final die Termine dann gebucht
class bookEventView(View):
    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)

        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")

        # Ab hier verändert, um Anfragen zu zu lassen
        inquiry_id_get = request.GET.get('inquiry')
        if inquiry_id_get:
            try:
                inquiry = Inquiry.objects.get(Q(respondent=request.user), Q(id=force_str(
                    urlsafe_base64_decode(inquiry_id_get))), Q(type=0))
            except Inquiry.DoesNotExist:
                # Es ist ein Fehler passiert, deswegen wird die "standard" Variante ausgeführt
                messages.error(
                    request, "Die angegebene Anfrage konnte leider nicht gefunden werden.")
                form = BookForm(request=request, teacher=event.teacher)
                teacher_id = urlsafe_base64_encode(
                    force_bytes(event.teacher.id))
                back_url = reverse('event_teacher_list', args=[teacher_id])
            else:
                form = BookForm(request=request, teacher=event.teacher, initial={
                                'student': [student.id for student in inquiry.students.all()]})
                back_url = reverse('inquiry_detail_view',
                                   args=[inquiry_id_get])
        else:
            # Das event wurde nicht über eine Anfrage aufgerufen
            form = BookForm(request=request, teacher=event.teacher)
            teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
            back_url = reverse('event_teacher_list', args=[teacher_id])

        booked_times = []
        for b_times in Event.objects.filter(Q(parent=request.user), Q(occupied=True)).values_list("start", flat=True):
            time = timezone.localtime(b_times)
            booked_times.append(time)

        return render(request, 'dashboard/events/book.html', {'event': event, 'book_form': form, 'back_url': back_url, 'booked_times': booked_times})

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
        form = BookForm(request.POST, request=request,
                        teacher=event.teacher)
        if form.is_valid():
            students = []
            for student in form.cleaned_data['student']:
                try:
                    model_student = Student.objects.get(
                        id=student)
                except Student.DoesNotExist:
                    raise Http404("Error")
                else:
                    students.append(model_student)
            # ? validation of students needed or given through the form
            inquiry = Inquiry.objects.create(
                type=1, event=event, requester=request.user, respondent=event.teacher, reason="")
            inquiry.students.set(students)
            inquiry.save()
            event.parent = request.user
            event.status = 2
            event.student.set(students)
            event.occupied = True
            event.save()
            messages.success(request, "Angefragt")
            return redirect('event_per_id', event_id=event.id)

        teacher_id = urlsafe_base64_encode(force_bytes(event.teacher.id))
        url = reverse('event_teacher_list', args=[teacher_id])

        booked_times = []
        for b_times in Event.objects.filter(Q(parent=request.user), Q(occupied=True)).values_list("start", flat=True):
            time = timezone.localtime(b_times)
            booked_times.append(time)

        return render(request, 'dashboard/events/book.html', {'event': event, 'book_form': form, 'teacher_url': url, 'booked_times': booked_times})


# Der Inquiry View wurde einmal neu gemacht, muss jetzt noch weiter so ergänzt werden, damit er schön aussieht
@method_decorator(parent_required, name='dispatch')
class InquiryView(View):
    def get(self, request, inquiry_id):
        inquiry = get_object_or_404(Inquiry.objects.filter(Q(requester=request.user) | Q(respondent=request.user)), type=0, id=force_str(
            urlsafe_base64_decode(inquiry_id)))

        teacher_id = urlsafe_base64_encode(force_bytes(inquiry.requester.id))

        if inquiry.processed:  # Die Anfrage wurde bereits bearbeitet
            return render(request, "dashboard/inquiry_answered.html", {'inquiry_id': inquiry_id, 'inquiry': inquiry, 'teacher_id': teacher_id})

        # form = InquiryForm(
        #     request=request, selected_student=inquiry.students.first, teacher=inquiry.requester, parent=inquiry.respondent)

        events = Event.objects.filter(Q(teacher=inquiry.requester))

        events_dt = Event.objects.filter(Q(teacher=inquiry.requester))
        dates = []
        datetime_objects = events_dt.values_list("start", flat=True)
        for datetime_object in datetime_objects:
            if timezone.localtime(datetime_object).date() not in dates:
                dates.append(timezone.localtime(datetime_object).date())

        events_dt_dict = {}
        for date in dates:
            events_dt_dict[str(date)] = Event.objects.filter(
                Q(teacher=inquiry.requester), Q(start__date=date)).order_by('start')

        booked_times = []
        for b_times in Event.objects.filter(Q(parent=request.user), Q(occupied=True)).values_list("start", flat=True):
            time = timezone.localtime(b_times)
            booked_times.append(time)

        return render(request, "dashboard/inquiry.html", {'inquiry_id': inquiry_id, 'inquiry': inquiry, 'events': events, 'events_dt': events_dt, 'events_dt_dict': events_dt_dict, 'teacher_id': teacher_id, 'booked_times': booked_times})

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


@method_decorator(parent_required, name='dispatch')
class EventView(View):
    cancel_form = cancelEventForm

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, parent=request.user)
        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")
        edit_form = EditEventForm(
            request=request, teacher=event.teacher, event=event, initial={'student': [student.id for student in event.student.all()]})
        return render(request, "dashboard/events/view.html", {'event': event, 'cancel_form': self.cancel_form, "teacher_id": urlsafe_base64_encode(force_bytes(event.teacher.id)), 'edit_form': edit_form})

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, parent=request.user)
        if event.occupied and event.parent != request.user:
            return render(request, "dashboard/events/occupied.html")

        edit_form = EditEventForm(request=request, teacher=event.teacher, event=event, initial={
                                  'student': [student.id for student in event.student.all()]})
        cancel_form = self.cancel_form()

        # Es wurde die Cancel-Form zurück gegeben
        if 'cancel_event' in request.POST:
            cancel_form = self.cancel_form(request.POST)
            if cancel_form.is_valid():
                message = cancel_form.cleaned_data["message"]

                Announcements.objects.create(
                    announcement_type=1,
                    user=event.teacher,
                    message='%s %s hat einen Termin abgesagt und folgende Nachricht hinterlassen: \n %s' % (
                        request.user.first_name, request.user.last_name, message)
                )
                # Hier wird überprüft, ob es eine Anfrage gab, für die das bearbeitete Event zuständig war
                check_inquiry_reopen(request.user, event.teacher)
                event.parent = None
                event.status = 0
                event.occupied = False
                event.student.clear()
                event.save()
                messages.success(
                    request, "Der Termin wurde erfolgreich abgesagt")
                return redirect("home")

        # Es wurde die Book-Form zurück gegeben
        if 'edit_event' in request.POST:
            edit_form = EditEventForm(
                request.POST, request=request, teacher=event.teacher, event=event)

            if edit_form.is_valid():
                students = []
                for student in edit_form.cleaned_data['student']:
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
        return render(request, "dashboard/events/view.html", {'event': event, 'cancel_form': self.cancel_form,  "teacher_id": urlsafe_base64_encode(force_bytes(event.teacher.id)), 'edit_form': edit_form})


@login_required
@parent_required
def markAnnouncementRead(request, announcement_id):
    announcement = get_object_or_404(Announcements, id__exact=force_str(
        urlsafe_base64_decode(announcement_id)), user=request.user)
    announcement.read = True
    announcement.save()
    return redirect("home")
