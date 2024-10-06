import django_tables2 as tables
from django_tables2.utils import Accessor
from authentication.models import Student, StudentChange, CustomUser, Tag
from dashboard.models import (
    Event,
    EventChangeFormula,
    BaseEventGroup,
    DayEventGroup,
    TeacherEventGroup,
)
from django.utils.html import format_html
from django.template.loader import render_to_string
from custom_backup.models import *
from django.utils.translation import gettext as _
from django_tables2.utils import A
from django.urls import reverse_lazy


class EventStatusColumn(tables.Column):
    def render(self, value):
        event = Event.objects.get(pk=value)

        return format_html(
            render_to_string(
                "teacher/tables/event_status_column.html", {"event": event}
            )
        )


class EventActionsColumn(tables.Column):
    def render(self, value):
        event = Event.objects.get(pk=value)

        return format_html(
            render_to_string(
                "teacher/tables/event_actions_column.html", {"event": event}
            )
        )


class PersonalEventsTable(tables.Table):
    class Meta:
        model = Event
        fields = ["start", "end", "parent"]

    start = tables.TimeColumn(
        verbose_name=_("Start"), orderable=True, attrs={"th": {"id": "start_id"}}
    )
    end = tables.TimeColumn(verbose_name=_("End"), orderable=False)
    parent = tables.Column(orderable=False)
    status = EventStatusColumn(accessor="pk", orderable=False)
    actions = EventActionsColumn(
        accessor="pk",
        orderable=False,
        verbose_name="",
        attrs={"td": {"align": "right"}},
    )
