from django.db import models
import string
import random
from datetime import datetime
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

from .managers import CustomUserManager

# Create your models here.


class Student(models.Model):
    first_name = models.CharField(max_length=48)
    last_name = models.CharField(max_length=48)
    child_email = models.EmailField(max_length=200, null=True)
    registered = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class CustomUser(AbstractBaseUser, PermissionsMixin):

    CHOCES_ROLES = ((0, "Parent"), (1, "Teacher"), (2, "Others"))

    email = models.EmailField("Email", unique=True)
    first_name = models.CharField(max_length=48, default="", blank=True)
    last_name = models.CharField(max_length=48, default="", blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    role = models.IntegerField(choices=CHOCES_ROLES, default=2)
    date_joined = models.DateTimeField(default=timezone.now)

    students = models.ManyToManyField(Student, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


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


class Upcomming_User(models.Model):
    user_token = models.CharField(
        max_length=12, primary_key=True, default=generate_unique_code)
    access_key = models.CharField(max_length=12, default=generate_unique_code)
    otp = models.IntegerField(default=generate_unique_otp)
    otp_verified = models.BooleanField(default=False)
    otp_verified_date = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(default=timezone.now)
    student = models.OneToOneField(Student, on_delete=models.CASCADE)

    def __str__(self):
        return f'Access for {self.student}'
