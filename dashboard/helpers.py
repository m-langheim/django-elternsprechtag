from django.db.models import Q
from django.utils import timezone
import pytz


def create_event_date_dict(events):
    events_dt = events

    dates = []
    datetime_objects = events_dt.order_by("start").values_list("start", flat=True)
    for datetime_object in datetime_objects:
        if timezone.localtime(datetime_object).date() not in [
            date.date() for date in dates
        ]:
            dates.append(datetime_object.astimezone(pytz.UTC))

    events_dt_dict = {}
    for date in dates:
        events_dt_dict[str(date.date())] = events.filter(
            Q(
                start__gte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                )
            ),
            Q(
                start__lte=timezone.datetime.combine(
                    date.date(),
                    timezone.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                )
            ),
        ).order_by("start")

    return events_dt_dict
