from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, Inquiry
from django.db.models import Q


@receiver(post_save, sender=Event)
def handleInquiries(sender, instance, **kwargs):
    inquiries = Inquiry.objects.filter(Q(type=0), Q(
        requester=instance.teacher), Q(respondent=instance.parent), Q(event=None))
    for inquiry in inquiries:
        if inquiry.student.shield_id in list(
                instance.student.values_list('shield_id', flat=True)):
            inquiry.event = instance
            inquiry.save()
