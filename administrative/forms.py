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
from dashboard.models import EventChangeFormula
from authentication.models import CustomUser, Tag, Student
from django.utils import timezone
from django.db.models import Q

from crispy_forms.helper import FormHelper


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
    date = forms.DateField(initial=timezone.datetime.now().date, widget=forms.DateInput)


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
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all())
    image = forms.ImageField(required=False)


class SettingsEditForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ("",)
