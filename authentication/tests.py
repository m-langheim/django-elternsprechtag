from django.contrib.auth import get_user_model
from django.test import TestCase
from .factories import *
from .utils import *
import factory
from faker import Faker

fake = Faker()


class UsersManagersTests(TestCase):

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(email="normal@user.com", password="foo")
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(TypeError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="foo")

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            email="super@user.com", password="foo"
        )
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="super@user.com", password="foo", is_superuser=False
            )


class StudentTests(TestCase):
    def setUp(self) -> None:
        self.student = StudentFactory.create()
        self.parent = ParentFactory.create(students=[self.student])

    def test_student_name(self):
        self.assertEqual(
            str(self.student), f"{self.student.first_name} {self.student.last_name}"
        )

    def test_student_parent_relationship(self):
        self.assertEqual(self.student.parent(), self.parent)


class TagTests(TestCase):
    def setUp(self) -> None:
        self.tags = TagFactory.create_batch(10)

    def test_color_unique(self):
        new_color = generate_new_color()

        self.assertFalse(Tag.objects.filter(color=new_color).exists())

    def test_tag_name(self):
        self.assertEqual(str(self.tags[0]), self.tags[0].name)


class CodeGeneratorTests(TestCase):
    def setUp(self) -> None:
        StudentFactory.create_batch(10)

    def test_generate_unique_code(self):
        self.assertFalse(
            Upcomming_User.objects.filter(user_token=generate_unique_code()).exists()
        )

    def test_generate_unique_otp(self):
        self.assertFalse(
            Upcomming_User.objects.filter(otp=generate_unique_otp()).exists()
        )


class TeacherTests(TestCase):
    def setUp(self) -> None:
        self.teacher = TeacherFactory.create()
        self.parent = ParentFactory.create(students=[StudentFactory.create()])

    def test_teacher_registration_start(self):
        email = fake.email()
        register_new_teacher(email)

        self.assertTrue(
            CustomUser.objects.filter(Q(role=1), Q(email=email), Q(is_active=False))
        )

        # self.assertRaises(register_new_teacher(self.parent.email))

        # register_new_teacher(self.teacher.email)
        # self.assertRaisesMessage(expected_message="Nutzer existiert bereits")

        self.teacher.is_active = False
        self.teacher.save()
        register_new_teacher(self.teacher.email)
        self.assertTrue(
            CustomUser.objects.filter(Q(role=1), Q(email=email), Q(is_active=False))
        )
