import functools
from django.shortcuts import redirect, render, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import CustomUser, Upcomming_User
from .utils import (
    parent_registration_link_deprecated,
    parent_registration_check_otp_verified,
)
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def valid_custom_user_link(view_func):
    @functools.wraps(view_func)
    def wrapper(request, user_token, key_token, *args, **kwargs):
        try:
            up_user = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            up_user = None

        if up_user is not None and not parent_registration_link_deprecated(up_user):
            return view_func(request, user_token, key_token, *args, **kwargs)

    return wrapper


def upcomming_user_otp_validated(view_func):
    @functools.wraps(view_func)
    def wrapper(request, user_token, key_token, *args, **kwargs):
        try:
            up_user = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            up_user = None

        if parent_registration_check_otp_verified(up_user):
            return view_func(request, user_token, key_token, *args, **kwargs)
        else:
            return redirect(
                "parent_check_otp",
                user_token=user_token,
                key_token=key_token,
            )

    return wrapper
