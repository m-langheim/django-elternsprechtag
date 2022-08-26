from django.core.mail import send_mail
from celery import shared_task


@shared_task
def async_send_mail(email_subject, email_body, email_receiver):
    send_mail(email_subject, email_body,
              "elternsprechtag@jhgcloud.de", [email_receiver, ])
