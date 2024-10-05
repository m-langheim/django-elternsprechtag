import rules
from .models import CustomUser


@rules.predicate
def user_is_teacher(user, *args, **kwargs):
    return user.role == CustomUser.UserRoleChoices.TEACHER


rules.add_perm("student.can_view_all", user_is_teacher)
