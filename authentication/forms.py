from cProfile import label
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from django.utils.translation import gettext as _


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('email',)


class Register_OTP(forms.Form):
    otp = forms.IntegerField(label='One-Time-Password')


class Register_Parent_Account(forms.Form):
    email = forms.EmailField(label=_('Email'))
    first_name = forms.CharField(label=_('FirstName'))
    last_name = forms.CharField(label=_('Last Name'))
    password = forms.CharField(widget=forms.PasswordInput)