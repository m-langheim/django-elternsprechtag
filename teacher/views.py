from django.shortcuts import render, redirect
from dashboard.models import TeacherStudentInquiry, Student, Event
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.http import Http404
from .decorators import teacher_required
from .forms import createInquiryForm, editInquiryForm

# Create your views here.

from django.urls import reverse
from django.contrib import messages


@login_required
@teacher_required
def dashboard(request):
    inquiries = TeacherStudentInquiry.objects.filter(teacher=request.user)
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
            Q(first_name__icontains=search) | Q(last_name__icontains=search)).order_by('shield_id')
    paginator = Paginator(students, 25)
    page_obj = paginator.get_page(page_number)
    print(page_obj)
    return render(request, "teacher/studentList.html", {'page_obj': page_obj})


class DetailStudent(View):
    def get(self, request):
        return render(request, "teacher/student.html")


class InquiryView(View):
    form_class = editInquiryForm

    def get(self, request, id):
        try:
            inquiry = TeacherStudentInquiry.objects.get(id__exact=force_str(
                urlsafe_base64_decode(id)))
        except TeacherStudentInquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            print(inquiry.parent)
            initial = {'reason': inquiry.reason,
                       'student': inquiry.student,
                       'parent': inquiry.parent,
                       'event': inquiry.event}
            form = self.form_class(initial=initial)
            print(inquiry)
            return render(request, "teacher/inquiry.html", {'form': form})

    def post(self, request, id):
        try:
            inquiry = TeacherStudentInquiry.objects.get(id__exact=force_str(
                urlsafe_base64_decode(id)))
        except TeacherStudentInquiry.DoesNotExist:
            Http404("Inquiry wurde nicht gefunden")
        else:
            initial = {'reason': inquiry.reason,
                       'student': inquiry.student,
                       'parent': inquiry.parent,
                       'event': inquiry.event}
            form = self.form_class(request.POST, initial=initial)
            print(request.POST)
            if form.is_valid():
                inquiry.reason = form.cleaned_data['reason']
                inquiry.save()
                messages.success(request, "Änderungen angenommen")
                return redirect('teacher_dashboard')
            return render(request, "teacher/inquiry.html", {'form': form})


class CreateInquiryView(View):
    def get(self, request, id):
        form = createInquiryForm(request=request)
        return render(request, "teacher/createInquiry.html", {'form': form})
