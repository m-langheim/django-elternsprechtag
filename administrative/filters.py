import django_filters
from dashboard.models import Event
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit
from dashboard.models import BaseEventGroup, Event
from django.utils import timezone
from django import forms
from custom_backup.models import *


class EventFilter(django_filters.FilterSet):

    class Meta:
        model = Event
        fields = [
            "teacher",
            "status",
            "lead_status",
        ]

    status = django_filters.MultipleChoiceFilter(
        choices=Event.STATUS_CHOICES, widget=forms.CheckboxSelectMultiple
    )
    lead_status = django_filters.MultipleChoiceFilter(
        choices=Event.LEAD_STATUS_CHOICES, widget=forms.CheckboxSelectMultiple
    )


class EventFilterFormHelper(FormHelper):
    form_method = "GET"
    layout = ("teacher", "start", Submit("submit", "Filter"))


class BackupFilter(django_filters.FilterSet):
    class Meta:
        model = Backup
        fields = ["backup_type"]
