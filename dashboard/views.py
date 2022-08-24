from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData
from .models import Event

from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from .forms import BookForm
from .decorators import lead_started
from django.contrib import messages

# Create your views here.


@login_required
def public_dashboard(request):
    students = request.user.students.all()
    return render(request, 'dashboard/public_dashboard.html', {'events': Event.objects.filter(parent=request.user)})


@login_required
def search(request):
    teachers = CustomUser.objects.filter(role=1)
    teacherExtraData = TeacherExtraData.objects.all()
    request_search = request.GET.get('q', None)
    if request_search is None:
        print('None')
    elif request_search.startswith('#'):
        request_search = request_search[1:]
        extraData = teacherExtraData.filter(tags__icontains=request_search)
        result = []
        for data in extraData:
            teacher = data.teacher
            result.append(teacher)
    else:
        result = teachers.filter(last_name__icontains=request_search)

    custom_result = []

    for teacher in result:
        teacher_id = urlsafe_base64_encode(force_bytes(teacher.id))
        custom_result.append({'first_name': teacher.first_name,
                             'last_name': teacher.last_name, 'email': teacher.email, 'url': reverse('event_teacher_list', args=[teacher_id])})  # notwendig um den Url parameter zu dem queryset hinzu zu fügen
    # return render(request, 'dashboard/search.html', {'teachers': result, 'search': request_search})
    return render(request, 'dashboard/search.html', {'teachers': custom_result, 'search': request_search})


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
        print("error")
    else:
        if request.method == 'POST':
            form = BookForm(request.POST, request=request)
            if form.is_valid():
                event.parent = request.user
                event.student.set(form.cleaned_data['student'])
                event.occupied = True
                event.save()
                messages.success(request, "Gebucht")
        else:
            form = BookForm(request=request)
        return render(request, 'dashboard/events/book.html', {'event_id': event_id, 'book_form': form})
