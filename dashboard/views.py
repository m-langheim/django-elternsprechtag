from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student
from .models import Event, TeacherStudentInquiry, SiteSettings
from django.db.models import Q
from django.utils import timezone

from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from .forms import BookForm, InquiryForm
from .decorators import lead_started
from django.contrib import messages
from django.http import Http404

# Create your views here.


@login_required
def public_dashboard(request):
    students = request.user.students.all()
    inquiries = []
    for inquiry in TeacherStudentInquiry.objects.filter(Q(parent=request.user), Q(event=None)):
        inquiry_id = urlsafe_base64_encode(force_bytes(inquiry.id))
        inquiries.append({'teacher': inquiry.teacher, 'student': inquiry.student,
                         'inquiry_link': reverse('inquiry_detail_view', args=[inquiry_id])})
    return render(request, 'dashboard/public_dashboard.html', {'events': Event.objects.filter(parent=request.user), 'inquiries': inquiries})


@login_required
def search(request):
    teachers = CustomUser.objects.filter(role=1)
    teacherExtraData = TeacherExtraData.objects.all()
    request_search = request.GET.get('q', None)
    state = 0
    if request_search is None:
        state = 0
    elif request_search.startswith('#'):
        request_search = request_search[1:]
        extraData = teacherExtraData.filter(tags__icontains=request_search)
        result = []
        for data in extraData:
            teacher = data.teacher
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


@login_required
# man erhält eine Liste mit allen freien Terminen des Lehrers
def bookEventTeacherList(request, teacher_id):

    try:
        teacher = CustomUser.objects.filter(role=1).get(id=force_str(
            urlsafe_base64_decode(teacher_id)))  # get the teacher for the id
    except CustomUser.DoesNotExist:
        print("error")
    except CustomUser.MultipleObjectsReturned:
        print("Error")
    else:
        print(teacher)
        print(Event.objects.filter(teacher=teacher))
        events = []
        for event in Event.objects.filter(teacher=teacher).filter(occupied=False):
            events.append({'event': event, 'url': reverse(
                'event_per_id', args=[event.id])})

        print(events)
    return render(request, 'dashboard/events/teacher.html', {'teacher': teacher, 'events': events})


@login_required
@lead_started
def bookEvent(request, event_id):  # hier werden final die Termine dann gebucht
    try:
        event = Event.objects.get(id=event_id)
    except Event.MultipleObjectsReturned:
        print("error")
    except Event.DoesNotExist:
        return Http404("This event was not found")
    else:
        if event.occupied:
            return render(request, "dashboard/events/occupied.html")
        if request.method == 'POST':
            form = BookForm(request.POST, request=request,
                            teacher=event.teacher)
            if form.is_valid():
                # #! Aktuell ist nur eine Lehreranfrage pro Schüler möglich
                # inquiries = TeacherStudentInquiry.objects.filter(
                #     Q(parent=request.user), Q(teacher=event.teacher))

                # if inquiries:
                students = []
                for student in form.cleaned_data['student']:
                    try:
                        model_student = Student.objects.get(
                            shield_id=student)
                    except Student.DoesNotExist:
                        Http404("Error")
                    else:
                        students.append(model_student)
                # ? validation of students needed or given through the form
                event.parent = request.user
                event.student.set(students)
                event.occupied = True
                event.save()
                messages.success(request, "Gebucht")
                return redirect('home')
                #     students_valid = True
                #     students = []
                #     for inquiry in inquiries:
                #         students.append(inquiry.student)

                #     students_valid = True
                #     if SiteSettings.objects.all().first().lead_start > timezone.now().date():
                #         for data_student in form.cleaned_data['student']:
                #             if not data_student in students:
                #                 students_valid = False
                #         if not students_valid:
                #             messages.warning(
                #                 request, "Die allgemeine Buchung hat noch nicht begonnen, Sie können nur angefragte Schüler wählen")
                #     if students_valid:
                #         event.parent = request.user
                #         event.student.set(form.cleaned_data['student'])
                #         event.occupied = True
                #         event.save()
                #         for inquiry in inquiries:
                #             if inquiry.student in form.cleaned_data['student']:
                #                 inquiry.event = event
                #                 inquiry.save()
                #         messages.success(request, "Gebucht")
                #         return redirect('home')
                # else:
                #     event.parent = request.user
                #     event.student.set(form.cleaned_data['student'])
                #     event.occupied = True
                #     event.save()
                #     messages.success(request, "Gebucht")
                #     return redirect('home')
                # try:
                #     inquiry = TeacherStudentInquiry.objects.get(
                #         Q(parent=request.user), Q(teacher=event.teacher))
                # except TeacherStudentInquiry.DoesNotExist:  # Es ist keine Anfrage eines Lehrers verfügbar

                # else:
                #     if inquiry.student in form.cleaned_data['student']:
                #         if SiteSettings.objects.all().first().lead_start > timezone.now().date() and form.cleaned_data['student'].length > 1:
                #             messages.warning(
                #                 request, "Die allgemeine Buchung hat noch nicht begonnen, Sie können nur angefragte Schüler wählen")
                #         else:
                #             event.parent = request.user
                #             event.student.set(form.cleaned_data['student'])
                #             event.occupied = True
                #             event.save()
                #             inquiry.event = event
                #             inquiry.save()
                #             messages.success(request, "Gebucht")
                #             return redirect('home')
                #     else:
                #         messages.warning(
                #             request, "You have to select the inquiry student")
                #         form = BookForm(request=request, teacher=event.teacher)
        else:
            form = BookForm(request=request, teacher=event.teacher)
        return render(request, 'dashboard/events/book.html', {'event_id': event_id, 'book_form': form})


@login_required
def inquiryView(request, inquiry_id):
    try:
        inquiry = TeacherStudentInquiry.objects.get(
            id=force_str(urlsafe_base64_decode(inquiry_id)))
    except TeacherStudentInquiry.DoesNotExist:
        return Http404("Inquiry does not exist.")

    else:
        if inquiry.event != None:
            return render(request, "dashboard/error/inquiry_ocupied.html")
        elif request.method == 'POST':
            form = InquiryForm(request.POST,
                               request=request, selected_student=inquiry.student, teacher=inquiry.teacher, parent=inquiry.parent)
            if form.is_valid():
                event = form.cleaned_data['event']
                event.parent = inquiry.parent
                students = []
                for student in form.cleaned_data['student']:
                    try:
                        model_student = Student.objects.get(shield_id=student)
                    except Student.DoesNotExist:
                        Http404("Error")
                    else:
                        students.append(model_student)
                event.student.set(students)
                event.occupied = True
                event.save()
                messages.success(request, "Gebucht")
                return redirect('home')
        else:
            form = InquiryForm(
                request=request, selected_student=inquiry.student, teacher=inquiry.teacher, parent=inquiry.parent)
        return render(request, "dashboard/inquiry.html", {'reason': inquiry.reason, 'form': form})
