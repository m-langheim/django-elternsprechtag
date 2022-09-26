from django.shortcuts import render, redirect
from authentication.models import CustomUser
from dashboard.models import Inquiry, Student, Event
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.http import Http404
from django.utils.decorators import method_decorator
from .decorators import teacher_required
from .forms import createInquiryForm, editInquiryForm

# Create your views here.

from django.urls import reverse
from django.contrib import messages


teacher_decorators = [login_required, teacher_required]


@login_required
@teacher_required
def dashboard(request):
    inquiries = Inquiry.objects.filter(requester=request.user)
    # create individual link for each inquiry
    custom_inquiries = []
    for inquiry in inquiries:
        custom_inquiries.append({'inquiry': inquiry, 'url': reverse(
            'teacher_show_inquiry', args=[urlsafe_base64_encode(force_bytes(inquiry.id))])})
    events = Event.objects.filter(Q(teacher=request.user))
    return render(request, "teacher/dashboard.html", {'inquiries': custom_inquiries, 'events': events})


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
            inquiry = Inquiry.objects.get(id__exact=force_str(
                urlsafe_base64_decode(id)))
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            print(inquiry.respondent)
            initial = {'reason': inquiry.reason,
                       'student': inquiry.student,
                       'parent': inquiry.respondent,
                       'event': inquiry.event}
            form = self.form_class(initial=initial)
            print(inquiry)
            return render(request, "teacher/inquiry.html", {'form': form})

    def post(self, request, id):
        try:
            inquiry = Inquiry.objects.get(id__exact=force_str(
                urlsafe_base64_decode(id)))
        except Inquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            initial = {'reason': inquiry.reason,
                       'student': inquiry.student,
                       'parent': inquiry.respondent,
                       'event': inquiry.event}
            form = self.form_class(request.POST, initial=initial)
            if form.is_valid():
                inquiry.reason = form.cleaned_data['reason']
                inquiry.save()
                messages.success(request, "Änderungen angenommen")
                return redirect('teacher_dashboard')
            return render(request, "teacher/inquiry.html", {'form': form})


@method_decorator(teacher_decorators, name='dispatch')
class CreateInquiryView(View):

    def get(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            return Http404("Student not found")
        else:
            # redirect the user if an inquiry already exists ==> prevent the userr to create a new one
            inquiry = Inquiry.objects.filter(
                Q(student=student), Q(requester=request.user))
            if inquiry:
                messages.info(
                    request, "Sie haben bereits eine Anfrage für dieses Kind erstellt. Im folgenden haben Sie die Möglichkeit diese Anfrage zu bearbeiten.")
                return redirect('teacher_show_inquiry', id=urlsafe_base64_encode(force_bytes(inquiry.first().id)))

            # let the user create a new inquiry
            parent = CustomUser.objects.filter(
                Q(role=0), Q(students=student)).first
            initial = {'student': student, 'parent': parent}
            form = createInquiryForm(initial=initial)
        return render(request, "teacher/createInquiry.html", {'form': form})

    def post(self, request, studentID):
        try:
            student = Student.objects.get(id__exact=studentID)
        except Student.DoesNotExist:
            return Http404("Student not found")
        else:
            # redirect the user if an inquiry already exists ==> prevent the userr to create a new one
            inquiry = Inquiry.objects.filter(
                Q(student=student), Q(requester=request.user))
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
                Inquiry.objects.create(
                    requester=request.user, student=form.cleaned_data["student"], respondent=form.cleaned_data["parent"], reason=form.cleaned_data["reason"])
                messages.success(request, "Anfrage erstellt")
                return redirect('teacher_dashboard')
        return render(request, "teacher/createInquiry.html", {'form': form})
