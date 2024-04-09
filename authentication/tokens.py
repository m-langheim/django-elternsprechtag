from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .models import Upcomming_User


class TeacherRegistrationToken(PasswordResetTokenGenerator):
    def _make_hash_value(self, user: AbstractBaseUser, timestamp: int) -> str:
        # print(user.pk, timestamp, user.is_active, "account_activation")
        return (
            str(user.pk) + str(timestamp) + str(user.is_active) + "account_activation"
        )


class ParentRegistrationToken(PasswordResetTokenGenerator):
    def _make_hash_value(self, up_user: Upcomming_User, timestamp: int) -> str:
        return (
            str(up_user.user_token)
            + str(up_user.created)
            + str(up_user.parent_email)
            + str(up_user.otp)
            + str(timestamp)
            + "parent_registration"
        )


teacher_registration_token = TeacherRegistrationToken()
parent_registration_token = ParentRegistrationToken()
