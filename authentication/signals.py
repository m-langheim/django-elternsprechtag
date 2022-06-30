from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student, Upcomming_User

from django.core.mail import send_mail
from django.template.loader import render_to_string


@receiver(post_save, sender=Student)
def add_access(sender, instance, created, **kwargs):
    if created:
        Upcomming_User.objects.create(student=instance)

# signal when new Upcomming_User object saved to send email to the child


@receiver(post_save, sender=Upcomming_User)
def send_email(sender, instance, created, **kwargs):
    if created:
        print(instance)
        current_site = "127.0.0.1:8000"
        email_subject = "Anmeldelink für den Elternsprechtag"
        email_body = render_to_string(
            'authentication/emails/link.html', {'current_site': current_site, 'id': instance.user_token, 'key': instance.access_key, 'otp': instance.otp})

        send_mail(email_subject, email_body, "admin@jhgcloud.de",
                  [instance.student.child_email])
