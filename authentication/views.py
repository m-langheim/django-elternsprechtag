from django.shortcuts import render, redirect
from .models import Upcomming_User, CustomUser
from django.db.models import Q
from .forms import *
from .tasks import async_send_mail
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
import os


def register(request, user_token, key_token):

    # First checks and initialization

    if user_token is None or key_token is None:
        return redirect("help_register")

    user_data = Upcomming_User.objects.filter(
        Q(user_token=user_token), Q(access_key=key_token))

    if not user_data.exists():
        return render(request, 'authentication/register/link_error.html')

    user_data = user_data.first()

    if user_data.created + timezone.timedelta(days=30) < timezone.now():
        student = user_data.student
        user_data.delete()
        Upcomming_User.objects.create(student=student)
        return render(request, 'authentication/register/link_deprecated.html')

    # Show different pages

    if user_data.otp_verified: # OTP verified
        
        if user_data.otp_verified_date + timezone.timedelta(hours=3) > timezone.now(): # OTP not verified in the last 3 hours

            # Page where you can choose to login or register

            if request.GET.get('login', False) and request.user.is_authenticated: # Clicked on 'login' and logged into an account again

                # Which type of account

                if request.user.role == 0: # Logged into a parent account -> Add the student to this account
                    user = request.user
                    user.students.add(user_data.student)
                    user.save()
                    name = user_data.student
                    user_data.delete()

                    # TODO: Email, dass Schüler zum Account hinzugefügt wurde

                    messages.success(request, f"You added {name} to your parent account.") # TODO: Hier kann man auch die message durch eine Mitteilung ersetzen.
                    return redirect("home")
                else: # Logged into teacher or staff account -> Logout and re-login
                    logout(request)
                    return render(request, 'authentication/register/unusable_account.html', {'path': request.get_full_path()})

            if request.GET.get('register', False): # Clicked on 'register'

                # Clicked on 'submit' or load this page
                
                if request.method == 'POST': # Clicked on 'submit'
                    form = Register_Parent_Account(request.POST)
                    if form.is_valid():
                        cu = CustomUser(
                            email=form.cleaned_data['email'],
                            first_name=form.cleaned_data['first_name'],
                            last_name=form.cleaned_data['last_name'], role=0)
                        cu.set_password(form.cleaned_data['password'])
                        cu.save()
                        cu.students.add(user_data.student)
                        cu.save()
                        user_data.delete()

                        # TODO: Hier muss hin, dass der Schüler zum Account hinzugefügt wurd

                        # Send confirmation mail
                        async_send_mail.delay("Registrierung erfolgreich", render_to_string("authentication/register/register_finished_email.txt", {'user': cu, 'current_site': os.environ.get("PUBLIC_URL")}), cu.email)

                        if request.user.is_authenticated:
                            logout(request)
                            messages.info(request, "You are logged out to continue the registration process.")

                        return redirect('login')

                else:
                    form = Register_Parent_Account()
                
                return render(request, "authentication/register/register_parent.html", {'register_parent_account': form})
            
            # Set name for the register-choose page

            name = str(user_data.student)
            if len(name) > 20:
                name = name[:18]
                name = name+'...'

            return render(request, "authentication/register/register_choose.html", {'child_name': name, 'path': request.get_full_path()})
        
        else:  # OTP verified more than 3 hours ago
            user_data.otp_verified = False
            user_data.save()
            form = Register_OTP(user_token=user_token, key_token=key_token)

            # Set name for the register-otp page

            name = str(user_data.student)
            if len(name) > 20:
                name = name[:18]
                name = name+'...'

            return render(request, 'authentication/register/register_otp.html', {'otp_form': form, 'child_name': name})
        
    else: # OTP not verified

        # Clicked on 'submit' or load this page

        if request.method == 'POST': # Clicked on 'submit'
            form = Register_OTP(request.POST, user_token=user_token, key_token=key_token)
            if form.is_valid():
                user_data.otp_verified = True
                user_data.otp_verified_date = timezone.now()
                user_data.save()

                # Set name for the register-choose page

                name = str(user_data.student)
                if len(name) > 20:
                    name = name[:18]
                    name = name+'...'

                return render(request, "authentication/register/register_choose.html", {'child_name': name, 'path': request.get_full_path()})

        else:
            form = Register_OTP(user_token=user_token, key_token=key_token)

        # Set name for the register-otp page

        name = str(user_data.student)
        if len(name) > 20:
            name = name[:18]
            name = name+'...'

        return render(request, 'authentication/register/register_otp.html', {'otp_form': form, 'child_name': name})


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = CustomPasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = CustomUser.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "authentication/password-reset/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'current_site': os.environ.get("PUBLIC_URL"),
                    }
                    email = render_to_string(email_template_name, c)
                    # email_html = render_to_string(
                    #     "authentication/password-reset/password_reset_email_html.html", c)
                    # send_mail(subject, email, 'admin@example.com',
                    #           [user.email], fail_silently=False)
                    # async_send_mail.delay(
                    #     subject, email, user.email, email_html_body=email_html)
                    async_send_mail.delay(
                        subject, email, user.email)
                    # return redirect("password_reset_done")
            return redirect("password_reset_done")
    password_reset_form = CustomPasswordResetForm()
    return render(request=request, template_name="authentication/password-reset/password_reset.html", context={"password_reset_form": password_reset_form})
