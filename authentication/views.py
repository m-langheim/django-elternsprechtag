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
from django.views import View
from django.views.generic.base import TemplateView

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .tokens import teacher_registration_token, parent_registration_token
from .utils import (
    send_parent_registration_mail,
    parent_registration_check_otp_verified,
    string_shortener,
    parent_registration_link_deprecated,
)


class RegistrationStartView(View):
    def get(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None and not parent_registration_link_deprecated(user_data):
            if not parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_check_otp",
                    user_token=user_token,
                    key_token=key_token,
                )
            if user_data.parent_email:
                try:
                    existing_user = CustomUser.objects.get(email=user_data.parent_email)
                except CustomUser.DoesNotExist:
                    return render(
                        request,
                        "authentication/register/register_parent_email_specified.html",
                        {"parent_email": user_data.parent_email},
                    )
                else:
                    if existing_user.role == 0:
                        return redirect(
                            "parent_register_link_account",
                            user_token=user_token,
                            key_token=key_token,
                        )

            form = Parent_Input_email_Form()

            return render(
                request,
                "authentication/register/register_parent.html",
                {"register_parent_account": form},
            )

    def post(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None and not parent_registration_link_deprecated(user_data):
            if not parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_check_otp",
                    user_token=user_token,
                    key_token=key_token,
                )
            if user_data.parent_email:
                try:
                    existing_user = CustomUser.objects.get(email=user_data.parent_email)
                except CustomUser.DoesNotExist:
                    return render(
                        request,
                        "authentication/register/register_parent_email_specified.html",
                        {"parent_email": user_data.parent_email},
                    )
                else:
                    if existing_user.role == 0:
                        return redirect(
                            "parent_register_link_account",
                            user_token=user_token,
                            key_token=key_token,
                        )

            form = Parent_Input_email_Form(request.POST)

            if form.is_valid():
                email = form.cleaned_data["email"]
                try:
                    existing_user = CustomUser.objects.get(email=email)
                except CustomUser.DoesNotExist:
                    user_data.parent_email = email
                    user_data.save()

                    send_parent_registration_mail(user_data)
                else:
                    if existing_user.role == 0:
                        user_data.parent_email = email
                        user_data.save()
                        return redirect(
                            "parent_register_link_account",
                            user_token=user_token,
                            key_token=key_token,
                        )
                        # return render(
                        #     request,
                        #     "authentication/register/register_parent_email_specified.html",
                        #     {"parent_email": email},
                        # )  # todo Hier muss fertig gestellt werden, was passieren soll, wenn es bereits einen Account gibt mit Weiterleitung und so
                    messages.error(
                        request,
                        "Diese Email gehört zu einem Account, welcher nicht als Elternteil eingetragen ist. Es handelt sich wahrscheinlich um einen Lehreraccount. Bitte verwenden Sie eine andere Email-Adresse um einen Eltern Account zu erstellen.",
                    )
                    form = Parent_Input_email_Form()
            return render(
                request,
                "authentication/register/register_parent.html",
                {"register_parent_account": form},
            )


class RegistrationAccountLinkChooseView(View):
    def get(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None and not parent_registration_link_deprecated(user_data):
            if not parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_check_otp",
                    user_token=user_token,
                    key_token=key_token,
                )
            if not user_data.parent_email:
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )
            try:
                existing_user = CustomUser.objects.get(email=user_data.parent_email)
            except CustomUser.DoesNotExist:
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )
            else:
                if existing_user.role != 0:
                    messages.error(
                        request,
                        "Diese Email gehört zu einem Account, welcher nicht als Elternteil eingetragen ist. Es handelt sich wahrscheinlich um einen Lehreraccount. Bitte verwenden Sie eine andere Email-Adresse um einen Eltern Account zu erstellen.",
                    )
                    return redirect(
                        "parent_register",
                        user_token=user_token,
                        key_token=key_token,
                    )


