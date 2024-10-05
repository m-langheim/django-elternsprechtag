from .models import *
import factory

from factory.django import DjangoModelFactory
from django.contrib.auth.models import Group


class StudentFactory(DjangoModelFactory):
    class Meta:
        model = Student

    shield_id = factory.Faker("bothify", text="????????????????????????????????")
    child_email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    class_name = factory.Faker("bothify", text="##?")


class TeacherFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser

    role = 1
    is_active = True


class ParentFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser

    role = 0
    is_active = True
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")

    @factory.post_generation
    def students(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return StudentFactory.create()

        # Add the iterable of groups using bulk addition
        self.students.add(*extracted)


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Faker("name")
