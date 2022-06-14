from django.shortcuts import render, redirect
from .models import Upcomming_User
from django.db.models import Q
from .forms import *
from django.utils import timezone
from django.contrib import messages

# Create your views here.


def register(request):
    user_token = request.GET.get('u')
    key_token = request.GET.get('key')
    if user_token is None or key_token is None:
        return redirect("help_register")

    user_data = Upcomming_User.objects.filter(
        Q(user_token=user_token), Q(access_key=key_token))

    if not user_data.exists():
        return render(request, 'login/register/link_error.html')

    user_data = user_data.first()

    if user_data.otp_verified:
        print(user_data.otp_verified_date)

    if request.method == 'POST':
        form = Register_OTP(request.POST)

        if form.is_valid():
            if user_data.otp != form.cleaned_data['otp']:
                print("eror")  # hier muss zurück kommen, dass der Pin flasch ist
                messages.error(request, "The code is invalid")
            else:
                user_data.otp_verified = True
                user_data.otp_verified_date = timezone.now()
                user_data.save()
                print("Login")
                return render(request, "login/register/register.html")

    else:
        form = Register_OTP()

    return render(request, 'login/register/register_otp.html', {'otp_form': form})
