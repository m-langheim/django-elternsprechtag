from dataclasses import field
from django import forms
from django.db.models import Q
from dashboard.models import Student, Event, EventChangeFormula
from authentication.models import CustomUser, Tag, TeacherExtraData
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.forms import PasswordChangeForm

from django.utils.translation import gettext as _


class createInquiryForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=0), disabled=True
    )
    reason = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(createInquiryForm, self).__init__(*args, **kwargs)
        self.fields["reason"].label = False


class editInquiryForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), disabled=True)
    parent = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=0), disabled=True
    )
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(Q(occupied=True)), disabled=True, required=False
    )
    reason = forms.CharField(widget=forms.Textarea, required=False)

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
        widget=forms.Textarea, label=_("Explanation why you dismiss the event.")
    )
    book_other_event = forms.BooleanField(
        initial=False, required=False, label=_("Parent should book a different event.")
    )
    cancel_event = forms.BooleanField(widget=forms.HiddenInput, initial=True)


class EventChangeFormulaForm(forms.ModelForm):
    class Meta:
        model = EventChangeFormula
        fields = ["start_time", "end_time", "no_events"]

    def clean(self):
        super(EventChangeFormulaForm, self).clean()

        print(self.cleaned_data)

        start_time = self.cleaned_data.get("start_time")
        end_time = self.cleaned_data.get("end_time")
        no_events = self.cleaned_data.get("no_events")

        if not no_events:
            if not start_time:
                self.add_error("start_time", "This field must be specified.")
            if not end_time:
                self.add_error("end_time", "This field must be specified.")
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