class RegistrationAccountLinkLoginView(
    View
):  # ? Sollte dies nur über einen Link möglich sein, damit die emails immer verdeckt bleiben? Dann wäre es aber weniger Nutzerfreundlich
    def get(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None and not parent_registration_link_deprecated(user_data):
            if not parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_check_otp",
                    user_token=user_token,
                    key_token=key_token,
                )
            if not user_data.parent_email:
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )
            try:
                existing_user = CustomUser.objects.get(email=user_data.parent_email)
            except CustomUser.DoesNotExist:
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )
            else:
                if existing_user.role != 0:
                    messages.error(
                        request,
                        "Diese Email gehört zu einem Account, welcher nicht als Elternteil eingetragen ist. Es handelt sich wahrscheinlich um einen Lehreraccount. Bitte verwenden Sie eine andere Email-Adresse um einen Eltern Account zu erstellen.",
                    )
                    return redirect(
                        "parent_register",
                        user_token=user_token,
                        key_token=key_token,
                    )
                form = ParentRegistrationLoginForm(
                    initial={"email": user_data.parent_email}
                )
                return render(
                    request,
                    "authentication/register/register_parent_link_existiing_login.html",
                    {"form": form},
                )

    def post(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None and not parent_registration_link_deprecated(user_data):
            if not parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_check_otp",
                    user_token=user_token,
                    key_token=key_token,
                )
            if not user_data.parent_email:
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )
            try:
                existing_user = CustomUser.objects.get(email=user_data.parent_email)
            except CustomUser.DoesNotExist:
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )
            else:
                if existing_user.role != 0:
                    messages.error(
                        request,
                        "Diese Email gehört zu einem Account, welcher nicht als Elternteil eingetragen ist. Es handelt sich wahrscheinlich um einen Lehreraccount. Bitte verwenden Sie eine andere Email-Adresse um einen Eltern Account zu erstellen.",
                    )
                    return redirect(
                        "parent_register",
                        user_token=user_token,
                        key_token=key_token,
                    )
                form = ParentRegistrationLoginForm(
                    request.POST, initial={"email": user_data.parent_email}
                )

                if form.is_valid():
                    username = form.cleaned_data["email"]
                    password = form.cleaned_data["password"]

                    if existing_user.check_password(password):
                        existing_user.students.add(user_data.student)
                        existing_user.save()
                        messages.success(
                            request,
                            f"You added {str(user_data.student)} to your parent account.",
                        )
                        user_data.delete()
                        return redirect("parent_register_success")
                return render(
                    request,
                    "authentication/register/register_parent_link_existiing_login.html",
                    {"form": form},
                )


class RegistrationCheckOtpView(View):
    def get(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None:
            if parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )

            form = Register_OTP(user_token=user_token, key_token=key_token)

            name = string_shortener(str(user_data.student))

            return render(
                request,
                "authentication/register/register_otp.html",
                {"otp_form": form, "child_name": name},
            )

    def post(self, request, user_token, key_token, *args, **kwargs):
        try:
            user_data = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            user_data = None

        if user_data is not None:
            if parent_registration_check_otp_verified(user_data):
                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )

            form = Register_OTP(
                request.POST, user_token=user_token, key_token=key_token
            )
            if form.is_valid():
                user_data.otp_verified = True
                user_data.otp_verified_date = timezone.now()
                user_data.save()

                return redirect(
                    "parent_register",
                    user_token=user_token,
                    key_token=key_token,
                )

            name = string_shortener(str(user_data.student))

            return render(
                request,
                "authentication/register/register_otp.html",
                {"otp_form": form, "child_name": name},
            )


class RegistrationSuccessView(TemplateView):
    template_name = "authentication/register/register_parent_success.html"


# def register(request, user_token, key_token):
#     # First checks and initialization

#     if user_token is None or key_token is None:
#         return redirect("help_register")

#     user_data = Upcomming_User.objects.filter(
#         Q(user_token=user_token), Q(access_key=key_token)
#     )

#     if not user_data.exists():
#         return render(request, "authentication/register/link_error.html")

#     user_data = user_data.first()

#     if user_data.created + timezone.timedelta(days=30) < timezone.now():
#         student = user_data.student
#         user_data.delete()
#         Upcomming_User.objects.create(student=student)
#         return render(request, "authentication/register/link_deprecated.html")

#     # Show different pages

#     if user_data.otp_verified:  # OTP verified
#         if (
#             user_data.otp_verified_date + timezone.timedelta(hours=3) > timezone.now()
#         ):  # OTP not verified in the last 3 hours
#             # Page where you can choose to login or register

#             if (
#                 request.GET.get("login", False) and request.user.is_authenticated
#             ):  # Clicked on 'login' and logged into an account again
#                 # Which type of account

