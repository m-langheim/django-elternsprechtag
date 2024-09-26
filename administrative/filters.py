import django_filters
from dashboard.models import Event, LeadStatusChoices
from authentication.models import CustomUser
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

    teacher = django_filters.ModelChoiceFilter(
        queryset=CustomUser.objects.filter(role=1),
        label="",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )

    status = django_filters.MultipleChoiceFilter(
        choices=Event.StatusChoices,
        widget=forms.CheckboxSelectMultiple(),
        label="",
    )
    lead_status = django_filters.MultipleChoiceFilter(
        choices=LeadStatusChoices, widget=forms.CheckboxSelectMultiple(), label=""
    )


class EventFilterFormHelper(FormHelper):
    form_method = "GET"
    layout = ("teacher", "start", Submit("submit", "Filter"))


class BackupFilter(django_filters.FilterSet):
    class Meta:
        model = Backup
        fields = ["backup_type"]
