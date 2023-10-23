from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class TeacherRegistrationToken(PasswordResetTokenGenerator):
    def _make_hash_value(self, user: AbstractBaseUser, timestamp: int) -> str:
        print(user.pk, timestamp, user.is_active, "account_activation")
        return (
            str(user.pk) + str(timestamp) + str(user.is_active) + "account_activation"
        )


teacher_registration_token = TeacherRegistrationToken()
