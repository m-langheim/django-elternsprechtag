from dataclasses import field
from django import forms
from django.db.models import Q
from dashboard.models import Student, Event
from authentication.models import CustomUser, Tag, TeacherExtraData
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
    image = forms.ImageField(required=False)
    change_profile = forms.BooleanField(
        widget=forms.HiddenInput, initial=True)  # field to identify the form

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Speichern'))

    def save(self, commit=True):
        if self.cleaned_data['image']:
            extraData = self.instance.teacherextradata
            extraData.image = self.cleaned_data['image']
            extraData.save()
        return super(changeProfileForm, self).save(commit=commit)


class changeTeacherPictureForm(forms.ModelForm):
    change_picture = forms.BooleanField(widget=forms.HiddenInput, initial=True)

    class Meta:
        model = TeacherExtraData
        fields = ('image',)


class configureTagsForm(forms.Form):
    confiure_tags = forms.BooleanField(
        widget=forms.HiddenInput, initial=True)
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects, required=False)


class changePasswordForm(PasswordChangeForm):
    change_password = forms.BooleanField(
        widget=forms.HiddenInput, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', 'Ändern'))


class cancelEventForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)
    book_other_event = forms.BooleanField(initial=False, required=False)
    cancel_event = forms.BooleanField(widget=forms.HiddenInput, initial=True)
