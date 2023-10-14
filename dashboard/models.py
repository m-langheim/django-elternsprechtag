import uuid
import datetime

from django.db import models
from django.core.cache import cache
from authentication.models import CustomUser, Student
from django.utils import timezone

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from django.utils.translation import gettext as _

# Create your models here.


class Event(models.Model):  # Termin
    # identifier für diesen speziellen Termin
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1}
    )  # limit_choices_to={'role': 1} besagt, dass nur Nutzer, wo der Wert role glwich 1 ist eingesetzt werden können, also es wird verhindert, dass Eltern oder andere als Lehrer in Terminen gespeichert werden

    parent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": 0},
        default=None,
        null=True,
        blank=True,
        related_name="%(class)s_parent",
    )  # limit_choices_to={'role': 0} besagt, dass nur Nutzer, wo der Wert role glwich 0 ist eingesetzt werden können, also es wird verhindert, dass Lehrer oder andere als Eltern in Terminen gespeichert werden

    student = models.ManyToManyField(Student, default=None, blank=True)

    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    room = models.CharField(default=None, blank=True, null=True, max_length=3)

    STATUS_CHOICES = ((0, _("Unoccupied")), (1, _("Occupied")), (2, _("Inquiry pending")))
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)

    occupied = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')


# Allgemeine Anfragen, also Terminanfragen von den Eltern an die Lehrer und die ufforderung für ein Termin von den Eltern an die Schüler
class Inquiry(models.Model):
    CHOICES_INQUIRYTYPE = (
        (0, "Anfrage zur Buchung eines Termins (Lehrer->Eltern)"),
        (1, "Anfrage zur Bestätigung eines Termins (Eltern->Lehrer)"),
    )
    type = models.IntegerField(choices=CHOICES_INQUIRYTYPE, default=0)
    requester = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="%(class)s_requester"
    )
    students = models.ManyToManyField(Student)
    respondent = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="%(class)s_respondent",
    )
    reason = models.TextField()

    processed = models.BooleanField(default=False)
    event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, blank=True, null=True, default=None
    )

    REACTION_CHOICES = (
        (0, _("No response")),
        (1, _("Inquiry accepted")),
        (3, _("Inquiry dismissed")),
    )
    respondent_reaction = models.IntegerField(choices=REACTION_CHOICES, default=0)

    class Meta:
        verbose_name = _('Inquiry')
        verbose_name_plural = _('Inquries')


class Announcements(models.Model):
    TYPE_CHOICES = (
        (0, "Neue Buchungsanfrage"),
        (1, "Termin absage"),
        (2, "Systembenachrichtigung"),
    )
    announcement_type = models.IntegerField(choices=TYPE_CHOICES, default=0)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    action_link = models.TextField(null=True, blank=True)
    action_name = models.CharField(max_length=200, null=True, blank=True)

    read = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now)

    def encodedID(self):
        return urlsafe_base64_encode(force_bytes(self.id))
    
    class Meta:
        verbose_name = _('Announcement')
        verbose_name_plural = _('Announcements')


########################################################################### Settings ###################################################


class SingletonModel(models.Model):  # set all general setting for Singleton models
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class SiteSettings(SingletonModel):
    lead_start = models.DateField(default=timezone.now, help_text=_("Specify when all parents can book events"))
    lead_inquiry_start = models.DateField(default=timezone.now, help_text=_("Specify when parents with inquiries can start booking for corresponding events"))
    event_duration = models.DurationField(default=datetime.timedelta(seconds=0), help_text=_("Here you can set the general length of an event. The lenth applies to all events created with the function."))
    impressum = models.URLField(max_length=200, default="")

    class Meta:
        verbose_name = _('SiteSettings')
        verbose_name_plural = _('SiteSettings')
