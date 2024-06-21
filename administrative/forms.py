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
from django.db.models import Q

from crispy_forms.helper import FormHelper


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
