from django.core.mail import send_mail
from celery import shared_task
from django.conf import settings


@shared_task
def async_send_mail(email_subject, email_body, email_receiver):
    send_mail(email_subject, email_body,
              settings.EMAIL_COMPLETE, [email_receiver, ])
