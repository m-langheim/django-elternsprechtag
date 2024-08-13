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

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class StudentSelector(forms.CheckboxSelectMultiple):
    def __init__(self, *args, **kwargs):
        self.active_choices = kwargs.pop("active_choices", [])
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        option["attrs"]["disabled"] = value not in self.active_choices
        return option


class BookForm(forms.Form):  # * Hier wurde einiges verändert
    book_event = forms.BooleanField(initial=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.teacher = kwargs.pop("teacher")
        super(BookForm, self).__init__(*args, **kwargs)

        #  Es werden immer alle Schüler:innen, die zu dem Elternteil gehören angezeigt
        choices = []
        for student in self.request.user.students.all():
            choices.append([student.id, student.first_name + " " + student.last_name])

        active_choices = []

        # ! Muss nochmal getestet werden
        if (
            SiteSettings.objects.all().first().lead_start > timezone.now().date()
        ):  # lead not started yet
            inquiries = Inquiry.objects.filter(
                Q(type=0),
                Q(requester=self.teacher),
                Q(respondent=self.request.user),
                Q(event=None),
                Q(processed=False),
            )

            active_choices = [
                student for student in inquiries.values_list("students", flat=True)
            ]  # Alle Schüler, die in einer Anfrage stehen werden auf aktiv gesetzt
        else:
            # Hier wird jetzt gefiltert, ob noch ein Schüler:in offen ist, bei der noch kein Termin für diesen Lehrer eingetragen ist
            students_with_event = Event.objects.filter(
                Q(teacher=self.teacher), Q(occupied=True), Q(parent=self.request.user)
            ).values_list("student", flat=True)
            for student in choices:
                if student[0] not in students_with_event:
                    active_choices.append(student[0])

        self.fields["student"].choices = choices
        self.fields["student"].widget.active_choices = active_choices

    student = forms.MultipleChoiceField(choices=[], widget=StudentSelector(), label="")


class EditEventForm(forms.Form):
    edit_event = forms.BooleanField(initial=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        self.teacher = kwargs.pop("teacher")
        self.event = kwargs.pop("event")
        super(EditEventForm, self).__init__(*args, **kwargs)

        #  Es werden immer alle Schüler:innen, die zu dem Elternteil gehören angezeigt
        choices = []
        for student in self.request.user.students.all():
            choices.append([student.id, student.first_name + " " + student.last_name])

        active_choices = []
        if (
            SiteSettings.objects.all().first().lead_start > timezone.now().date()
        ):  # lead not started yet
            # Es sollen nur Schüler:innen auswählbar sein, bei denen eine Anfrage vorliegt
            inquiries = Inquiry.objects.filter(
                Q(type=0), Q(requester=self.teacher), Q(respondent=self.request.user)
            )

            active_choices = [
                student for student in inquiries.values_list("students", flat=True)
            ]  # Alle Schüler, die in einer Anfrage stehen werden auf aktiv gesetzt
        else:
            # Hier wird jetzt gefiltert, ob noch ein Schüler:in offen ist, bei der noch kein Termin für diesen Lehrer eingetragen ist
            students_with_event = (
                Event.objects.filter(
                    Q(teacher=self.teacher),
                    Q(occupied=True),
                    Q(parent=self.request.user),
                )
                .exclude(id=self.event.id)
                .values_list("student", flat=True)
            )
            for student in choices:
                if student[0] not in students_with_event:
                    active_choices.append(student[0])

        self.fields["student"].choices = choices
        self.fields["student"].widget.active_choices = active_choices

    student = forms.MultipleChoiceField(
        choices=[], widget=StudentSelector(), label="", required=True
    )


# class InquiryForm(forms.Form): #? Irrelevant, da es ein überarbeitetes Interface zum beantworten von Anfragen gibt?
#     def __init__(self, *args, **kwargs):
#         self.request = kwargs.pop('request')
#         self.selected_student = kwargs.pop('selected_student')
#         self.teacher = kwargs.pop('teacher')
#         self.parent = kwargs.pop('parent')
#         super(InquiryForm, self).__init__(*args, **kwargs)

#         self.fields['student'].queryset = self.request.user.students.all()
#         self.fields['student'].initial = self.selected_student()
#         self.fields['event'].queryset = Event.objects.filter(
#             Q(teacher=self.teacher), Q(occupied=False))

#     def clean(self):
#         cleaned_data = super(InquiryForm, self).clean()
#         students = cleaned_data.get('student')
#         if not self.selected_student() in students:
#             self.add_error(
#                 'student', "The default selected student needs to stay selected")

#         return cleaned_data

#     event = forms.ModelChoiceField(queryset=None)
#     student = forms.ModelMultipleChoiceField(
#         queryset=None, widget=forms.CheckboxSelectMultiple)

# Admin Form


class AdminEventForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role=1))
    date = forms.DateField(widget=forms.SelectDateWidget())
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"class": "timepicker"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"class": "timepicker"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit("submit", "Speichern"))


class AdminEventCreationFormulaForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role=1))
    date = forms.DateField(
        widget=forms.SelectDateWidget(), initial=timezone.datetime.now().date
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit("submit", "Speichern"))


class cancelEventForm(forms.Form):
    cancel_event = forms.BooleanField(initial=True, widget=forms.HiddenInput)
    message = forms.CharField(
        widget=forms.Textarea,
        max_length=4000,
        help_text="Der Text darf nicht länger als 4000 Zeichen sein.",
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
            self.add_error(
                "end", "The events end time must be later than the event start time."
            )
        if lead_start > start:
            self.add_error(
                "lead_start", "The lead start must be set before the event start."
            )
        if lead_start > lead_inquiry_start:
            self.add_error(
                "lead_inquiry_start",
                "The lead inquiry field is designed to be set before the lead start value.",
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
