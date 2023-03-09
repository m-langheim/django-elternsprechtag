from .models import Inquiry, Event, CustomUser
from django.db.models import Q


def check_inquiry_reopen(parent: CustomUser, teacher: CustomUser):
    for inquiry in Inquiry.objects.filter(Q(respondent=parent), Q(requester=teacher), Q(type=0), Q(processed=True)):
        if inquiry.students not in Event.objects.filter(Q(teacher=teacher), Q(parent=parent), Q(occupied=True)).values_list('student', flat=True):
            print("Inquiry wieder geöffnet")
            inquiry.processed = False
            inquiry.event = None
            inquiry.save()
