from typing import Dict
from django.shortcuts import render, redirect
from authentication.models import StudentChange, CustomUser, Upcomming_User
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.contrib.auth.password_validation import password_validators_help_text_html
from django.urls import reverse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404

import datetime

from .forms import *
from .tasks import *
from .utils import *
from .tables import *
from .filters import *
from .forms_helpers import get_students_choices_for_event
from django_tables2 import SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from general_tasks.tasks import async_send_mail

from django.contrib.admin.views.decorators import staff_member_required

from dashboard.models import (
    Event,
    EventChangeFormula,
    Announcements,
    Inquiry,
    DayEventGroup,
    TeacherEventGroup,
)
from dashboard.tasks import async_create_events_special, apply_event_change_formular

from dashboard.utils import check_inquiry_reopen

import csv, io, os

from django.utils.decorators import method_decorator


def get_event_creation_modal_context():
    structure_context = []
    for base in BaseEventGroup.objects.filter(valid_until__gte=timezone.now()):
        date_context = []
        for date in DayEventGroup.objects.filter(
            date__gte=timezone.now(), base_event=base
        ).order_by("date"):
            date_context.append(
                {
                    "date": date.date,
                    "id": force_str(urlsafe_base64_encode(force_bytes(date.id))),
                }
            )
        structure_context.append(
            {
                "name": base.__str__,
                "id": force_str(urlsafe_base64_encode(force_bytes(base.pk))),
                "dates": date_context,
                "add_new_date_form": EventAddNewDateForm(initial={"base_event": base}),
            }
        )

    return structure_context
