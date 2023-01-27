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
    shield_id = models.CharField(
        max_length=38, unique=True)
    first_name = models.CharField(_("First name"), max_length=48)
    last_name = models.CharField(_("Last name"), max_length=48)
    child_email = models.EmailField(max_length=200, null=True)
    class_name = models.CharField(max_length=2, default="")
    registered = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class CustomUser(AbstractBaseUser, PermissionsMixin):  # Erwachsene (also alle außer Schüler)

    CHOCES_ROLES = ((0, _("Parent")), (1, _("Teacher")), (2, _("Others")))

    email = models.EmailField(_("Email"), unique=True)
    first_name = models.CharField(
        _("First name"), max_length=48, default="", blank=True)
    last_name = models.CharField(
        _("Last name"), max_length=48, default="", blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    role = models.IntegerField(_("Role"), choices=CHOCES_ROLES, default=2)
    date_joined = models.DateTimeField(default=timezone.now)

    students = models.ManyToManyField(Student, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


def generate_new_color():

    while True:
        color = "#"+''.join([random.choice('ABCDEF0123456789')
                            for i in range(6)])
        if not Tag.objects.filter(color=color):
            break

    return color


class Tag(models.Model):
    name = models.CharField(max_length=32)
    synonyms = models.TextField(null=True, blank=True)
    color = ColorField(default=generate_new_color)

    def __str__(self):
        return self.name


class TeacherExtraData(models.Model):
    teacher = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1})
    acronym = models.CharField(max_length=3, default="")
    # tags = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    room = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='teacher_pics/', default="default.jpg")

    def __str__(self):
        return f'{self.teacher.last_name} extraData'

    def save(self, *args, **kwargs):
        super(TeacherExtraData, self).save(*args, **kwargs)
        # resize the image
        if self.image:
            img = Image.open(self.image.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)


def generate_unique_code():

    while True:
        random_num = random.randint(a=0, b=2)
        sample_str = ''.join((random.choice(string.ascii_letters)
                              for i in range(4+random_num)))
        sample_str += ''.join((random.choice(string.digits)
                               for i in range(8-random_num)))

        # Convert string to list and shuffle it to mix letters and digits
        sample_list = list(sample_str)
        random.shuffle(sample_list)
        final_code = ''.join(sample_list)
        if Upcomming_User.objects.filter(models.Q(user_token=final_code) | models.Q(access_key=final_code)).count() == 0:
            break

    return final_code


def generate_unique_otp():

    while True:
        final_code = ''.join(random.choice(string.digits) for i in range(6))
        if Upcomming_User.objects.filter(otp=final_code).count() == 0:
            break

    return final_code


class Upcomming_User(models.Model):  # Alle Schüler, die noch keine Eltern haben
    user_token = models.CharField(
        max_length=12, primary_key=True, default=generate_unique_code)
    access_key = models.CharField(max_length=12, default=generate_unique_code)
    otp = models.CharField(max_length=6, default=generate_unique_otp)
    otp_verified = models.BooleanField(default=False)
    otp_verified_date = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)
    student = models.OneToOneField(Student, on_delete=models.CASCADE)

    def __str__(self):
        return f'{_("Access for")} {self.student}'