#                 if (
#                     request.user.role == 0
#                 ):  # Logged into a parent account -> Add the student to this account
#                     user = request.user
#                     user.students.add(user_data.student)
#                     user.save()
#                     name = user_data.student
#                     user_data.delete()

#                     # TODO: Email, dass Schüler zum Account hinzugefügt wurde

#                     messages.success(
#                         request, f"You added {name} to your parent account."
#                     )  # TODO: Hier kann man auch die message durch eine Mitteilung ersetzen.
#                     return redirect("home")
#                 else:  # Logged into teacher or staff account -> Logout and re-login
#                     logout(request)
#                     return render(
#                         request,
#                         "authentication/register/unusable_account.html",
#                         {"path": request.get_full_path()},
#                     )

#             if request.GET.get("register", False):  # Clicked on 'register'
#                 # Clicked on 'submit' or load this page

#                 if request.method == "POST":  # Clicked on 'submit'
#                     form = Parent_Input_email_Form(request.POST)
#                     if form.is_valid():
#                         user_data.parent_email = form.cleaned_data["email"]
#                         user_data.save()

#                         send_parent_registration_mail(user_data)

#                 else:
#                     form = Parent_Input_email_Form()

#                 return render(
#                     request,
#                     "authentication/register/register_parent.html",
#                     {"register_parent_account": form},
#                 )

#             # Set name for the register-choose page

#             name = str(user_data.student)
#             if len(name) > 20:
#                 name = name[:18]
#                 name = name + "..."

#             return render(
#                 request,
#                 "authentication/register/register_choose.html",
#                 {"child_name": name, "path": request.get_full_path()},
#             )

#         else:  # OTP verified more than 3 hours ago
#             user_data.otp_verified = False
#             user_data.save()
#             form = Register_OTP(user_token=user_token, key_token=key_token)

#             # Set name for the register-otp page

#             name = str(user_data.student)
#             if len(name) > 20:
#                 name = name[:18]
#                 name = name + "..."

#             return render(
#                 request,
#                 "authentication/register/register_otp.html",
#                 {"otp_form": form, "child_name": name},
#             )

#     else:  # OTP not verified
#         # Clicked on 'submit' or load this page

#         if request.method == "POST":  # Clicked on 'submit'
#             form = Register_OTP(
#                 request.POST, user_token=user_token, key_token=key_token
#             )
#             if form.is_valid():
#                 user_data.otp_verified = True
#                 user_data.otp_verified_date = timezone.now()
#                 user_data.save()

#                 # Set name for the register-choose page

#                 name = str(user_data.student)
#                 if len(name) > 20:
#                     name = name[:18]
#                     name = name + "..."

#                 return render(
#                     request,
#                     "authentication/register/register_choose.html",
#                     {"child_name": name, "path": request.get_full_path()},
#                 )
#         else:
#             form = Register_OTP(user_token=user_token, key_token=key_token)

#         # Set name for the register-otp page

#         name = str(user_data.student)
#         if len(name) > 20:
#             name = name[:18]
#             name = name + "..."

#         return render(
#             request,
#             "authentication/register/register_otp.html",
#             {"otp_form": form, "child_name": name},
#         )


#! Dies ist die alte Version
# def register(request, user_token, key_token):
#     # First checks and initialization

#     if user_token is None or key_token is None:
#         return redirect("help_register")

#     user_data = Upcomming_User.objects.filter(
#         Q(user_token=user_token), Q(access_key=key_token)
#     )

#     if not user_data.exists():
#         return render(request, "authentication/register/link_error.html")

#     user_data = user_data.first()

#     if user_data.created + timezone.timedelta(days=30) < timezone.now():
#         student = user_data.student
#         user_data.delete()
#         Upcomming_User.objects.create(student=student)
#         return render(request, "authentication/register/link_deprecated.html")

#     # Show different pages

#     if user_data.otp_verified:  # OTP verified
#         if (
#             user_data.otp_verified_date + timezone.timedelta(hours=3) > timezone.now()
#         ):  # OTP not verified in the last 3 hours
#             # Page where you can choose to login or register

#             if (
#                 request.GET.get("login", False) and request.user.is_authenticated
#             ):  # Clicked on 'login' and logged into an account again
#                 # Which type of account

