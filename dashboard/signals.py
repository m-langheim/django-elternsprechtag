from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, Inquiry, Announcements
from django.db.models import Q


@receiver(post_save, sender=Event)
def handleInquiries(sender, instance, **kwargs):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(
        requester=instance.teacher), Q(respondent=instance.parent), Q(event=None))
    for inquiry in inquiries:
        if inquiry.students.first().shield_id in list(
                instance.student.values_list('shield_id', flat=True)):
            inquiry.event = instance
            inquiry.save()


@receiver(post_save, sender=Inquiry)
def addAnnouncements(sender, instance: Inquiry, created: bool, **kwargs):
    if created:
        if instance.type == 1:
            Announcements.objects.create(
                user=instance.respondent, message='%s bittet um den Termin am %s um %s Uhr. Bitte bestätigen Sie den Termin.' % (instance.requester, instance.event.start.date().strftime("%d.%m.%Y"), instance.event.start.time().strftime("%H:%M")))
        elif instance.type == 0:
            Announcements.objects.create(
                user=instance.respondent, message='%s bittet Sie darum einen Termin zu erstellen' % (instance.requester))
