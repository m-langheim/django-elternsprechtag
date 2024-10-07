from dataclasses import field
from django import forms
from django.db.models import Q
from dashboard.models import (
    Student,
    Event,
    EventChangeFormula,
    BaseEventGroup,
    DayEventGroup,
    TeacherEventGroup,
)
from authentication.models import CustomUser, Tag, TeacherExtraData
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db.models import F
from .helpers import AbsoluteDifference


class createInquiryForm(forms.Form):
    base_event = forms.ModelChoiceField(
        queryset=BaseEventGroup.objects.filter(valid_until__gte=timezone.now()),
        label="",
    )
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=0), disabled=True
    )
    reason = forms.CharField(
        widget=forms.Textarea,
        required=False,
        max_length=4000,
        help_text=_("The text must not be longer than 4000 characters."),
    )

    def __init__(self, *args, **kwargs):
        super(createInquiryForm, self).__init__(*args, **kwargs)
        self.fields["reason"].label = False
        self.initial["base_event"] = (
            BaseEventGroup.objects.filter(lead_start__gte=timezone.now())
            .order_by("lead_start")
            .first()
        )


class editInquiryForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=0), disabled=True
    )
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(Q(occupied=True)), disabled=True, required=False
    )
    reason = forms.CharField(
        widget=forms.Textarea,
        required=False,
        max_length=4000,
        help_text=_("The text must not be longer than 4000 characters."),
    )

    def __init__(self, *args, **kwargs):
        super(editInquiryForm, self).__init__(*args, **kwargs)
        self.fields["reason"].label = False


class changePasswordForm(PasswordChangeForm):
    change_password = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit("submit", "Ändern"))


class cancelEventForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea,
        label=_("Explanation why you dismiss the event:"),
        max_length=4000,
    )
    book_other_event = forms.BooleanField(
        initial=False, required=False, label=_("Parent should book a different event.")
    )
    cancel_event = forms.BooleanField(widget=forms.HiddenInput, initial=True)


class EventChangeFormulaPeriodForm(forms.ModelForm):
    class Meta:
        model = EventChangeFormula
        fields = ["start_time", "end_time", "no_events"]

    def __init__(self, *args, **kwargs):
        super(EventChangeFormulaPeriodForm, self).__init__(*args, **kwargs)
        self.fields["start_time"].widget = forms.TimeInput(attrs={"type": "time"})
        self.fields["end_time"].widget = forms.TimeInput(attrs={"type": "time"})
        self.fields["start_time"].label = False
        self.fields["end_time"].label = False
        self.fields["no_events"].label = "An diesem Tag habe ich keine Termine"

    def clean(self):
        super(EventChangeFormulaPeriodForm, self).clean()

        print(self.cleaned_data)

        start_time = self.cleaned_data.get("start_time")
        end_time = self.cleaned_data.get("end_time")
        no_events = self.cleaned_data.get("no_events")

        if not no_events:
            if not start_time:
                self._errors["start_time"] = self.error_class(
                    ["Bitte eine gültige Uhrzeit eingeben."]
                )
            if not end_time:
                self._errors["end_time"] = self.error_class(
                    ["Bitte eine gültige Uhrzeit eingeben."]
                )
            if start_time and end_time:
                if start_time > end_time:
                    self._errors["end_time"] = self.error_class(
                        [
                            "Bitte wählen Sie einen Startzeitpunkt, der vor dem Endzeitpunkt liegt."
                        ]
                    )
        else:
            if start_time or end_time:
                self._errors["no_events"] = self.error_class(
                    ["Bitte entweder eine Uhrzeit angeben oder dieses Feld ausfüllen."]
                )
        return self.cleaned_data

    def save(self):
        data = self.cleaned_data
        instance = self.instance

        time_start = data.get("start_time")
        time_end = data.get("end_time")
        no_events = data.get("no_events")

        instance.status = 1
        instance.start_time = time_start
        instance.end_time = time_end
        instance.no_events = no_events
        instance.save()


