from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q

from dashboard.models import Inquiry, Event


@receiver(post_save, sender=Inquiry)
def handleTeacherNewInquiry(sender, instance: Inquiry, created: bool, **kwargs):
    if created and instance.type == 1:
        requested_student = instance.students.first

        try:
            event = Event.objects.exclude(status=0).get(
                Q(teacher=instance.requester),
                Q(student=requested_student),
                Q(parent=instance.respondent),
            )
        except Event.DoesNotExist:
            pass
        else:
            instance.processed = True
            instance.save()
