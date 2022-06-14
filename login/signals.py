from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student, Upcomming_User


@receiver(post_save, sender=Student)
def add_access(sender, instance, created, **kwargs):
    if created:
        Upcomming_User.objects.create(student=instance)
