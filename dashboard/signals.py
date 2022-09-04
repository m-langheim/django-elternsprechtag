from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, TeacherStudentInquiry
from django.db.models import Q


@receiver(post_save, sender=Event)
def handleInquiries(sender, instance, **kwargs):
    inquiries = TeacherStudentInquiry.objects.filter(
        Q(teacher=instance.teacher), Q(parent=instance.parent), Q(event=None))
    for inquiry in inquiries:
        if inquiry.student.shield_id in list(
                instance.student.values_list('shield_id', flat=True)):
            inquiry.event = instance
            inquiry.save()
