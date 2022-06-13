from operator import imod
from django.shortcuts import render, redirect
from .models import Upcomming_User
from django.db.models import Q
from .forms import *
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

    if request.method == 'POST':
        form = Register_OTP(request.POST)

        if form.is_valid():
            if user_data.first().otp != form.cleaned_data['otp']:
                print("eror")  # hier muss zurück kommen, dass der Pin flasch ist

    else:
        form = Register_OTP()

    return render(request, 'login/register/register.html', {'name': request.GET.get('u'), 'otp_form': form})