#                 if (
#                     request.user.role == 0
#                 ):  # Logged into a parent account -> Add the student to this account
#                     user = request.user
#                     user.students.add(user_data.student)
#                     user.save()
#                     name = user_data.student
#                     user_data.delete()

#                     # TODO: Email, dass Schüler zum Account hinzugefügt wurde

#                     messages.success(
#                         request, f"You added {name} to your parent account."
#                     )  # TODO: Hier kann man auch die message durch eine Mitteilung ersetzen.
#                     return redirect("home")
#                 else:  # Logged into teacher or staff account -> Logout and re-login
#                     logout(request)
#                     return render(
#                         request,
#                         "authentication/register/unusable_account.html",
#                         {"path": request.get_full_path()},
#                     )

#             if request.GET.get("register", False):  # Clicked on 'register'
#                 # Clicked on 'submit' or load this page

#                 if request.method == "POST":  # Clicked on 'submit'
#                     form = Register_Parent_Account(request.POST)
#                     if form.is_valid():
#                         cu = CustomUser(
#                             email=form.cleaned_data["email"],
#                             first_name=form.cleaned_data["first_name"],
#                             last_name=form.cleaned_data["last_name"],
#                             role=0,
#                         )
#                         cu.set_password(form.cleaned_data["password"])
#                         cu.save()
#                         studi = user_data.student
#                         cu.students.add(studi)
#                         cu.save()
#                         user_data.delete()

#                         # Send confirmation mails
#                         async_send_mail.delay(
#                             "Registrierung erfolgreich",
#                             render_to_string(
#                                 "authentication/register/register_finished_email.txt",
#                                 {
#                                     "user": cu,
#                                     "current_site": os.environ.get("PUBLIC_URL"),
#                                 },
#                             ),
#                             cu.email,
#                         )
#                         async_send_mail.delay(
#                             "Registrierung erfolgreich",
#                             render_to_string(
#                                 "authentication/register/register_finished_email_student.txt",
#                                 {"user": studi},
#                             ),
#                             studi.child_email,
#                         )

#                         if request.user.is_authenticated:
#                             logout(request)
#                             messages.info(
#                                 request,
#                                 "You are logged out to continue the registration process.",
#                             )

#                         return redirect("login")

#                 else:
#                     form = Register_Parent_Account()

#                 return render(
#                     request,
#                     "authentication/register/register_parent.html",
#                     {"register_parent_account": form},
#                 )

#             # Set name for the register-choose page

#             name = str(user_data.student)
#             if len(name) > 20:
#                 name = name[:18]
#                 name = name + "..."

#             return render(
#                 request,
#                 "authentication/register/register_choose.html",
#                 {"child_name": name, "path": request.get_full_path()},
#             )

#         else:  # OTP verified more than 3 hours ago
#             user_data.otp_verified = False
#             user_data.save()
#             form = Register_OTP(user_token=user_token, key_token=key_token)

#             # Set name for the register-otp page

#             name = str(user_data.student)
#             if len(name) > 20:
#                 name = name[:18]
#                 name = name + "..."

#             return render(
#                 request,
#                 "authentication/register/register_otp.html",
#                 {"otp_form": form, "child_name": name},
#             )

#     else:  # OTP not verified
#         # Clicked on 'submit' or load this page

#         if request.method == "POST":  # Clicked on 'submit'
#             form = Register_OTP(
#                 request.POST, user_token=user_token, key_token=key_token
#             )
#             if form.is_valid():
#                 user_data.otp_verified = True
#                 user_data.otp_verified_date = timezone.now()
#                 user_data.save()

#                 # Set name for the register-choose page

#                 name = str(user_data.student)
#                 if len(name) > 20:
#                     name = name[:18]
#                     name = name + "..."

#                 return render(
#                     request,
#                     "authentication/register/register_choose.html",
#                     {"child_name": name, "path": request.get_full_path()},
#                 )
#         else:
#             form = Register_OTP(user_token=user_token, key_token=key_token)

#         # Set name for the register-otp page

#         name = str(user_data.student)
#         if len(name) > 20:
#             name = name[:18]
#             name = name + "..."

#         return render(
#             request,
#             "authentication/register/register_otp.html",
#             {"otp_form": form, "child_name": name},
#         )


