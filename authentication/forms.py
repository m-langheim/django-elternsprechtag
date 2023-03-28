from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import CustomUser
from crispy_forms.helper import FormHelper
from django.utils.translation import gettext as _

class CustomAuthForm(AuthenticationForm): # login
    class Meta:
        fields = ['username','password']
    def __init__(self, *args, **kwargs):
        super(CustomAuthForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autocomplete': "off"})
        self.fields['username'].label = False
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder':'Password'}) 
        self.fields['password'].label = False

class CustomPasswordResetForm(PasswordResetForm): # password reset
    class Meta:
        fields = ['email']
    def __init__(self, *args, **kwargs):
        super(CustomPasswordResetForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autocomplete': "off"})
        self.fields['email'].label = False

class CustomSetPasswordForm(SetPasswordForm):

    class Meta:
        fields = ['new_password1','new_password2']

    def __init__(self, *args, **kwargs):
        super(CustomSetPasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password', 'autocomplete': "off"})
        self.fields['new_password1'].label = False
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password', 'autocomplete': "off"})
        self.fields['new_password2'].label = False

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('email',)


class Register_OTP(forms.Form): # one time password
    otp = forms.CharField(label=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Code'}), min_length=6, max_length=6)

    def clean(self):
        if self.cleaned_data('otp') != 6: # how to get the amount of chars?
            raise forms.ValidationError(_("a error."), code='invalid_.')



class Register_Parent_Account(forms.Form): # register (parent account)
    def validate_the_email(value):
        if CustomUser.objects.filter(email=value).exists():
            raise forms.ValidationError(_('This email is already in use. Please select another email.'))

    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': _('Email'), 'autocomplete': 'off'}), validators=[validate_the_email], label=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('First Name'), 'autocomplete': 'off'}), label=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('Last Name'), 'autocomplete': 'off'}), label=False)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': _('Password'), 'autocomplete': 'off'}), max_length=255, label=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': _('Confirm Password'), 'autocomplete': 'off'}), max_length=255, label=False)

    def clean(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']

        if password == confirm_password:
            return self.cleaned_data
        raise forms.ValidationError(_("a error."))

class AdminCsvImportForm(forms.Form):
    csv_file = forms.FileField()