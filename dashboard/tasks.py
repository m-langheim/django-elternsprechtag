from time import sleep
from dashboard.models import Event, SiteSettings
import datetime
from celery import shared_task

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
                Event.objects.get(requester=teacher, start=start)
            except Event.DoesNotExist:
                Event.objects.create(
                    requester=teacher, start=start, end=start+duration)
            start = start + duration
