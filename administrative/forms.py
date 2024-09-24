from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.utils.translation import gettext as _
from .models import *
from dashboard.models import SiteSettings
from authentication.models import Student, CustomUser, StudentChange
from dashboard.models import (
    EventChangeFormula,
    Event,
    DayEventGroup,
    TeacherEventGroup,
    BaseEventGroup,
)
from authentication.models import CustomUser, Tag, Student
from django.utils import timezone
from django.db.models import Q

from crispy_forms.helper import FormHelper

from django.contrib.auth.password_validation import validate_password
from django.core import validators
from django.core.exceptions import ValidationError

from .forms_helpers import get_students_choices_for_event
from .tasks import *


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class TeacherImportForm(forms.Form):
    csv_file = forms.FileField(required=False)
    teacher_email = forms.EmailField(required=False)


class AdminStudentEditForm(forms.Form):
    first_name = forms.CharField(label=_("First name"), max_length=48)
    last_name = forms.CharField(label=_("Last name"), max_length=48)
    child_email = forms.EmailField(label=_("Child emails"), max_length=200)
    class_name = forms.CharField(label=_("Name of class"), max_length=4)


class EventChangeFormularForm(forms.Form):
    teacher = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role=1), widget=forms.CheckboxSelectMultiple
    )


class EventAddNewDateForm(forms.Form):
    base_event = forms.ModelChoiceField(
        queryset=BaseEventGroup.objects.filter(valid_until__gte=timezone.now().date()),
        empty_label="Neues Base Event erstellen",
        required=False,
    )
    date = forms.DateField()
    teacher = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role=1), widget=forms.CheckboxSelectMultiple
    )
    lead_start = forms.DateField()
    lead_inquiry_start = forms.DateField()


class EventChangeFormulaEditForm(forms.ModelForm):
    class Meta:
        model = EventChangeFormula
        fields = (
            "start_time",
            "end_time",
            "no_events",
        )

    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"class": "timepicker"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"class": "timepicker"}))

    def save(self, commit=True):
        self.instance.status = 1
        if not self.cleaned_data.get("no_events"):
            self.instance.start_time = self.cleaned_data.get("start_time")
            self.instance.end_time = self.cleaned_data.get("end_time")
        else:
            self.instance.no_events = True
        self.instance.save()
        return super(EventChangeFormulaEditForm, self).save(commit=commit)


class ParentEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "students",
            "email",
            "is_active",
        )

    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects, widget=forms.SelectMultiple
    )


class TeacherEditForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=48)
    last_name = forms.CharField(max_length=48)
    acronym = forms.CharField(max_length=3)
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)
    image = forms.ImageField(required=False)


class SettingsEditForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ("",)


class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ("teacher_event_group", "day_group", "teacher", "start", "end")

    def save(self, commit=True):
        instance: Event = self.instance

        if "lead_status" in self.changed_data:
            instance.lead_manual_override = True

        if commit:
            instance.save()

        return instance


class EventAddStudentForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = []

    add_student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(EventAddStudentForm, self).__init__(*args, **kwargs)

        if self.instance.parent:
            choices = get_students_choices_for_event(event=self.instance)

            if choices.__len__() == 0:
                print("Test")
                self.fields["add_student"].widget = self.fields[
                    "add_student"
                ].hidden_widget()

            self.fields["add_student"].choices = choices

    def clean_add_student(self):
        instance = self.instance

        data = self.cleaned_data["add_student"]

        if instance.parent and data and not data in instance.parent.students.all():
            raise ValidationError(
                "The specified student does not belong to the same parent as an already specified student. Please only choose students linked to the same parent account."
            )

        return data

    def save(self, commit=True):
        instance: Event = self.instance

        if "add_student" in self.changed_data:
            add_student = self.cleaned_data["add_student"]

            instance.student.add(add_student)
            if CustomUser.objects.filter(Q(role=0), Q(students=add_student)).exists():
                instance.parent = CustomUser.objects.get(
                    Q(role=0), Q(students=add_student)
                )

            instance.occupied = True
            instance.status = 1

        if commit:
            instance.save()

        return instance


class ControlParentCreationForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=48)
    last_name = forms.CharField(max_length=48)

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
                "autocomplete": "off",
            }
        ),
        validators=[validate_password],
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirrm password",
                "autocomplete": "off",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"]

        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(
                "This email is already taken. Please provide a different one."
            )

        return email

    def clean(self):
        password = self.cleaned_data["password"]
        confirm_password = self.cleaned_data["confirm_password"]

        if password != confirm_password:
            self.add_error(
                "password", "The password and the confirm password must be equal."
            )
            self.add_error(
                "confirm_password",
                "The password and the confirm password must be equal.",
            )


class ControlParentAddStudent(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(queryset=CustomUser.objects.filter(Q(role=0)))


class EditStudentChangesForm(forms.ModelForm):
    class Meta:
        model = StudentChange
        exclude = ("applied", "approved", "applied_time")

    shield_id = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    child_email = forms.EmailField(required=False)
    created = forms.DateTimeField(disabled=True)
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), disabled=True, required=False
    )

    apply = forms.BooleanField(required=False)

    def save(self, commit=True):
        instance = self.instance
        apply = self.cleaned_data["apply"]

        if commit:
            instance.save()

        if apply:
            apply_and_approve_student_changes.delay([instance.pk])
        return instance
