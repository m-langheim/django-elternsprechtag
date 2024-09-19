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
            bookable, reason = event.get_parent_event_individual_status(parent)

            # print(event.get_parent_event_individual_status(parent))

            event_dict[date][index].bookable = bookable

            match reason:
                case event.PersonalEventStatusChoices.INQUIRY_PENDING:
                    event_dict[date][index].inquiry_pending = True
                case event.PersonalEventStatusChoices.BOOKED:
                    event_dict[date][index].booked = True
                case event.PersonalEventStatusChoices.OCCUPIED:
                    event_dict[date][index].occupied = True
                case event.PersonalEventStatusChoices.TIME_CONFLICT:
                    event_dict[date][index].time_conflict = True
                case event.PersonalEventStatusChoices.TIME_CONFLICT_FOLLOWUP:
                    event_dict[date][index].time_conflict_followup = True
    return event_dict
