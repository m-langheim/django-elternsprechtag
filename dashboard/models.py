import uuid

from django.db import models
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

    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    room = models.IntegerField(default=None, blank=True, null=True)

    occupied = models.BooleanField(default=False)


# Anfragen, die der Lehrer an einen Schüler schickt. Muss einzelnd sein, weil es auch möglich ist, dass es noch keinen Elternaccount zum Schüler gibt
class TeacherStudentInquiry(models.Model):
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 1})
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 0}, default=None, null=True, blank=True, related_name='%(class)s_parent')  # limit_choices_to={'role': 0} besagt, dass nur Nutzer, wo der Wert role glwich 0 ist eingesetzt werden können, also es wird verhindert, dass Lehrer oder andere als Eltern in Terminen gespeichert werden
    reason = models.TextField()

    event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, blank=True, null=True, default=None)
