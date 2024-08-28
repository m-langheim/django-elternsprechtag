from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import (
    Event,
    Inquiry,
    Announcements,
    EventChangeFormula,
    DayEventGroup,
    TeacherEventGroup,
    BaseEventGroup,
)
from django.db.models import Q
from django.utils import timezone
from authentication.tasks import async_send_mail
from django.template.loader import render_to_string
from django.urls import reverse
import os
import datetime
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from .utils import check_inquiry_reopen


@receiver(post_save, sender=Event)
def handleInquiries(sender, instance, **kwargs):
    """
    Diese Funktion dient dazu nach der Buchung eines Termins mögliche Anfragen Seitens des Lehrers auf beantwortet zu setzen.

    Args:
        sender (_type_): _description_
        instance (Event): _description_
    """
    inquiries = Inquiry.objects.filter(
        Q(type=0),
        Q(requester=instance.teacher),
        Q(respondent=instance.parent),
        Q(event=None),
    )
    for inquiry in inquiries:
        if inquiry.students.first().shield_id in list(
            instance.student.values_list("shield_id", flat=True)
        ):
            inquiry.event = instance
            inquiry.processed = True
            inquiry.save()


@receiver(post_save, sender=Inquiry)
def addAnnouncements(sender, instance: Inquiry, **kwargs):
    """_summary_

    Args:
        sender (_type_): _description_
        instance (Inquiry): _description_
        created (bool): _description_
    """
    if not instance.notified:
        if instance.type == 1:

            email_subject = "New appointment request"
            email_str_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_teacher.txt",
                {
                    "parent": instance.requester,
                    "teacher": instance.respondent,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse("teacher_event_view", args=[instance.event.id]),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )
            email_html_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_teacher.html",
                {
                    "parent": instance.requester,
                    "teacher": instance.respondent,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse("teacher_event_view", args=[instance.event.id]),
                    "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )  #! Dies wird derzeit nicht benutzt

            # async_send_mail.delay(
            #     email_subject,
            #     email_str_body,
            #     instance.respondent.email,
            #     email_html_body=email_html_body,
            # )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                instance.respondent.email,
            )  #! Hier wird keine HTML versendet

            Announcements.objects.create(
                user=instance.respondent,
                message="%s bittet um den Termin am %s um %s Uhr. Bitte bestätigen Sie den Termin."
                % (
                    instance.requester,
                    timezone.localtime(instance.event.start)
                    .date()
                    .strftime("%d.%m.%Y"),
                    timezone.localtime(instance.event.start).time().strftime("%H:%M"),
                ),
            )
            instance.notified = True
            instance.save()
        elif instance.type == 0 and len(instance.students.all()) > 0:
            instance.notified = True
            instance.save()

            email_subject = "New appointment request"
            email_str_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_parent.txt",
                {
                    "parent": instance.respondent,
                    "teacher": instance.requester,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse(
                        "inquiry_detail_view",
                        args=[urlsafe_base64_encode(force_bytes(instance.id))],
                    ),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )
            email_html_body = render_to_string(
                "dashboard/email/new_inquiry/new_inquiry_parent.html",
                {
                    "parent": instance.respondent,
                    "teacher": instance.requester,
                    "url": str(os.environ.get("PUBLIC_URL"))
                    + reverse(
                        "inquiry_detail_view",
                        args=[urlsafe_base64_encode(force_bytes(instance.id))],
                    ),
                    "date": datetime.datetime.now().strftime("%d.%m.%Y"),
                    # "students": "\n,".join(
                    #    [
                    #        "{} {}".format(student.first_name, student.last_name)
                    #        for student in instance.students.all()
                    #    ]
                    # ),
                },
            )  #! Dies wird derzeit nicht benutzt

            # async_send_mail.delay(
            #     email_subject,
            #     email_str_body,
            #     instance.respondent.email,
            #     email_html_body=email_html_body,
            # )

            async_send_mail.delay(
                email_subject,
                email_str_body,
                instance.respondent.email,
            )  #! Hier wird keine HTML versendet

            Announcements.objects.create(
                user=instance.respondent,
                message="%s bittet Sie darum einen Termin zu erstellen"
                % (instance.requester),
            )


@receiver(post_delete, sender=Inquiry)
def freeEvents(sender, instance, **kwarg):
    inquiriy = instance
    try:
        event = inquiriy.event
    except:
        pass
    else:
        if inquiriy.type == 1 and not inquiriy.processed and event:
            check_inquiry_reopen(event.parent, event.teacher)
            event.parent = None
            event.student.clear()
            event.status = 0
            event.occupied = False
            event.save()

            print(event)


