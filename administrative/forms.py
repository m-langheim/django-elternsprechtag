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
from dashboard.models import EventChangeFormula
from authentication.models import CustomUser, Tag
from django.utils import timezone
from django.db.models import Q

from crispy_forms.helper import FormHelper


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


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


class TeacherEditForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=48)
    last_name = forms.CharField(max_length=48)
    acronym = forms.CharField(max_length=3)
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all())
    image = forms.ImageField(required=False)
