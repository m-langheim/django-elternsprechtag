from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from .models import CustomUser
from django.utils.translation import gettext as _
from .models import *
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password

from crispy_forms.helper import FormHelper


class CustomAuthForm(AuthenticationForm):  # login
    class Meta:
        fields = ["username", "password"]

    def __init__(self, *args, **kwargs):
        super(CustomAuthForm, self).__init__(*args, **kwargs)
        self.fields["username"].widget = forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
                "autocomplete": "off",
            }
        )
        self.fields["username"].label = False
        self.fields["password"].widget = forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
        self.fields["password"].label = False


class CustomPasswordResetForm(PasswordResetForm):  # password reset
    class Meta:
        fields = ["email"]

    def __init__(self, *args, **kwargs):
        super(CustomPasswordResetForm, self).__init__(*args, **kwargs)
        self.fields["email"].widget = forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email",
                "autocomplete": "off",
            }
        )
        self.fields["email"].label = False


class CustomSetPasswordForm(SetPasswordForm):
    class Meta:
        fields = ["new_password1", "new_password2"]

    def __init__(self, *args, **kwargs):
        super(CustomSetPasswordForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "New password",
                "autocomplete": "off",
            }
        )
        self.fields["new_password1"].label = False
        self.fields["new_password2"].widget = forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm password",
                "autocomplete": "off",
            }
        )
        self.fields["new_password2"].label = False


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email",)


class Register_OTP(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user_token = kwargs.pop("user_token")
        self.key_token = kwargs.pop("key_token")
        super(Register_OTP, self).__init__(*args, **kwargs)

    otp = forms.CharField(
        label=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center fs-4",
                "autocomplete": "off"
            }
        ),
        required=True,
        max_length=6,
        min_length=6
    )
    def clean_otp(self):
        otp = self.cleaned_data["otp"]
        user_data = Upcomming_User.objects.get(
            Q(user_token=self.user_token), Q(access_key=self.key_token)
        )

        if not otp.isdigit():
            raise forms.ValidationError(
                "The verification code will only consist of digits.", code="invalid_type"
            )

        if str(user_data.otp) != str(otp):
            raise forms.ValidationError(
                "This verification code is not correct.", code="incorrect_code"
            )
        
class Parent_Input_email_Form(forms.Form):
    email = forms.CharField(
        widget=forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "off"}),
        label=False,
    )


class Register_Parent_Account(forms.Form):

    email = forms.CharField(
        widget=forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "off"}),
        label=False,
        disabled=True,
    )
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "First Name", "autocomplete": "off"}
        ),
        label=False,
        required=True,
    )
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Last Name", "autocomplete": "off"}
        ),
        label=False,
        required=True,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "autocomplete": "off"}
        ),
        max_length=255,
        label=False,
        required=True,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm Password", "autocomplete": "off"} #Use "Form-control" to get the same design as "as_crispy_field" but no error etc.
        ),
        max_length=255,
        label=False,
        required=True,
    )

    def clean_confirm_password(self):
        password = self.cleaned_data["password"]
        confirm_password = self.cleaned_data["confirm_password"]

        if password != confirm_password:
            raise forms.ValidationError(
                "The passwords do not match", code="passwords_wrong"
            )
        validate_password(password, user=None, password_validators=None)


class ParentRegistrationLoginForm(forms.Form):
    email = email = forms.CharField(
        widget=forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "off"}),
        label=False,
        disabled=True,
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "autocomplete": "off"}
        ),
        max_length=255,
        label=False,
    )


class TeacherRegistrationForm(forms.Form):
    email = forms.CharField(
        widget=forms.EmailInput(attrs={"placeholder": "Email", "autocomplete": "off"}),
        label=False,
        required=True,
        disabled=True,
    )
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "First Name", "autocomplete": "off"}
        ),
        label=False,
    )
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Last Name", "autocomplete": "off"}
        ),
        label=False,
    )

    acronym = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={"placeholder": "Acronym", "autocomplete": "off"}),
        label=False,
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "autocomplete": "off"}
        ),
        max_length=255,
        label=False,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm Password", "autocomplete": "off"}
        ),
        max_length=255,
        label=False,
        required=True,
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm Password", "autocomplete": "off"} #Use "Form-control" to get the same design as "as_crispy_field" but no error etc.
        ),
        max_length=255,
        label=False,
        required=True,
    )

    def clean_confirm_password(self):
        password = self.cleaned_data["password"]
        confirm_password = self.cleaned_data["confirm_password"]

        if password != confirm_password:
            raise forms.ValidationError(
                "The passwords do not match", code="passwords_wrong"
            )
        validate_password(password, user=None, password_validators=None)


# These are all forms regarding the admin interface
class AdminCsvImportForm(forms.Form):
    csv_file = forms.FileField()
