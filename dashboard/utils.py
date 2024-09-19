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
from django.utils.translation import gettext as _


# class PersonalEventStatusChoices:
#     EVENT_BOOKABLE = 0, "Event bookable"
#     INQUIRY_PENDING = 1, "Inquiry pending"
#     BOOKED = 2, "Booked"
#     OCCUPIED = 3, "Occupied"
#     BLOCKED = 4, "Blocked"
#     TIME_CONFLICT = 5, "Time conflict"
#     TIME_CONFLICT_FOLLOWUP = 6, "Followup event"


def check_inquiry_reopen(parent: CustomUser, teacher: CustomUser):
    for inquiry in Inquiry.objects.filter(
        Q(respondent=parent), Q(requester=teacher), Q(type=0), Q(processed=True)
    ):
        print(
            inquiry.students.all(),
            Event.objects.filter(
                Q(teacher=teacher), Q(parent=parent), Q(occupied=True)
            ).values_list("student", flat=True),
        )
        day_group = DayEventGroup.objects.filter(base_event=inquiry.base_event)
        for student in inquiry.students.all():
            if student.pk not in Event.objects.filter(
                Q(teacher=teacher),
                Q(parent=parent),
                Q(occupied=True),
                Q(day_group__in=day_group),
            ).values_list("student", flat=True):
                inquiry.processed = False
                inquiry.event = None
                inquiry.save()


def check_parent_book_event_allowed(parent: CustomUser, teacher: CustomUser):
    if parent.role != 0:
        raise ValueError(
            _(
                "The function requires a parent, but the user is not a parent."
            )  # The provided user is not a parent. This function requires a parent user!
        )

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
