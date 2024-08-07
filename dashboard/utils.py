from .models import Inquiry, Event, CustomUser
from django.db.models import Q
from django.utils import timezone


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


def check_parent_book_event_allowed(
    parent: CustomUser, event: Event = None, teacher: CustomUser = None
):
    if parent.role != 0:
        raise ValueError(
            "The provided user is not a parent. This function requires a parent user!"
        )

    if event:
        match event.lead_status:
            case 0:
                return False
            case 1:
                return parent.has_perm("dashboard.condition_prebook_event")
            case 2:
                inquiry = Inquiry.objects.filter(
                    Q(type=0),
                    Q(requester=event.teacher),
                    Q(respondent=parent),
                    Q(processed=False),
                )

                return inquiry.exists()
            case 3:
                return True
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
        raise ValueError("One of the attributes teacher or event must be set.")
