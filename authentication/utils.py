from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import CustomUser, Upcomming_User
from django.db.models import Q

from .tokens import teacher_registration_token, parent_registration_token

import os
from django.utils import timezone
from django.template.loader import render_to_string

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

        subject = "Teacher Registration"
        email_template_name = (
            "authentication/teacher_registration/teacher_registration_email.txt"
        )
        c = {
            "email": new_teacher.email,
            "uid": urlsafe_base64_encode(force_bytes(new_teacher.pk)),
            "user": new_teacher,
            "token": teacher_registration_token.make_token(new_teacher),
            "current_site": os.environ.get("PUBLIC_URL"),
        }
        email = render_to_string(email_template_name, c)
        # email_html = render_to_string(
        #     "authentication/password-reset/password_reset_email_html.html", c)
        # send_mail(subject, email, 'admin@example.com',
        #           [user.email], fail_silently=False)
        # async_send_mail.delay(
        #     subject, email, user.email, email_html_body=email_html)
        async_send_mail.delay(subject, email, new_teacher.email)
    else:
        raise "Nutzer existiert bereits"


def parent_registration_check_otp_verified(user_data: Upcomming_User) -> bool:
    if user_data.otp_verified_date + timezone.timedelta(hours=3) > timezone.now():
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
        subject = "Teacher Registration"
        email_template_name = (
            "authentication/email/registration_email/parent_registration_email.txt"
        )
        token = parent_registration_token.make_token(up_user)
        c = {
            "email": up_user.parent_email,
            "up_user": up_user,
            "token": token,
            "current_site": os.environ.get("PUBLIC_URL"),
        }
        print(
            token,
            parent_registration_token.check_token(up_user, token),
            up_user.parent_email,
        )
        email = render_to_string(email_template_name, c)
        # email_html = render_to_string(
        #     "authentication/password-reset/password_reset_email_html.html", c)
        # send_mail(subject, email, 'admin@example.com',
        #           [user.email], fail_silently=False)
        # async_send_mail.delay(
        #     subject, email, user.email, email_html_body=email_html)
        async_send_mail.delay(subject, email, up_user.parent_email)
