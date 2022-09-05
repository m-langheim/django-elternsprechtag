import functools
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import SiteSettings, TeacherStudentInquiry, Event
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def lead_started(view_func):
    @functools.wraps(view_func)
    def wrapper(request, event_id, *args, **kwargs):
        if SiteSettings.objects.all().first().lead_start <= timezone.now().date():
            return view_func(request, event_id, *args, **kwargs)
        elif SiteSettings.objects.all().first().lead_inquiry_start <= timezone.now().date():
            try:
                event = Event.objects.get(id=event_id)
                print(event.teacher)
            except Event.MultipleObjectsReturned:
                print("error")
            except Event.DoesNotExist:
                print("error")
            else:
                inquiries = TeacherStudentInquiry.objects.filter(
                    Q(parent=request.user), Q(teacher=event.teacher))
                if inquiries:
                    if inquiries.filter(event=None):
                        return view_func(request, event_id, *args, **kwargs)
                    else:
                        return render(request, "dashboard/error/inquiry_ocupied.html")
        else:
            messages.error(request, "lead not started")
            print("lead not started")
            return render(request, "dashboard/error/lead_not_started.html", status=401)

    return wrapper
