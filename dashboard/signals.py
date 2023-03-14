from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, Inquiry, Announcements
from django.db.models import Q
from django.utils import timezone
from authentication.tasks import async_send_mail
from django.template.loader import render_to_string
from django.urls import reverse
import os
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes


@receiver(post_save, sender=Event)
def handleInquiries(sender, instance, **kwargs):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(
        requester=instance.teacher), Q(respondent=instance.parent), Q(event=None))
    for inquiry in inquiries:
        if inquiry.students.first().shield_id in list(
                instance.student.values_list('shield_id', flat=True)):
            inquiry.event = instance
            inquiry.processed = True
            inquiry.save()


@receiver(post_save, sender=Inquiry)
def addAnnouncements(sender, instance: Inquiry, created: bool, **kwargs):
    if created:
        if instance.type == 1:
            async_send_mail.delay(
                "Termin-Anfrage",
                render_to_string(
                    "dashboard/email/new_inquiry_teacher.html",
                    {
                        'parent': instance.requester,
                        'teacher': instance.respondent,
                        'url': reverse("teacher_event_view", args=[instance.event.id]),
                        'current_site': os.environ.get("PUBLIC_URL")
                    }
                ), instance.respondet.email)
            Announcements.objects.create(
                user=instance.respondent, message='%s bittet um den Termin am %s um %s Uhr. Bitte bestätigen Sie den Termin.' % (instance.requester, timezone.localtime(instance.event.start).date().strftime("%d.%m.%Y"), timezone.localtime(instance.event.start).time().strftime("%H:%M")))
        elif instance.type == 0:
            async_send_mail.delay(
                "Termin-Anfrage",
                render_to_string(
                    "dashboard/email/new_inquiry_parent.html",
                    {
                        'parent': instance.respondent,
                        'teacher': instance.requester,
                        'url': reverse(
                            'inquiry_detail_view', args=[urlsafe_base64_encode(force_bytes(instance.id))]),
                        'current_site': os.environ.get("PUBLIC_URL")
                    }
                ), instance.respondet.email)
            Announcements.objects.create(
                user=instance.respondent, message='%s bittet Sie darum einen Termin zu erstellen' % (instance.requester))
