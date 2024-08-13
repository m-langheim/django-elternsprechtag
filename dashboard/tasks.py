from time import sleep
from dashboard.models import Event, SiteSettings, Inquiry, EventChangeFormula
import datetime
from django.db.models import Q
from celery import shared_task
from django.utils import timezone
from authentication.models import CustomUser


@shared_task
def async_create_events():
    teachers = CustomUser.objects.filter(role=1)

    time_start = SiteSettings.objects.all().first().time_start
    time_end = SiteSettings.objects.all().first().time_end
    duration = SiteSettings.objects.all().first().event_duration
    for teacher in teachers:
        start = datetime.datetime.combine(datetime.date.today(), time_start)
        while start + duration <= datetime.datetime.combine(
            datetime.date.today(), time_end
        ):
            try:
                Event.objects.get(teacher=teacher, start=start)
            except Event.DoesNotExist:
                Event.objects.create(teacher=teacher, start=start, end=start + duration)
            start = start + duration


@shared_task
def async_create_events_special(teachers: list, date: str, start_t: str, end_t: str):
    duration = SiteSettings.objects.all().first().event_duration
    for teacher_pk in teachers:
        teacher = CustomUser.objects.get(Q(role=1), Q(id=int(teacher_pk)))
        start = datetime.datetime.combine(
            datetime.datetime.strptime(date, "%Y-%m-%d").date(),
            datetime.datetime.strptime(start_t, "%H:%M:%S").time(),
        )
        while start + duration <= datetime.datetime.combine(
            datetime.datetime.strptime(date, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_t, "%H:%M:%S").time(),
        ):
            try:
                Event.objects.get(teacher=teacher, start=timezone.make_aware(start))
            except Event.DoesNotExist:
                Event.objects.create(
                    teacher=teacher,
                    start=timezone.make_aware(start),
                    end=timezone.make_aware(start + duration),
                )
            start = start + duration


@shared_task
def apply_event_change_formular(formular_id: int):
    try:
        formular = EventChangeFormula.objects.get(id=formular_id)
    except:
        pass
    else:
        start = timezone.datetime.combine(formular.date, formular.start_time)
        end = timezone.datetime.combine(formular.date, formular.end_time)
        teacher = formular.teacher
        duration = SiteSettings.objects.all().first().event_duration

        while start + duration <= end:
            Event.objects.get_or_create(
                teacher=teacher,
                day_group=formular.day_group,
                teacher_event_group=formular.teacher_event_group,
                start=start,
                end=start + duration,
            )
            start = start + duration


@shared_task
def all_events_update_event_lead_status():
    for event in Event.objects.all():
        event.update_event_lead_status()
