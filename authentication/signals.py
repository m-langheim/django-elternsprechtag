from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student, Upcomming_User, CustomUser, TeacherExtraData
from django.template.loader import render_to_string
from django.contrib.auth.models import Group

from authentication.tasks import async_send_mail
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender=Student)
def add_access(sender, instance, created, **kwargs):
    if created:
        Upcomming_User.objects.create(student=instance)


@receiver(post_save, sender=Student)
# add groups for all new classes when a student is registered
def add_groups(sender, instance, **kwargs):
    class_group = Group.objects.get_or_create(
        name="class_"+instance.class_name)

    parent = CustomUser.objects.filter(students=instance)
    if parent.exists():  # ! all groups are reseted when new student data gets imported
        class_group.user_set.add(parent)


# @receiver(post_save, sender=CustomUser)
# def add_parents_to_group(sender, instance, created, **kwargs):
#    if created and instance.role == 0:
#        parent_group = Group.objects.get_or_create(name="parents")
#        parent_group.user_set.add(instance)


@receiver(post_save, sender=CustomUser)
def add_teacher_data(sender, instance, created, **kwargs):
    if created and instance.role == 1:
        TeacherExtraData.objects.create(teacher=instance)

# signal when new Upcomming_User object saved to send email to the child


@receiver(post_save, sender=Upcomming_User)
def send_email(sender, instance, created, **kwargs):
    if created:
        print(instance)
        current_site = "127.0.0.1:8000"
        email_subject = "Anmeldelink für den Elternsprechtag"
        email_body = render_to_string(
            'authentication/emails/link.html', {'current_site': current_site, 'id': instance.user_token, 'key': instance.access_key, 'otp': instance.otp})

        # async_send_mail.delay(email_subject, email_body,
        #                      instance.student.child_email)
        send_mail(email_subject, email_body, settings.EMAIL_HOST_USER,
                  [instance.student.child_email])