class ParentCreateAccountView(View):
    def get(self, request, user_token, key_token, token):
        try:
            up_user = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            up_user = None
            print("No user")
            print(
                Upcomming_User.objects.filter(
                    Q(user_token=user_token), Q(access_key=key_token)
                )
            )
        print(
            up_user is not None,
            parent_registration_token.check_token(up_user, token),
            up_user is not None
            and parent_registration_token.check_token(up_user, token),
        )
        if up_user is not None and parent_registration_token.check_token(
            up_user, token
        ):  # todo Hier muss noch überprüft werden, ob es bereits einen Nutzer mit der email gibt
            payload = {
                "up_user": up_user,
                "form": Register_Parent_Account(
                    initial={"email": up_user.parent_email}
                ),
            }
            return render(
                request,
                "authentication/register/register_parent_account.html",
                payload,
            )
        else:
            messages.error(request, "Dieser Link ist ungültig.")
            return redirect("login")

    def post(self, request, user_token, key_token, token):
        try:
            up_user = Upcomming_User.objects.get(
                Q(user_token=user_token), Q(access_key=key_token)
            )
        except:
            up_user = None

        if up_user is not None and parent_registration_token.check_token(
            up_user, token
        ):
            form = Register_Parent_Account(
                request.POST, initial={"email": up_user.parent_email}
            )
            if form.is_valid():
                cu = CustomUser(
                    email=up_user.parent_email,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    role=0,
                )
                cu.set_password(form.cleaned_data["password"])
                cu.save()
                studi = up_user.student
                cu.students.add(studi)
                cu.save()
                up_user.delete()
                messages.success(
                    request,
                    "Wir haben Ihren Elternaccount nun erstellt. Sie können sich im Folgenden anmelden.",
                )
                return redirect("parent_register_success")
            payload = {"user": up_user, "form": form}
            return render(
                request,
                "authentication/register/register_parent_account.html",
                payload,
            )
        else:
            messages.error(request, "Dieser Link ist ungültig.")
            return redirect("login")


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = CustomPasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data["email"]
            associated_users = CustomUser.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = (
                        "authentication/password-reset/password_reset_email.txt"
                    )
                    c = {
                        "email": user.email,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        "token": default_token_generator.make_token(user),
                        "current_site": os.environ.get("PUBLIC_URL"),
                    }
                    email = render_to_string(email_template_name, c)
                    # email_html = render_to_string(
                    #     "authentication/password-reset/password_reset_email_html.html", c)
                    # send_mail(subject, email, 'admin@example.com',
                    #           [user.email], fail_silently=False)
                    # async_send_mail.delay(
                    #     subject, email, user.email, email_html_body=email_html)
                    async_send_mail.delay(subject, email, user.email)
                    # return redirect("password_reset_done")
            return redirect("password_reset_done")
    password_reset_form = CustomPasswordResetForm()
    return render(
        request=request,
        template_name="authentication/password-reset/password_reset.html",
        context={"password_reset_form": password_reset_form},
    )


# Dies dient zum Registrieren eines neuen Lehrers
class TeacherRegistrationView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(Q(pk=uid), Q(role=1))
        except:
            user = None

        if user is not None and teacher_registration_token.check_token(user, token):
            payload = {
                "user": user,
                "form": TeacherRegistrationForm(initial={"email": user.email}),
            }
            return render(
                request,
                "authentication/teacher_registration/teacher_registration.html",
                payload,
            )
        else:
            messages.error(request, "Dieser Link ist ungültig.")
            return redirect("login")

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(Q(pk=uid), Q(role=1))
        except:
            user = None

        if user is not None and teacher_registration_token.check_token(user, token):
            form = TeacherRegistrationForm(request.POST, initial={"email": user.email})
            if form.is_valid():
                user.is_active = True
                user.first_name = form.cleaned_data["first_name"]
                user.last_name = form.cleaned_data["last_name"]
                user.teacherextradata.acronym = form.cleaned_data["acronym"]
                user.set_password(form.cleaned_data["password"])
                user.save()
                messages.success(
                    request,
                    "Ihr Lehreraccount wurde nun erfolgreich erstellt. Sie können sich nun anmelden.",
                )
                return redirect("login")
            payload = {"user": user, "form": form}
            return render(
                request,
                "authentication/teacher_registration/teacher_registration.html",
                payload,
            )
        else:
            messages.error(request, "Dieser Link ist ungültig.")
            return redirect("login")
