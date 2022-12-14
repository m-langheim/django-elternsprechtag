from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, Inquiry, Announcments
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
def addAnnouncments(sender, instance, created, **kwargs):
    if created:
        Announcments.objects.create(user=instance.respondent, inquiry=instance)


def deleteAnnouncment(sender, instance, **kwargs):
    if instance.processed == True:
        try:
            announcment = instance.announcment_set.all().first()
        except Announcments.DoesNotExist:
            pass
        else:
            announcment.delete()
