from typing import Any
from django import forms
from .models import (
    Student,
    Inquiry,
    SiteSettings,
    Event,
    DayEventGroup,
    TeacherEventGroup,
)
from authentication.models import CustomUser
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import *


class StudentSelector(forms.CheckboxSelectMultiple):
    def __init__(self, *args, **kwargs):
        self.active_choices = kwargs.pop("active_choices", [])
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        option["attrs"]["disabled"] = value not in self.active_choices
        return option


class BookForm(forms.Form):
    # book_event = forms.BooleanField(initial=True, widget=forms.HiddenInput) Sieht irrelevant und nicht mehr genutzt aus -> wird deshalb vorerst rausgenommen

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.inquiry: Inquiry = kwargs.pop("inquiry", None)
        self.instance: Event = kwargs.pop("instance")
        super(BookForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_show_errors = False

        teacher = self.instance.teacher
        #  Es werden immer alle Schüler:innen, die zu dem Elternteil gehören angezeigt
        choices = []
        for student in self.request.user.students.all():
            choices.append([student.id, student.first_name + " " + student.last_name])

        # Hier wird jetzt gefiltert, ob noch ein Schüler:in offen ist, bei der noch kein Termin für diesen Lehrer eingetragen ist
        students_with_event = Event.objects.filter(
            Q(teacher=teacher),
            Q(occupied=True),
            Q(parent=self.request.user),
            Q(
                day_group__in=DayEventGroup.objects.filter(
                    base_event=self.instance.get_base_event()
                )
            ),
        ).values_list("student", flat=True)

        active_choices = [
            student[0] if student[0] not in students_with_event else None
            for student in choices
        ]

        necessary_choices = []

        if self.inquiry:
            # If an inquiry is provided, one of the inquiry students (should be limited to one) must be selected. Other students can be selected in addition.
            for student in self.inquiry.students.all():
                choices.remove(
                    [student.id, student.first_name + " " + student.last_name]
                )
                active_choices.remove(student.id)
                self.fields["necessary_student"].widget = self.fields[
                    "necessary_student"
                ].hidden_widget()
        elif self.instance.lead_status == 2:  # lead not started yet
            inquiries = Inquiry.objects.filter(
                Q(type=0),
                Q(requester=teacher),
                Q(respondent=self.request.user),
                Q(base_event=self.instance.get_base_event()),
            )
            for inquiry in inquiries:
                for student in inquiry.students.all():
                    necessary_choices.append(
                        [student.id, student.first_name + " " + student.last_name]
                    )
                    choices.remove(
                        [student.id, student.first_name + " " + student.last_name]
                    )
        else:
            self.fields["necessary_student"].widget = self.fields[
                "necessary_student"
            ].hidden_widget()

        self.fields["student"].choices = choices
        self.fields["student"].widget.active_choices = active_choices
        self.fields["necessary_student"].choices = necessary_choices
        self.fields["necessary_student"].widget.active_choices = active_choices

    def clean(self):
        cleaned_data = super().clean()
        # Manually include initial values if they are not provided by the user
        student = cleaned_data["student"]
        necessary_student = cleaned_data["necessary_student"]

        all_students: list = student + necessary_student

        if self.inquiry:
            all_students += [str(student.id) for student in self.inquiry.students.all()]
        elif self.instance.lead_status == 2 and len(necessary_student) == 0:
            self.add_error(
                "necessary_student", _("One of the marked students must be selected.")
            )
        if len(all_students) == 0:
            raise ValidationError(_("At least one student must be selected."))
        cleaned_data["all_students"] = all_students
        return cleaned_data

    necessary_student = forms.MultipleChoiceField(
        choices=[],
        widget=StudentSelector(),
        label="",
        required=False,
    )

    student = forms.MultipleChoiceField(
        choices=[],
        widget=StudentSelector(),
        label="",
        required=False,
    )


class EditEventForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.instance: Event = kwargs.pop("instance")
        super(EditEventForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_show_errors = False

        teacher = self.instance.teacher
        #  Es werden immer alle Schüler:innen, die zu dem Elternteil gehören angezeigt
        choices = []
        for student in self.request.user.students.all():
            choices.append([student.id, student.first_name + " " + student.last_name])

        # Hier wird jetzt gefiltert, ob noch ein Schüler:in offen ist, bei der noch kein Termin für diesen Lehrer eingetragen ist
        students_with_event = (
            Event.objects.filter(
                Q(teacher=teacher),
                Q(occupied=True),
                Q(parent=self.request.user),
                Q(
                    day_group__in=DayEventGroup.objects.filter(
                        base_event=self.instance.get_base_event()
                    )
                ),
            )
            .exclude(id=self.instance.id)
            .values_list("student", flat=True)
        )

        active_choices = [
            student[0] if student[0] not in students_with_event else None
            for student in choices
        ]

        necessary_choices = []

        if self.instance.lead_status == 2:  # lead not started yet
            inquiries = Inquiry.objects.filter(
                Q(type=0),
                Q(requester=teacher),
                Q(respondent=self.request.user),
                Q(base_event=self.instance.get_base_event()),
            )
            for inquiry in inquiries:
                for student in inquiry.students.all():
                    necessary_choices.append(
                        [student.id, student.first_name + " " + student.last_name]
                    )
                    choices.remove(
                        [student.id, student.first_name + " " + student.last_name]
                    )
        else:
            self.fields["necessary_student"].widget = self.fields[
                "necessary_student"
            ].hidden_widget()

        self.fields["student"].choices = choices
        self.fields["student"].initial = [
            (str(student.id))
            for student in self.instance.student.all()
            if [student.id, student.first_name + " " + student.last_name] in choices
        ]
        self.fields["student"].widget.active_choices = active_choices
        self.fields["necessary_student"].choices = necessary_choices
        self.fields["necessary_student"].initial = [
            (str(student.id))
            for student in self.instance.student.all()
            if [student.id, student.first_name + " " + student.last_name]
            in necessary_choices
        ]
        self.fields["necessary_student"].widget.active_choices = active_choices

    def clean(self):
        cleaned_data = super().clean()
        # Manually include initial values if they are not provided by the user
        student = cleaned_data.get("student")
        necessary_student = cleaned_data.get("necessary_student", [])
        # necessary_student = []

        all_students: list = student + necessary_student

        if self.instance.lead_status == 2 and len(necessary_student) == 0:
            self.add_error(
                "necessary_student", _("One of the marked students must be selected.")
            )
        if len(all_students) == 0:
            raise ValidationError(_("At least one student must be selected."))
        cleaned_data["all_students"] = all_students
        return cleaned_data

    necessary_student = forms.MultipleChoiceField(
        choices=[],
        widget=StudentSelector(),
        label="",
        required=False,
    )

    student = forms.MultipleChoiceField(
        choices=[],
        widget=StudentSelector(),
        label="",
        required=False,
    )


class AdminEventForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role=1))
    date = forms.DateField(widget=forms.SelectDateWidget())
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"class": "timepicker"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"class": "timepicker"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit("submit", _("Save")))


class AdminEventCreationFormulaForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role=1))
    date = forms.DateField(
        widget=forms.SelectDateWidget(), initial=timezone.datetime.now().date
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit("submit", _("Save")))


class cancelEventForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea,
        max_length=4000,
        help_text=_("The text must not be longer than 4000 characters."),
        label=_("Reason for cancellation:"),
    )


class EventCreationForm(forms.BaseInlineFormSet):
    class Meta:
        model = Event
        fields = ["teacher", "start", "end"]

    teacher = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=1), required=True
    )
    start = forms.DateTimeField(required=True)
    end = forms.DateTimeField(required=True)
    lead_start = forms.DateField(required=False)
    lead_inquiry_start = forms.DateField(required=False)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super(EventCreationForm, self).clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        lead_start = cleaned_data.get("lead_start")
        lead_inquiry_start = cleaned_data.get("lead_inquiry_start")
        if start > end:
            self.add_error("end", _("The end time must be later than the start time."))
        if lead_start > start:
            self.add_error(
                "lead_start",
                _(
                    "The start time of the booking phase must be before the start of the appointments."
                ),
            )
        if lead_start > lead_inquiry_start:
            self.add_error(
                "lead_inquiry_start",
                _(
                    "The starting time of answering enquiries must be before the start time of the booking phase."
                ),
            )
        return cleaned_data

    def save(self):
        teacher = self.cleaned_data["teacher"]
        start = self.cleaned_data["start"]
        end = self.cleaned_data["end"]

        if self.cleaned_data["lead_start"] and self.cleaned_data["lead_inquiry_start"]:
            lead_start = self.cleaned_data["lead_start"]
            lead_inquiry_start = self.cleaned_data["lead_inquiry_start"]
        else:
            lead_start = start.date() - timezone.timedelta(days=7)
            lead_inquiry_start = start.date() - timezone.timedelta(days=14)

        day_group = DayEventGroup.objects.get_or_create(
            Q(date=start.date()),
            Q(lead_start=lead_start),
            Q(lead_inquiry_start=lead_inquiry_start),
        )
        teacher_event_group = TeacherEventGroup.objects.get_or_create(
            Q(teacher=self.cleaned_data["teacher"]),
            Q(day_group=day_group),
            Q(lead_start=lead_start),
            Q(lead_inquiry_start=lead_inquiry_start),
        )
        event = Event.objects.create(
            day_group=day_group,
            teacher_event_group=teacher_event_group,
            teacher=teacher,
            start=start,
            end=end,
        )
        event.save()

        return event
