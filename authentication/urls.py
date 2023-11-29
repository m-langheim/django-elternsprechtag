from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    # path("register/<user_token>/<key_token>/", register),
    path(
        "register/<user_token>/<key_token>/",
        RegistrationStartView.as_view(),
        name="parent_register",
    ),
    path(
        "register/<user_token>/<key_token>/otp/",
        RegistrationCheckOtpView.as_view(),
        name="parent_check_otp",
    ),
    path(
        "register/success/",
        RegistrationSuccessView.as_view(),
        name="parent_register_success",
    ),
    path(
        "register/<user_token>/<key_token>/link_account/login/",
        RegistrationAccountLinkLoginView.as_view(),
        name="parent_register_link_account",
    ),
    path(
        "register/<user_token>/<key_token>/<token>/new_account",
        ParentCreateAccountView.as_view(),
        name="parent_create_account",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="authentication/login.html",
            authentication_form=CustomAuthForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="authentication/logout.html"),
        name="logout",
    ),
    path("password-reset/", password_reset_request, name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="authentication/password-reset/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="authentication/password-reset/password_reset_confirm.html",
            form_class=CustomSetPasswordForm,
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="authentication/password-reset/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "teacher_registartion/<uidb64>/<token>/",
        TeacherRegistrationView.as_view(),
        name="teacher_new_registartion_view",
    ),
]

# path('password-reset/',
#          auth_views.PasswordResetView.as_view(
#              template_name='authentication/password-reset/password_reset.html',
#              subject_template_name='authentication/password-reset/password_reset_subject.txt',
#              email_template_name='authentication/password-reset/password_reset_email.html',
#              success_url='/login/'
#          ),
#          name='password_reset'),
