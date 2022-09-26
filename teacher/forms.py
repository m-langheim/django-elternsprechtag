from django import forms
from django.db.models import Q
from dashboard.models import Student, Event
from authentication.models import CustomUser


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
