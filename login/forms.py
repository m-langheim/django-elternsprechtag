from django import forms


class Register_OTP(forms.Form):
    otp = forms.IntegerField(label='One-Time-Password')
