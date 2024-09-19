from celery import shared_task, Celery
from elternsprechtag.celery import app
from django.core import management
import logging
from django.core.mail import send_mail, EmailMessage
from celery import shared_task
from django.conf import settings
from authentication.models import CustomUser
from django.template.loader import render_to_string
from dashboard.models import (
    Event,
    Inquiry,
    SiteSettings,
    Announcements,
    EventChangeFormula,
    BaseEventGroup,
)
from authentication.models import StudentChange
from django.db.models import Q

from .utils import EventPDFExport

from django.utils import timezone

from dashboard.utils import check_parent_book_event_allowed

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
        send_mail(
            email_subject,
            email_body,
            settings.EMAIL_COMPLETE,
            [
                email_receiver,
            ],
            html_message=kwargs.get("email_html_body"),
        )
    else:
        send_mail(
            email_subject,
            email_body,
            settings.EMAIL_COMPLETE,
            [
                email_receiver,
            ],
        )


@shared_task
def initiateEventPDFs():  # Mit diesem Task wird damit begonnen an alle Nutzer, die an dem Tag der Ausführung einen Termin vereinbart haben, die Termine per PDF zu senden.
    events = Event.objects.filter(
        Q(
            start__gte=timezone.datetime.combine(
                timezone.datetime.now().date(),
                timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
            )
        ),
        Q(
            start__lte=timezone.datetime.combine(
                timezone.datetime.now().date(),
                timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
            )
        ),
    )

    if events.count() > 0:
        receiving_user_list = (
            []
        )  # Hier werden alle Nutzer eingetragen, die für den heutigen Tag einen Termin haben

        for event in events:
            if event.parent:
                if event.parent.id not in receiving_user_list:
                    receiving_user_list.append(event.parent.id)
            if event.teacher:
                if event.teacher.id not in receiving_user_list:
                    receiving_user_list.append(event.teacher.id)
        for user_id in receiving_user_list:
            send_eventPDFs_over_email.delay(user_id)


@shared_task
def look_for_open_inquiries():
    inquiries = Inquiry.objects.filter(
        Q(processed=False), Q(type=0)
    )  # Hier werden alle nicht bearbeiteten Anfragen von Lehrern an Eltern geöffnet

    respondents_list = []

    for inquiry in inquiries:
        if inquiry.respondent.id not in respondents_list:
            respondents_list.append(inquiry.respondent.id)

    for respondent_id in respondents_list:
        try:
            respondent = CustomUser.objects.get(id=respondent_id)
        except CustomUser.DoesNotExist:
            print("Error")
        else:
            res_inquiries_queryset = Inquiry.objects.filter(
                Q(processed=False),
                Q(type=0),
                Q(respondent=respondent),
                Q(
                    base_event__in=BaseEventGroup.objects.filter(
                        valid_until__gte=timezone.now()
                    )
                ),
            )

            res_inquiries = [
                inquiry
                for inquiry in res_inquiries_queryset
                if check_parent_book_event_allowed(
                    parent=inquiry.respondent, teacher=inquiry.requester
                )
            ]

            async_send_mail.delay(
                "Offene Anfragen",
                render_to_string(
                    "general_tasks/email_unproccessedInquiries_reminder.html",
                    {"user": respondent, "res_inquiries": res_inquiries},
                ),
                respondent.email,
            )


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
            render_to_string("general_tasks/email_sendEventPDF.html", {"user": user}),
            settings.EMAIL_COMPLETE,
            [user.email],
        )

        mail.attach(
            f'events_{timezone.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.pdf',
            pdf.read(),
            "application/pdf",
        )
        mail.send()


@shared_task
def dayly_cleanup_task():
    if SiteSettings.objects.first().delete_events:
        past_events = Event.objects.filter(
            end__lte=timezone.now() - SiteSettings.objects.first().keep_events
        )
        past_events.delete()

    if SiteSettings.objects.first().delete_announcements:
        past_announcements = Announcements.objects.filter(
            created__lte=timezone.now()
            - SiteSettings.objects.first().keep_announcements
        )
        past_announcements.delete()

    if SiteSettings.objects.first().delete_student_changes:
        past_student_changes = StudentChange.objects.filter(
            created__lte=timezone.now()
            - SiteSettings.objects.first().keep_student_changes
        )
        past_student_changes.delete()

    for obj in SiteSettings.objects.first().iquiry_bahvior:
        inquiry_type = obj["type"]
        inquiry_delete = obj["delete"]
        inquiry_timedelta_days = obj["keep_for_days"]

        if inquiry_delete:
            inquiries = Inquiry.objects.filter(
                Q(type=inquiry_type),
                Q(
                    created__lte=timezone.now()
                    - timezone.timedelta(days=inquiry_timedelta_days)
                ),
            )
            inquiries.delete()

    if SiteSettings.objects.first().delete_event_change_formulas:
        past_event_change_formulas = EventChangeFormula.objects.filter(
            date__lte=timezone.now()
            - SiteSettings.objects.first().keep_event_change_formulas
        )
        past_event_change_formulas.delete()


@shared_task(bind=True)
def update_event_lead_status(self, *args, **kwargs):
    events = Event.objects.filter(
        Q(disable_automatic_changes=False),
        Q(start__lte=timezone.now()),
        Q(lead_manual_override=False),
    )

    for event in events:
        event.update_event_lead_status()
