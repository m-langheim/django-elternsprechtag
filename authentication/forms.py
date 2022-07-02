from cProfile import label
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser
from django.utils.translation import gettext as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

class CustomAuthForm(AuthenticationForm):
    class Meta:
        fields = ['username','password']
    def __init__(self, *args, **kwargs):
        super(CustomAuthForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autocomplete': "off"})
        self.fields['username'].label = False
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder':'Password'}) 
        self.fields['password'].label = False


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