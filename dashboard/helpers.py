from django.db.models import Q
from django.utils import timezone
from .utils import *
import pytz
from .models import Inquiry, Event, CustomUser, SiteSettings


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


def event_date_dict_add_book_information(parent: CustomUser, event_dict: dict):
    for date in event_dict.keys():
        for index, event in enumerate(event_dict[date]):
            match check_event_bookable(parent, event):
                case 0:
                    event_dict[date][index].bookable = True
                case 1:
                    event_dict[date][index].bookable = True
                    event_dict[date][index].inquiry_pending = True
                case 2:
                    event_dict[date][index].bookable = True
                    event_dict[date][index].booked = True
                case 3:
                    event_dict[date][index].bookable = False
                    event_dict[date][index].occupied = True
                case 4:
                    event_dict[date][index].bookable = False
                case 5:
                    event_dict[date][index].bookable = False
                    event_dict[date][index].time_conflict = True
    return event_dict
