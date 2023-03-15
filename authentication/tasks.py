from django.core.mail import send_mail
from celery import shared_task
from django.conf import settings


@shared_task
def async_send_mail(email_subject, email_body, email_receiver, *args, **kwargs):
    if "email_html_body" in kwargs:
        send_mail(email_subject, email_body,
                  settings.EMAIL_COMPLETE, [email_receiver, ], html_message=kwargs.get("email_html_body"))
    else:
        send_mail(email_subject, email_body,
                  settings.EMAIL_COMPLETE, [email_receiver, ])
