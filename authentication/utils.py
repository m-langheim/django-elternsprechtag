from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import CustomUser, Upcomming_User
from django.db.models import Q

from .tokens import teacher_registration_token, parent_registration_token

import os
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse

import datetime

from .tasks import async_send_mail


def register_new_teacher(email: str):
    if not CustomUser.objects.filter(
        Q(email=email), Q(role=1), Q(is_active=True)
    ).exists():
        if not CustomUser.objects.filter(email=email).exists():
            new_teacher = CustomUser(
                role=1, is_staff=True, is_active=False, email=email
            )
        elif not CustomUser.objects.filter(Q(email=email), Q(role=1)).exists():
            raise "Dieser Email wird bereits von einem nicht Lehrer genutzt."
        elif CustomUser.objects.filter(Q(email=email), Q(role=1), Q(is_active=False)):
            new_teacher = CustomUser.objects.get(email=email)
        else:
            raise "Es ist ein Fehler bei der Erstellung des Lehrer Accounts aufgetretetn."
        new_teacher.set_unusable_password()  # Hier wird ein nicht benutzbares Passwort festgelegt
        new_teacher.save()

        email_subject = "Teacher registration"
        email_str_body = render_to_string(
            "authentication/email/register_teacher/register_teacher_email.txt",
            {
                "user": new_teacher,
                "url": str(os.environ.get("PUBLIC_URL")) + reverse("teacher_new_registartion_view", kwargs={"uidb64": urlsafe_base64_encode(force_bytes(new_teacher.pk)), "token": teacher_registration_token.make_token(new_teacher)}),
            },
        )
        email_html_body = render_to_string(
            "authentication/email/register_teacher/register_teacher_email.html",
            {
                "user": new_teacher,
                "current_site": os.environ.get("PUBLIC_URL"),
                "uid": urlsafe_base64_encode(force_bytes(new_teacher.pk)),
                "token": teacher_registration_token.make_token(new_teacher),
                "date": datetime.datetime.now().strftime("%d.%m.%Y"),
            },
        )

        async_send_mail.delay(
            email_subject,
            email_str_body,
            new_teacher.email,
            email_html_body=email_html_body,
        )
    else:
        raise "Nutzer existiert bereits"


def parent_registration_check_otp_verified(user_data: Upcomming_User) -> bool:
    if (
        user_data.otp_verified_date + timezone.timedelta(hours=3) > timezone.now()
        and user_data.otp_verified
    ):
        return True
    else:
        user_data.otp_verified = False
        user_data.save()
        return False


def parent_registration_link_deprecated(user_data: Upcomming_User) -> bool:
    if user_data.created + timezone.timedelta(days=30) < timezone.now():
        student = user_data.student
        user_data.delete()
        Upcomming_User.objects.create(student=student)
        return True
    return False


def string_shortener(string: str, total_length=21) -> str:
    if len(string) >= total_length:
        string = string[: total_length - 3]
        string = string + "..."
    return string


def send_parent_registration_mail(up_user: Upcomming_User):
    if not up_user.parent_registration_email_send and up_user.parent_email:
            email_subject = "Continue registration for the parent consultation day"
            email_str_body = render_to_string(
                "authentication/email/register_parent/register_parent_parent_email.txt",
                {
                    "user": up_user, #ggf kann man das nicht so machen
                    "email": up_user.parent_email,
                    "url": str(os.environ.get("PUBLIC_URL")) + reverse("parent_create_account", kwargs={"user_token": up_user.user_token, "key_token": up_user.access_key, "token": parent_registration_token.make_token(up_user)}),
                }
            )
            email_html_body = render_to_string(
                "authentication/email/register_parent/register_parent_parent_email.html",
                {
                    "user": up_user, #ggf kann man das nicht so machen
                    "email": up_user.parent_email,
                    "url": str(os.environ.get("PUBLIC_URL")) + reverse("parent_create_account", kwargs={"user_token": up_user.user_token, "key_token": up_user.access_key, "token": parent_registration_token.make_token(up_user)}),
                    "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                },
            )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                up_user.parent_email,
                email_html_body=email_html_body,
            )
