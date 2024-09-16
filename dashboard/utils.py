from .models import (
    Inquiry,
    Event,
    CustomUser,
    SiteSettings,
    DayEventGroup,
    TeacherEventGroup,
)
from django.db.models import Q
from django.utils import timezone

PERSONAL_EVENT_STATUS = (
    (0, "Event bookable"),
    (1, "Inquiry pending"),
    (2, "Booked"),
    (3, "Occupied"),
    (4, "Blocked"),
    (5, "Time conflict"),
)


def check_inquiry_reopen(parent: CustomUser, teacher: CustomUser):
    for inquiry in Inquiry.objects.filter(
        Q(respondent=parent), Q(requester=teacher), Q(type=0), Q(processed=True)
    ):
        if inquiry.students not in Event.objects.filter(
            Q(teacher=teacher), Q(parent=parent), Q(occupied=True)
        ).values_list("student", flat=True):
            print("Inquiry wieder geöffnet")
            inquiry.processed = False
            inquiry.event = None
            inquiry.save()


def check_event_time_conflict(parent: CustomUser, event: Event):
    min_event_seperation = SiteSettings.objects.first().min_event_seperation
    conflicting_events = (
        Event.objects.filter(Q(parent=parent))
        .exclude(start__gt=event.end + min_event_seperation)
        .exclude(end__lt=event.start - min_event_seperation)
    )
    return conflicting_events.exists()


def check_parent_book_event_allowed(
    parent: CustomUser, event: Event = None, teacher: CustomUser = None
):
    if parent.role != 0:
        raise ValueError(
            _("The function requires a parent, but the user is not a parent.") #The provided user is not a parent. This function requires a parent user!
        )

    if event:
        match event.lead_status:
            case 0:
                return False
            case 1:
                return parent.has_perm(
                    "dashboard.condition_prebook_event"
                ) and not check_event_time_conflict(parent, event)
            case 2:
                inquiry = Inquiry.objects.filter(
                    Q(type=0),
                    Q(requester=event.teacher),
                    Q(respondent=parent),
                    Q(processed=False),
                )

                return inquiry.exists() and not check_event_time_conflict(parent, event)
            case 3:
                return True and not check_event_time_conflict(parent, event)
    elif teacher:
        lead_min_status = 3
        inquiry = Inquiry.objects.filter(
            Q(type=0),
            Q(requester=teacher),
            Q(respondent=parent),
            Q(processed=False),
        )

        if inquiry.exists():
            lead_min_status = 2
        if parent.has_perm("dashboard.condition_prebook_event"):
            lead_min_status = 1
        events = Event.objects.filter(
            Q(teacher=teacher),
            Q(start__gte=timezone.now()),
            Q(lead_status__gte=lead_min_status),
        )
        return events.exists()
    else:
        raise ValueError(_("Either the teacher or the date must be given as an attribute.")) #One of the attributes teacher or event must be set.


def check_event_bookable(parent: CustomUser, event: Event):
    if (
        event.occupied and event.parent != parent
    ):  # Das Event wurde gebucht und ist von einem anderen Elternteil belegt
        return PERSONAL_EVENT_STATUS[3][0]
    elif (
        event.occupied and event.parent == parent
    ):  # Das Event wurde von dem angegebenen Elternteil gebucht
        match event.status:
            case 1:
                return PERSONAL_EVENT_STATUS[2][0]
            case 2:
                return PERSONAL_EVENT_STATUS[1][0]
    if check_parent_book_event_allowed(parent, event):
        return PERSONAL_EVENT_STATUS[0][0]  # Parent is allowed to book the event
    elif not check_event_time_conflict(parent, event):
        return PERSONAL_EVENT_STATUS[4][
            0
        ]  # There is an other conflict like not having the current permission level or an inquiry
    else:
        return PERSONAL_EVENT_STATUS[5][0]  # Time conflict


# def addEvent(
#     teacher: CustomUser,
#     start: timezone.datetime,
#     end: timezone.datetime,
#     lead_start: timezone.datetime.date = None,
#     lead_inquiry_start: timezone.datetime.date = None,
# ) -> Event:

#     if start > end:
#         raise ValueError("The events end time must be later than the event start time.")
#     if lead_start and lead_start > start:
#         raise ValueError("The lead start must be set before the event start.")
#     if lead_start and lead_inquiry_start and lead_start > lead_inquiry_start:
#         raise ValueError(
#             "The lead inquiry field is designed to be set before the lead start value.",
#         )

#     if not lead_start or not lead_inquiry_start:
#         lead_start = start.date() - timezone.timedelta(days=7)
#         lead_inquiry_start = start.date() - timezone.timedelta(days=14)

#     day_group = DayEventGroup.objects.get_or_create(
#         Q(date=start.date()),
#         Q(lead_start=lead_start),
#         Q(lead_inquiry_start=lead_inquiry_start),
#     )

#     teacher_event_group = TeacherEventGroup.objects.get_or_create(
#         Q(teacher=teacher),
#         Q(day_group=day_group),
#         Q(lead_start=lead_start),
#         Q(lead_inquiry_start=lead_inquiry_start),
#     )

#     event = Event.objects.get_or_create(
#         Q(teacher=teacher),
#         Q(start=start),
#         Q(end=end),
#         Q(day_group=day_group),
#         Q(teacher_event_group=teacher_event_group),
#     )

#     return event
