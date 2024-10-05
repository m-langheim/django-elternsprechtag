from .models import *
import factory

from factory.django import DjangoModelFactory


class SettingsFactory(DjangoModelFactory):
    class Meta:
        model = SiteSettings

    impressum = factory.Faker("url")
