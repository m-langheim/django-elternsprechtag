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
    LeadStatusChoices,
    DayEventGroup,
    TeacherEventGroup,
)
from authentication.models import StudentChange
from django.db.models import Q

from .utils import EventPDFExport

from django.utils import timezone

from dashboard.utils import check_parent_book_event_allowed

logger = logging.getLogger(__name__)


def automatically_update_base_events():
    logger.debug("Starting to update lead status for base events.")
    current_base_events = BaseEventGroup.objects.filter(
        Q(valid_until__gte=timezone.now()),
        Q(disable_automatic_changes=False),
        Q(lead_manual_override=False),
    )

    lead_inquiry_bases = current_base_events.filter(
        Q(lead_inquiry_start__lte=timezone.now()), Q(lead_start__gte=timezone.now())
    )

    for base in lead_inquiry_bases:
        if base.lead_status_last_change < timezone.datetime.combine(
            date=base.lead_inquiry_start,
            time=timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
        ):
            base.lead_status = LeadStatusChoices.INQUIRY
            base.lead_status_last_change = timezone.now()
            base.save()

    lead__bases = current_base_events.filter(Q(lead_start__lte=timezone.now()))

    for base in lead__bases:
        if base.lead_status_last_change < timezone.datetime.combine(
            date=base.lead_start,
            time=timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
        ):
            base.lead_status = LeadStatusChoices.ALL
            base.lead_status_last_change = timezone.now()
            base.save()

    logger.debug("Finished updating lead status for base events.")


def automatically_update_day_groups():
    logger.debug("Starting to update lead status for day groups.")
    lead_inquiry_day_group = DayEventGroup.objects.filter(
        Q(date__gte=timezone.now()),
        Q(lead_inquiry_start__lte=timezone.now()),
        Q(lead_start__gte=timezone.now()),
        Q(disable_automatic_changes=False),
        Q(lead_manual_override=False),
    )

    for day in lead_inquiry_day_group:
        if day.lead_status_last_change < timezone.datetime.combine(
            date=day.lead_inquiry_start,
            time=timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
        ):
            day.lead_status = LeadStatusChoices.INQUIRY
            day.lead_status_last_change = timezone.now()
            day.save()

    lead_day_group = DayEventGroup.objects.filter(
        Q(date__gte=timezone.now()),
        Q(lead_start__lte=timezone.now()),
        Q(disable_automatic_changes=False),
        Q(lead_manual_override=False),
    )

    for day in lead_day_group:
        if day.lead_status_last_change < timezone.datetime.combine(
            date=day.lead_inquiry_start,
            time=timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
        ):
            day.lead_status = LeadStatusChoices.INQUIRY
            day.lead_status_last_change = timezone.now()
            day.save()

    logger.debug("Finished updating lead status for day groups.")


def automatically_update_teacher_groups():
    logger.debug("Starting to update lead status for teacher groups.")

    lead_inquiry_teacher_group = TeacherEventGroup.objects.filter(
        Q(day_group__in=DayEventGroup.objects.filter(date__gte=timezone.now())),
        Q(lead_inquiry_start__lte=timezone.now()),
        Q(lead_start__gte=timezone.now()),
        Q(disable_automatic_changes=False),
        Q(lead_manual_override=False),
    )

    for teacher_group in lead_inquiry_teacher_group:
        if teacher_group.lead_status_last_change < timezone.datetime.combine(
            date=teacher_group.lead_inquiry_start,
            time=timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
        ):
            teacher_group.lead_status = LeadStatusChoices.INQUIRY
            teacher_group.lead_status_last_change = timezone.now()
            teacher_group.save()

    lead_teacher_group = TeacherEventGroup.objects.filter(
        Q(day_group__in=DayEventGroup.objects.filter(date__gte=timezone.now())),
        Q(lead_start__lte=timezone.now()),
        Q(disable_automatic_changes=False),
        Q(lead_manual_override=False),
    )

    for teacher_group in lead_teacher_group:
        if teacher_group.lead_status_last_change < timezone.datetime.combine(
            date=teacher_group.lead_start,
            time=timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
        ):
            teacher_group.lead_status = LeadStatusChoices.ALL
            teacher_group.lead_status_last_change = timezone.now()
            teacher_group.save()

    logger.debug("Finished updating lead status for teacher groups.")
