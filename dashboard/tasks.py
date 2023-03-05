from time import sleep
from dashboard.models import Event, SiteSettings, Inquiry
import datetime
from django.db.models import Q
from celery import shared_task
from django.utils import timezone
from authentication.models import CustomUser


@shared_task
def async_create_events():
    sleep(10)
    teachers = CustomUser.objects.filter(role=1)

    time_start = SiteSettings.objects.all().first().time_start
    time_end = SiteSettings.objects.all().first().time_end
    duration = SiteSettings.objects.all().first().event_duration
    for teacher in teachers:

        start = datetime.datetime.combine(
            datetime.date.today(), time_start)
        while start + duration <= datetime.datetime.combine(datetime.date.today(), time_end):
            try:
                Event.objects.get(teacher=teacher, start=start)
            except Event.DoesNotExist:
                Event.objects.create(
                    teacher=teacher, start=start, end=start+duration)
            start = start + duration


@shared_task
def async_create_events_special(teachers: list, date: str, start_t: str, end_t: str):
    print(SiteSettings.objects.all())
    duration = SiteSettings.objects.all().first().event_duration
    for teacher_pk in teachers:
        teacher = CustomUser.objects.get(Q(role=1), Q(id=int(teacher_pk)))
        start = datetime.datetime.combine(
            datetime.datetime.strptime(date, "%Y-%m-%d").date(), datetime.datetime.strptime(start_t, "%H:%M:%S").time())
        while start + duration <= datetime.datetime.combine(datetime.datetime.strptime(date, "%Y-%m-%d").date(), datetime.datetime.strptime(end_t, "%H:%M:%S").time()):
            try:
                Event.objects.get(
                    teacher=teacher, start=timezone.make_aware(start))
            except Event.DoesNotExist:
                Event.objects.create(
                    teacher=teacher, start=timezone.make_aware(start), end=timezone.make_aware(start+duration))
            start = start + duration
