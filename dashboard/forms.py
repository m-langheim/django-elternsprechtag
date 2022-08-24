from django import forms
from .models import Student


class BookForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(BookForm, self).__init__(*args, **kwargs)
        self.fields['student'].queryset = self.request.user.students

    student = forms.ModelMultipleChoiceField(
        queryset=None, widget=forms.CheckboxSelectMultiple)
