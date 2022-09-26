import functools
from django.shortcuts import redirect, render, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from dashboard.models import SiteSettings, Inquiry, Event
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def teacher_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role == 1 or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponse({'error': 'Unauthorized'}, status=401)

    return wrapper
