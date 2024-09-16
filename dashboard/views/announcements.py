from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from authentication.models import CustomUser, TeacherExtraData, Student, Tag
from ..models import Event, Inquiry, SiteSettings, Announcements
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.views import View
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _

from django.shortcuts import get_object_or_404
from django.urls import reverse

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from ..forms import BookForm, cancelEventForm, EditEventForm
from ..decorators import lead_started, parent_required
from django.contrib import messages
from django.http import Http404

from django.conf import settings
import pytz

from ..utils import check_inquiry_reopen, check_parent_book_event_allowed

from general_tasks.utils import EventPDFExport
import datetime
from django.http import FileResponse

import logging

from ..helpers import create_event_date_dict, event_date_dict_add_book_information

parent_decorators = [login_required, parent_required]


@method_decorator(login_required, name="dispatch")
class AnnouncementsAllUsers(ListView):
    model = Announcements

    template_name = "dashboard/announcements/announcements_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super(AnnouncementsAllUsers, self).get_queryset(*args, **kwargs)
        qs = qs.filter(Q(user=self.request.user), Q(read=False))
        qs = qs.order_by("-created")
        return qs


@login_required
def markAllAnnouncementsRead(request):
    announcements = Announcements.objects.filter(Q(user=request.user), Q(read=False))
    for announcement in announcements:
        announcement.read = True
        announcement.save()
    messages.success(request, _("All notifications have been marked as read."))
    return redirect("..")


@login_required
def markAnnouncementRead(request, announcement_id):
    announcement = get_object_or_404(
        Announcements,
        id__exact=force_str(urlsafe_base64_decode(announcement_id)),
        user=request.user,
    )
    announcement.read = True
    announcement.save()
    return redirect("..")
