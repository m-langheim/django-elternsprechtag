from django.shortcuts import render, redirect
from authentication.models import StudentChange, CustomUser, Upcomming_User
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

import datetime

from .forms import *
from .tasks import *
from .tables import *
from django_tables2 import SingleTableView
from general_tasks.tasks import async_send_mail

from dashboard.models import Event, EventChangeFormula
from dashboard.tasks import async_create_events_special

import csv, io, os

from django.utils.decorators import method_decorator


def reset_student_parent_relationship(student: Student):
    try:
        parent = CustomUser.objects.get(Q(role=0), Q(students=student))
    except:
        raise Exception("Es wurde kein passendes Elternteil gefunden.")
    else:
        parent.students.remove(student)
        parent.save()

        #! Das löschen alter Elternteile funktioniert für den Reset bisher leider nicht
        # if not parent.students.all().exists():
        #     parent.delete()

        up_user, created = Upcomming_User.objects.get_or_create(student=student)
        if (
            not created
            and up_user.created + timezone.timedelta(days=15) > timezone.now()
        ):
            up_user.delete()
            up_user = Upcomming_User.objects.create(student=student)
        up_user.save()

        return "Success"


def student_send_registration_mail(student: Student):
    up_user, created = Upcomming_User.objects.get_or_create(student=student)

    if not created and (
        up_user.created + timezone.timedelta(days=15) < timezone.now()
        or up_user.email_send
    ):
        up_user.delete()

        up_user = Upcomming_User.objects.create(student=student)
        up_user.save()

    email_subject = "Registration link for the parent consultation day"
    email_str_body = render_to_string(
        "authentication/email/register_parent/register_parent_child_email.txt",
        {
            "user": up_user,  # ggf kann man das nicht so machen
            "otp": up_user.otp,
            "url": str(os.environ.get("PUBLIC_URL"))
            + "/register/"
            + str(up_user.user_token)
            + "/"
            + str(up_user.access_key)
            + "/",
        },
    )
    email_html_body = render_to_string(
        "authentication/email/register_parent/register_parent_child_email.html",
        {
            "user": up_user,  # ggf kann man das nicht so machen
            "otp": up_user.otp,
            "url": str(os.environ.get("PUBLIC_URL"))
            + "/register/"
            + str(up_user.user_token)
            + "/"
            + str(up_user.access_key)
            + "/",
            "template_text_bottom": "Use the following One-Time-Password when signing up: <strong>"
            + up_user.otp
            + "</strong>.",
            "date": datetime.datetime.now().strftime("%d.%m.%Y"),
        },
    )  #!Hier habe ich ein wenig gefuscht; dies wird gerade nicht genutzt!

    # async_send_mail.delay(
    #     email_subject,
    #     email_str_body,
    #     up_user.student.child_email,
    #     email_html_body=email_html_body,
    # )

    async_send_mail.delay(
        email_subject,
        email_str_body,
        up_user.student.child_email,
    )  #! Hier wird keine HTML versandt
    up_user.email_send = True
    up_user.save()
