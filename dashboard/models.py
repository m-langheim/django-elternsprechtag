import uuid
import datetime

from django.db import models
from django.core.cache import cache
from authentication.models import CustomUser, Student
from django.utils import timezone

# Create your models here.


class Event(models.Model):  # Termin
    # identifier für diesen speziellen Termin
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 1})  # limit_choices_to={'role': 1} besagt, dass nur Nutzer, wo der Wert role glwich 1 ist eingesetzt werden können, also es wird verhindert, dass Eltern oder andere als Lehrer in Terminen gespeichert werden

    parent = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, limit_choices_to={'role': 0}, default=None, null=True, blank=True, related_name='%(class)s_parent')  # limit_choices_to={'role': 0} besagt, dass nur Nutzer, wo der Wert role glwich 0 ist eingesetzt werden können, also es wird verhindert, dass Lehrer oder andere als Eltern in Terminen gespeichert werden

    student = models.ManyToManyField(
        Student, default=None, blank=True)

    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    room = models.IntegerField(default=None, blank=True, null=True)

    occupied = models.BooleanField(default=False)


# Anfragen, die der Lehrer an einen Schüler schickt. Muss einzelnd sein, weil es auch möglich ist, dass es noch keinen Elternaccount zum Schüler gibt
class TeacherStudentInquiry(models.Model):
    requester = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 1}, related_name='%(class)s_requester')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    respondent = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 0}, default=None, null=True, blank=True, related_name='%(class)s_respondent')  # limit_choices_to={'role': 0} besagt, dass nur Nutzer, wo der Wert role glwich 0 ist eingesetzt werden können, also es wird verhindert, dass Lehrer oder andere als Eltern in Terminen gespeichert werden
    reason = models.TextField()

    event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, blank=True, null=True, default=None)


########################################################################### Settings ###################################################


class SingletonModel(models.Model):  # set all general setting for Singleton models

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(SingletonModel):
    lead_start = models.DateField(default=timezone.now)
    lead_inquiry_start = models.DateField(default=timezone.now)
    event_duration = models.DurationField(
        default=datetime.timedelta(seconds=0))
    time_start = models.TimeField(default=timezone.now)
    time_end = models.TimeField(default=timezone.now)
