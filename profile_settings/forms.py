from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from authentication.models import CustomUser, Tag

from django.utils.translation import gettext as _


class changeProfileFormForTeacher(forms.ModelForm):  # Nur für lehrer
    image = forms.ImageField(required=False)
    change_profile = forms.BooleanField(
        widget=forms.HiddenInput, initial=True)  # field to identify the form

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

    def save(self, commit=True):
        if self.cleaned_data['image']:
            extraData = self.instance.teacherextradata
            extraData.image = self.cleaned_data['image']
            extraData.save()
        return super(changeProfileFormForTeacher, self).save(commit=commit)


class changeProfileFormForTeacher(forms.ModelForm):  # Nur für lehrer
    image = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.add_input(Submit('submit', _('Speichern')))
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self, commit=True):
        if self.cleaned_data['image']:
            extraData = self.instance.teacherextradata
            extraData.image = self.cleaned_data['image']
            extraData.save()
        return super(changeProfileFormForTeacher, self).save(commit=commit)


class changeProfileFormForUsers(forms.ModelForm):  # Für alle außer Lehrer
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True



class configureTagsFormForTeacher(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects, required=False)