@receiver(pre_save, sender=EventChangeFormula)
def openNewEventChangeFormulaOnDisapprove(sender, instance, *args, **kwargs):
    if instance.id is None:
        pass
    else:
        current = instance
        previouse = EventChangeFormula.objects.get(id=instance.id)

        if previouse.status == 1 and current.status == 3 and current.type == 0:
            EventChangeFormula.objects.create(
                teacher=instance.teacher,
                date=instance.date,
                teacher_event_group=instance.teacher_event_group,
                day_group=instance.day_group,
            )


@receiver(pre_save, sender=Event)
def checkLeadStatusChange(sender, instance, *args, **kwargs):
    current = instance
    try:
        previouse = Event.objects.get(id=instance.id)
    except Event.DoesNotExist:
        pass
    else:
        if current.lead_status != previouse.lead_status:
            instance.lead_status_last_change = timezone.now()


@receiver(post_save, sender=DayEventGroup)
def updateBaseEventValidUntil(
    sender, instance: DayEventGroup, created, *args, **kwargs
):
    if created:
        if (
            not DayEventGroup.objects.filter(
                Q(date__gte=instance.date), Q(base_event=instance.base_event)
            )
            .exclude(pk=instance.pk)
            .exists()
            and instance.base_event.valid_until < instance.date
        ):
            instance.base_event.valid_until = instance.date + timezone.timedelta(days=7)
            instance.base_event.save()


@receiver(pre_save, sender=BaseEventGroup)
def updateLeadDatesBaseEvent(sender, instance, *args, **kwargs):
    current: BaseEventGroup = instance
    try:
        previouse = BaseEventGroup.objects.get(id=current.id)
    except BaseEventGroup.DoesNotExist:
        pass
    else:
        day_event_groups = DayEventGroup.objects.filter(Q(base_event=previouse))

        if not current.force:
            day_event_groups = day_event_groups.exclude(Q(lead_manual_override=True))
        else:
            current.force = False
            current.save()

        if (
            previouse.lead_start != current.lead_start
            or previouse.lead_inquiry_start != current.lead_inquiry_start
        ):
            for day_event_group in day_event_groups:
                day_event_group.lead_start = instance.lead_start
                day_event_group.lead_inquiry_start = instance.lead_inquiry_start
                day_event_group.save()

        if current.manual_apply:
            for day_event_group in day_event_groups:
                day_event_group.lead_status = current.lead_status
                day_event_group.manual_apply = True
                day_event_group.save()

            current.manual_apply = False
            current.save()


@receiver(pre_save, sender=DayEventGroup)
def updateLeadDatesDayEventGroups(sender, instance, *args, **kwargs):
    current: DayEventGroup = instance
    try:
        previouse = DayEventGroup.objects.get(id=current.id)
    except DayEventGroup.DoesNotExist:
        pass
    else:
        teacher_event_groups = TeacherEventGroup.objects.filter(Q(day_group=previouse))
        if not current.force:
            teacher_event_groups = teacher_event_groups.exclude(
                Q(lead_manual_override=True)
            )
        else:
            current.force = False
            current.save()

        if (
            previouse.lead_start != current.lead_start
            or previouse.lead_inquiry_start != current.lead_inquiry_start
        ):
            for teacher_event_group in teacher_event_groups:
                teacher_event_group.lead_start = instance.lead_start
                teacher_event_group.lead_inquiry_start = instance.lead_inquiry_start
                teacher_event_group.save()

        if current.manual_apply:
            for teacher_event_group in teacher_event_groups:
                teacher_event_group.lead_status = current.lead_status
                teacher_event_group.manual_apply = True
                teacher_event_group.disable_automatic_changes = (
                    current.disable_automatic_changes
                )
                teacher_event_group.lead_manual_override = False
                teacher_event_group.save()

                current.manual_apply = False
                current.save()


@receiver(pre_save, sender=TeacherEventGroup)
def updateLeadStatusPerEvent(sender, instance, *args, **kwargs):
    current: TeacherEventGroup = instance
    try:
        previouse = TeacherEventGroup.objects.get(id=current.id)
    except TeacherEventGroup.DoesNotExist:
        pass
    else:
        events = Event.objects.filter(Q(teacher_event_group=previouse))
        if not current.force:
            events = events.exclude(Q(lead_manual_override=True))
        else:
            current.force = False
            current.save()

        if current.manual_apply:
            events.update(
                lead_status=current.lead_status,
                disable_automatic_changes=current.disable_automatic_changes,
                lead_manual_override=False,
            )

            current.manual_apply = False
            current.save()