class EventChangeFormulaBreakForm(forms.ModelForm):
    class Meta:
        model = EventChangeFormula
        fields = ["start_time", "end_time"]

    def __init__(self, *args, **kwargs):
        super(EventChangeFormulaBreakForm, self).__init__(*args, **kwargs)
        self.fields["start_time"].widget = forms.TimeInput(attrs={"type": "time"})
        self.fields["end_time"].widget = forms.TimeInput(attrs={"type": "time"})
        self.fields["start_time"].label = False
        self.fields["end_time"].label = False

    def clean_start_time(self):
        start_time = self.cleaned_data["start_time"]

        start_datetime = timezone.datetime.combine(
            date=self.instance.day_group.date, time=start_time
        )

        print(start_datetime)

        if not Event.objects.filter(
            Q(teacher_event_group=self.instance.teacher_event_group),
            Q(start=start_datetime),
        ).exists():
            nearest = (
                Event.objects.filter(
                    Q(teacher_event_group=self.instance.teacher_event_group)
                )
                .annotate(distance=AbsoluteDifference(F("start") - start_datetime))
                .order_by("distance")
            )
            print(nearest.first())
            self.add_error(
                "start_time",
                f"The start time must match an events start time. The nearest start time is {nearest.first().end.timetz()}",
            )
        return start_time

    def clean_end_time(self):
        start_time = self.cleaned_data["start_time"]
        end_time = self.cleaned_data["end_time"]

        start_datetime = timezone.datetime.combine(
            date=self.instance.day_group.date, time=start_time
        )
        end_datetime = timezone.datetime.combine(
            date=self.instance.day_group.date, time=end_time
        )

        if end_time < start_time:
            self.add_error("end_time", "The end time must be set after the start time.")
        elif end_time == start_time:
            self.add_error("end_time", "The end time can´t be equal to the start time.")
        if not Event.objects.filter(
            Q(teacher_event_group=self.instance.teacher_event_group),
            Q(end=end_datetime),
        ).exists():
            nearest = (
                Event.objects.filter(
                    Q(teacher_event_group=self.instance.teacher_event_group)
                )
                .annotate(distance=AbsoluteDifference(F("end") - end_datetime))
                .order_by("distance")
            )
            print(nearest.first())
            self.add_error(
                "end_time",
                f"The end time must match an events end time. The nearest end time is {nearest.first().end.timetz()}",
            )
        return end_time

    def save(self):
        data = self.cleaned_data
        instance = self.instance

        time_start = data.get("start_time")
        time_end = data.get("end_time")

        instance.status = EventChangeFormula.FormularStatusChoices.PENDING_CONFIRMATION
        instance.type = EventChangeFormula.FormularTypeChoices.BREAKS
        instance.start_time = time_start
        instance.end_time = time_end
        instance.save()


class BreakFormularCreationForm(forms.Form):
    day_group = forms.ModelChoiceField(
        queryset=DayEventGroup.objects.filter(date__gte=timezone.now()),
        initial=DayEventGroup.objects.filter(date__gte=timezone.now()).first(),
        label=_("Day group"),
        help_text=_(
            "Please choose for which date you want to create the break request."
        ),
    )
    start_time = forms.TimeField(label=_("Start time"))
    end_time = forms.TimeField(label=_("End time"))


class SichLeaveForm(forms.ModelForm):
    class Meta:
        model = EventChangeFormula
        fields = ["day_group", "start_time", "end_time", "no_events"]

    day_group = forms.ModelChoiceField(
        queryset=DayEventGroup.objects.filter(date__gte=timezone.now()),
        initial=DayEventGroup.objects.filter(date__gte=timezone.now()).first(),
        label=_("Day group"),
        help_text=_(
            "Please choose for which date you want to create the break request."
        ),
    )

    def __init__(self, teacher, *args, **kwargs):
        super(SichLeaveForm, self).__init__(*args, **kwargs)

        self.teacher = teacher

    def clean_no_events(self):
        no_events = self.cleaned_data.get("no_events", False)

        if not no_events:
            if not self.cleaned_data["start_time"]:
                self.add_error(
                    "start_time",
                    "If you do not request sick leave for all events, you have to specify a start time.",
                )
            if not self.cleaned_data["end_time"]:
                self.add_error(
                    "end_time",
                    "If you do not request sick leave for all events, you have to specify a start time.",
                )
        else:
            if self.cleaned_data["start_time"]:
                self.add_error(
                    "start_time",
                    "When you request sick leave only the whole day or a specific time period can be requested. Not both at the same time.",
                )
            if self.cleaned_data["end_time"]:
                self.add_error(
                    "end_time",
                    "When you request sick leave only the whole day or a specific time period can be requested. Not both at the same time.",
                )
            # if self.cleaned_data["start_time"] or self.cleaned_data["end_time"]:
            #     self.add_error(
            #         "no_events",
            #         "When you request sick leave only the whole day or a specific time period can be requested. Not both at the same time.",
            #     )

        return no_events

    def save(self, commit=True):
        instance = self.instance
        day_group = self.cleaned_data["day_group"]

        instance.teacher = self.teacher
        instance.type = EventChangeFormula.FormularTypeChoices.ILLNESS
        instance.day_group = day_group
        instance.teacher_event_group = TeacherEventGroup.objects.get(
            Q(day_group=day_group), Q(teacher=self.teacher)
        )
        instance.date = day_group.date
        instance.start_time = self.cleaned_data["start_time"]
        instance.end_time = self.cleaned_data["end_time"]
        instance.no_events = self.cleaned_data["no_events"]

        instance.status = EventChangeFormula.FormularStatusChoices.PENDING_CONFIRMATION

        if commit:
            instance.save()
