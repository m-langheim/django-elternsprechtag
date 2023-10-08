from celery import shared_task, Celery
from elternsprechtag.celery import app
from django.core import management
import logging
from django.core.mail import send_mail, EmailMessage
from celery import shared_task
from django.conf import settings
from authentication.models import CustomUser
from django.template.loader import render_to_string
from dashboard.models import Event
from django.db.models import Q

from .utils import EventPDFExport

from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def run_dbbackup(**kwargs):
    logger.info("Databse Backup initiated...")
    management.call_command("dbbackup")

    logger.info("Media Backup initiated...")
    management.call_command("mediabackup")




@shared_task
def async_send_mail(email_subject, email_body, email_receiver, *args, **kwargs):
    if "email_html_body" in kwargs:
        send_mail(email_subject, email_body,
                  settings.EMAIL_COMPLETE, [email_receiver, ], html_message=kwargs.get("email_html_body"))
    else:
        send_mail(email_subject, email_body,
                  settings.EMAIL_COMPLETE, [email_receiver, ])

@shared_task
def daily_night_job(): # Hier können Aktionen ausgeführt werden, die jeden Tag laufen sollen.
    events = Event.objects.filter(Q(
                            start__gte=timezone.datetime.combine(
                                timezone.datetime.now().date(),
                                timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                            )
                        ),
                        Q(
                            start__lte=timezone.datetime.combine(
                                timezone.datetime.now().date(),
                                timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                            )))
    
    if events.count() > 0:
        receiving_user_list = [] # Hier werden alle Nutzer eingetragen, die für den heutigen Tag einen Termin haben

        for event in events:
            if event.parent:
                if event.parent.id not in receiving_user_list:
                    receiving_user_list.append(event.parent.id)
            if event.teacher:
                if event.teacher.id not in receiving_user_list:
                    receiving_user_list.append(event.teacher.id)
        for user_id in receiving_user_list:
            send_eventPDFs_over_email.delay(user_id)
    else: 
        print("Es wurden keine Events gefunden")

@shared_task
def send_eventPDFs_over_email(user_id=int):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        raise ("Error could not generate the PDF")
    else:
        generator = EventPDFExport(user.id)
        pdf = generator.print_events()
        mail = EmailMessage(
            "Ausdruck der gebuchten Termine", 
            render_to_string(
                "general_tasks/email_sendEventPDF.html",
                {"user":user}
                ),
            settings.EMAIL_COMPLETE, 
            [user.email]
        )

        mail.attach(f'events_{timezone.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.pdf', pdf.read(), "application/pdf")
        mail.send()