from django.db import models
import string
import random
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext as _
from colorfield.fields import ColorField

from PIL import Image

from .managers import CustomUserManager

# Create your models here.


class Student(models.Model):  # Schüler
    shield_id = models.CharField(max_length=38, unique=True)
    first_name = models.CharField(_("First name"), max_length=48)
    last_name = models.CharField(_("Last name"), max_length=48)
    child_email = models.EmailField(_("Child emails"), max_length=200, null=True)
    class_name = models.CharField(_("Name of class"), max_length=4, default="")
    registered = models.BooleanField(_("Childs parents have registered"), default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def parent(self):
        try:
            parent = CustomUser.objects.get(students=self)
        except CustomUser.DoesNotExist:
            return None
        else:
            return parent

    class Meta:
        verbose_name = _("Student")
        verbose_name_plural = _("Students")


class StudentChange(models.Model):
    CHOICES_OPERATION = (
        (0, "no changes"),
        (1, "Create new Student"),
        (2, "Field Changes"),
        (3, "Delete Student"),
    )

    operation = models.IntegerField(choices=CHOICES_OPERATION, default=0, blank=False)
    student = models.ForeignKey(
        Student,
        verbose_name=_("Student"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    shield_id = models.CharField(max_length=38, null=True, blank=True)
    first_name = models.CharField(_("First name"), max_length=48, null=True, blank=True)
    last_name = models.CharField(_("Last name"), max_length=48, null=True, blank=True)
    child_email = models.EmailField(
        _("Child emails"), max_length=200, null=True, blank=True
    )
    class_name = models.CharField(
        _("Name of class"), max_length=4, null=True, blank=True
    )
    approved = models.BooleanField(default=False)
    created = models.DateTimeField(default=timezone.now)
    applied = models.BooleanField(default=False)
    applied_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [("apply_changes", _("Can apply changes to the students"))]


class CustomUser(
    AbstractBaseUser, PermissionsMixin
):  # Erwachsene (also alle außer Schüler)
    class UserRoleChoices(models.IntegerChoices):
        PARENT = 0, _("Parent")
        TEACHER = 1, _("Teacher")
        OTHER = 2, _("Others")

    # CHOCES_ROLES = ((0, _("Parent")), (1, _("Teacher")), (2, _("Others")))

    email = models.EmailField(_("Email"), unique=True)
    first_name = models.CharField(
        _("First name"), max_length=48, default="", blank=True
    )
    last_name = models.CharField(_("Last name"), max_length=48, default="", blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    role = models.IntegerField(
        _("Role"), choices=UserRoleChoices, default=UserRoleChoices.OTHER
    )
    date_joined = models.DateTimeField(
        verbose_name=_("Date joined"), default=timezone.now
    )

    students = models.ManyToManyField(Student, verbose_name=_("Students"), blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


def generate_new_color():
    color = "#" + "".join([random.choice("ABCDEF0123456789") for i in range(6)])

    return color


class Tag(models.Model):
    name = models.CharField(_("General name"), max_length=32)
    synonyms = models.TextField(_("Synonyms"), null=True, blank=True)
    color = ColorField(_("Colour"), default=generate_new_color)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class TeacherExtraData(models.Model):
    teacher = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={"role": 1},
        verbose_name=_("User object of the teacher"),
    )
    acronym = models.CharField(max_length=3, default="", verbose_name=_("Acronym"))
    tags = models.ManyToManyField(Tag, blank=True, verbose_name=_("Tags"))
    room = models.IntegerField(blank=True, null=True, verbose_name=_("Room"))
    image = models.ImageField(
        upload_to="teacher_pics/",
        default="default.jpg",
        verbose_name=_("Profile image"),
    )

    def __str__(self):
        return f"{self.teacher.last_name} extraData"

    def save(self, *args, **kwargs):
        super(TeacherExtraData, self).save(*args, **kwargs)
        # resize the image
        if self.image:
            img = Image.open(self.image.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)

    class Meta:
        verbose_name = _("Additional data for teacher")
        verbose_name_plural = _("Additional data for teachers")


def generate_unique_code():
    while True:
        random_num = random.randint(a=0, b=2)
        sample_str = "".join(
            (random.choice(string.ascii_letters) for i in range(4 + random_num))
        )
        sample_str += "".join(
            (random.choice(string.digits) for i in range(8 - random_num))
        )

        # Convert string to list and shuffle it to mix letters and digits
        sample_list = list(sample_str)
        random.shuffle(sample_list)
        final_code = "".join(sample_list)
        if (
            Upcomming_User.objects.filter(
                models.Q(user_token=final_code) | models.Q(access_key=final_code)
            ).count()
            == 0
        ):
            break

    return final_code


def generate_unique_otp():
    while True:
        final_code = "".join(random.choice(string.digits) for i in range(6))
        if Upcomming_User.objects.filter(otp=final_code).count() == 0:
            break

    return final_code


class Upcomming_User(models.Model):  # Alle Schüler, die noch keine Eltern haben
    user_token = models.CharField(
        max_length=12,
        primary_key=True,
        default=generate_unique_code,
        verbose_name=_("User token"),
    )
    access_key = models.CharField(
        max_length=12, default=generate_unique_code, verbose_name=_("Access token")
    )
    otp = models.CharField(
        max_length=6, default=generate_unique_otp, verbose_name=_("OTP key")
    )
    otp_verified = models.BooleanField(
        default=False, verbose_name=_("OTP key was verified")
    )
    otp_verified_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("Time of OTP key verification")
    )
    created = models.DateTimeField(
        default=timezone.now, verbose_name=_("Time of creation")
    )
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, verbose_name=_("Student")
    )
    email_send = models.BooleanField(default=False, verbose_name=_("Email send"))

    parent_email = models.EmailField(blank=True, null=True)
    parent_registration_email_send = models.BooleanField(default=False)

    def __str__(self):
        return f'{_("Access for")} {self.student}'

    class Meta:
        verbose_name = _("Future user")
        verbose_name_plural = _("Future users")
