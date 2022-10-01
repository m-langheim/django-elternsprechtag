from django import forms
from django.db.models import Q
from dashboard.models import Student, Event
from authentication.models import CustomUser, Tag
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.forms import PasswordChangeForm


class createInquiryForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=0), disabled=True)
    reason = forms.CharField(widget=forms.Textarea, required=False)


class editInquiryForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=0), disabled=True)
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(Q(occupied=True)), disabled=True, required=False)
    reason = forms.CharField(widget=forms.Textarea, required=False)


class changeProfileForm(forms.ModelForm):
    change_profile = forms.BooleanField(
        widget=forms.HiddenInput, initial=True)  # field to identify the form

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Speichern'))


class configureTagsForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects)


class changePasswordForm(PasswordChangeForm):
    change_password = forms.BooleanField(
        widget=forms.HiddenInput, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Ändern'))
