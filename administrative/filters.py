import django_filters
from dashboard.models import Event, LeadStatusChoices, BaseEventGroup
from authentication.models import CustomUser
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit
from dashboard.models import BaseEventGroup, Event, TeacherEventGroup, DayEventGroup
from authentication.models import Student
from django.utils import timezone
from django import forms
from custom_backup.models import *

from django_select2 import forms as s2forms


class TeacherWidget(s2forms.ModelSelect2Widget):
    model = CustomUser
    search_fields = [
        "first_name__icontains",
        "last_name__icontains",
        "email__icontains",
    ]


class EventFilter(django_filters.FilterSet):

    class Meta:
        model = Event
        fields = ["teacher", "status", "lead_status", "base_event", "day_group"]

    teacher = django_filters.ModelChoiceFilter(
        queryset=CustomUser.objects.filter(role=1),
        label="",
        widget=TeacherWidget(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )

    base_event = django_filters.ModelChoiceFilter(
        queryset=BaseEventGroup.objects.all(), label=""
    )
    day_group = django_filters.ModelChoiceFilter(
        queryset=DayEventGroup.objects.all(), label=""
    )

    status = django_filters.MultipleChoiceFilter(
        choices=Event.StatusChoices,
        widget=forms.CheckboxSelectMultiple(),
        label="",
    )
    lead_status = django_filters.MultipleChoiceFilter(
        choices=LeadStatusChoices, widget=forms.CheckboxSelectMultiple(), label=""
    )


class TeacherEventGroupFilter(django_filters.FilterSet):

    class Meta:
        model = TeacherEventGroup
        fields = ["teacher", "lead_status", "day_group"]

    teacher = django_filters.ModelChoiceFilter(
        queryset=CustomUser.objects.filter(role=1),
        label="",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )

    # status = django_filters.MultipleChoiceFilter(
    #     choices=Event.StatusChoices,
    #     widget=forms.CheckboxSelectMultiple(),
    #     label="",
    # )
    lead_status = django_filters.MultipleChoiceFilter(
        choices=LeadStatusChoices, widget=forms.CheckboxSelectMultiple(), label=""
    )

    day_group = django_filters.ModelChoiceFilter(
        label="", queryset=DayEventGroup.objects.all()
    )

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)

        self.filters["day_group"].queryset = DayEventGroup.objects.filter(
            pk__in=list(queryset.all().values_list("day_group", flat=True))
        )


class EventFilterFormHelper(FormHelper):
    form_method = "GET"
    layout = ("teacher", "start", Submit("submit", "Filter"))


class BackupFilter(django_filters.FilterSet):
    class Meta:
        model = Backup
        fields = ["backup_type"]


class StudentFilter(django_filters.FilterSet):
    class Meta:
        model = Student
        fields = ["class_name"]
