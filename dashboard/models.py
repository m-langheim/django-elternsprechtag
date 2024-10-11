import uuid
import datetime

from django.db import models
from django.core.cache import cache
from authentication.models import CustomUser, Student
from django.utils import timezone

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes

from django.utils.translation import gettext as _
from django.db.models import Q


class LeadStatusChoices(models.IntegerChoices):
    NOBODY = 0, _("Nobody can currently request this appointment.")
    CONDITION = 1, _(
        "Only parents with special authorisations can currently request this appointment."
    )
    INQUIRY = 2, _(
        "Only parents who have received a request from the teacher can currently request this appointment."
    )
    ALL = 3, _("All parents can request this appointment at the moment.")


# Create your models here.
class BaseEventGroup(models.Model):
    def get_default_valid_until():
        return timezone.now() + timezone.timedelta(days=7)

    lead_start = models.DateField(
        default=timezone.now,
        help_text=_(
            "Set a date from which all parents can request appointments."
        ),  # Specify when all parents can book events
    )

    lead_inquiry_start = models.DateField(
        default=timezone.now,
        help_text=_(
            _(
                "Determine when teachers' enquiries can be answered."
            )  # Specify when parents with inquiries can start booking for corresponding events
        ),
    )

    valid_until = models.DateField(default=get_default_valid_until)

    # LEAD_STATUS_CHOICES = (
    #     (
    #         0,
    #         _("Nobody can currently request this appointment."),
    #     ),  # No one is allowed to book this event
    #     (
    #         1,
    #         _(
    #             "Only parents with special authorisations can currently request this appointment."
    #         ),  # Only parents with special treatment are currently allowed to book this event.
    #     ),
    #     (
    #         2,
    #         _(
    #             "Only parents who have received a request from the teacher can currently request this appointment."
    #         ),  # All parents who received an inquiry from this teacher are allowed to book this event.
    #     ),
    #     (
    #         3,
    #         _("All parents can request this appointment at the moment."),
    #     ),  # All parents are allowed to book this event.
    # )

    lead_status = models.IntegerField(choices=LeadStatusChoices, default=1)

    lead_status_last_change = models.DateTimeField(default=timezone.now)

    force = models.BooleanField(default=False)

    manual_apply = models.BooleanField(default=False)

    disable_automatic_changes = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        days = DayEventGroup.objects.filter(base_event=self).order_by("date")
        title_str = _(f"Parent-teacher conference on ")

        for index, day in enumerate(days):
            if index == 0:
                title_str += f"{day.date.strftime('%d.%m.%Y')}"
            elif index == days.count() - 1:
                title_str += _(" and ") + f"{day.date.strftime('%d.%m.%Y')}"
            else:
                title_str += f", {day.date.strftime('%d.%m.%Y')}"
        return title_str


class DayEventGroup(models.Model):
    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE, null=True)
    date = models.DateField(default=timezone.now)

    lead_start = models.DateField(
        default=timezone.now,
        help_text=_("Set a date from which all parents can request appointments."),
    )

    lead_inquiry_start = models.DateField(
        default=timezone.now,
        help_text=_(
            "Determine when teachers' enquiries can be answered."  # Specify when parents with inquiries can start booking for corresponding events
        ),
    )

    # LEAD_STATUS_CHOICES = (
    #     (0, "Nobody can currently request this appointment."),
    #     (
    #         1,
    #         "Only parents with special authorisations can currently request this appointment.",
    #     ),
    #     (
    #         2,
    #         "Only parents who have received a request from the teacher can currently request this appointment.",
    #     ),
    #     (3, "All parents can request this appointment at the moment."),
    # )

    lead_status = models.IntegerField(choices=LeadStatusChoices, default=1)

    lead_status_last_change = models.DateTimeField(default=timezone.now)

    force = models.BooleanField(default=False)

    manual_apply = models.BooleanField(default=False)

    lead_manual_override = models.BooleanField(default=False)

    disable_automatic_changes = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"Event group - {str(self.date)}"


class TeacherEventGroup(models.Model):
    # date = models.DateField(default=timezone.now)
    day_group = models.ForeignKey(DayEventGroup, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1}
    )

    lead_start = models.DateField(
        default=timezone.now,
        help_text=_("Set a date from which all parents can request appointments."),
    )

    lead_inquiry_start = models.DateField(
        default=timezone.now,
        help_text=_("Determine when teachers' enquiries can be answered."),
    )

    lead_end_timedelta = models.DurationField(default=timezone.timedelta(hours=1))
    lead_allow_same_day = models.BooleanField(default=True)

    # LEAD_STATUS_CHOICES = (
    #     (0, "Nobody can currently request this appointment."),
    #     (
    #         1,
    #         "Only parents with special authorisations can currently request this appointment.",
    #     ),
    #     (
    #         2,
    #         "Only parents who have received a request from the teacher can currently request this appointment.",
    #     ),
    #     (3, "All parents can request this appointment at the moment."),
    # )

    lead_status = models.IntegerField(choices=LeadStatusChoices, default=1)

    lead_status_last_change = models.DateTimeField(default=timezone.now)

    force = models.BooleanField(default=False)

    manual_apply = models.BooleanField(default=False)

    lead_manual_override = models.BooleanField(default=False)

    disable_automatic_changes = models.BooleanField(default=False)

    room = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return f"{self.teacher} - {str(self.day_group.date)}"


class Event(models.Model):  # Termin
    # identifier für diesen speziellen Termin
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE, null=True)
    day_group = models.ForeignKey(DayEventGroup, on_delete=models.CASCADE, null=True)
    teacher = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, limit_choices_to={"role": 1}
    )  # limit_choices_to={'role': 1} besagt, dass nur Nutzer, wo der Wert role glwich 1 ist eingesetzt werden können, also es wird verhindert, dass Eltern oder andere als Lehrer in Terminen gespeichert werden
    teacher_event_group = models.ForeignKey(
        TeacherEventGroup, on_delete=models.CASCADE, null=True
    )
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
    lead_status = models.IntegerField(choices=LeadStatusChoices, default=1)

    lead_status_last_change = models.DateTimeField(default=timezone.now)

    lead_manual_override = models.BooleanField(default=False)

    disable_automatic_changes = models.BooleanField(default=False)

    class StatusChoices(models.IntegerChoices):
        UNOCCUPIED = 0, _("Unoccupied")
        OCCUPIED = 1, _("Occupied")
        INQUIRY = 2, _("Inquiry pending")

    status = models.IntegerField(choices=StatusChoices, default=0)

    occupied = models.BooleanField(default=False)

    class PersonalEventStatusChoices:
        EVENT_BOOKABLE = 0, _("Event bookable")
        INQUIRY_PENDING = 1, _("Inquiry pending")
        BOOKED = 2, _("Booked")
        OCCUPIED = 3, _("Occupied")
        BLOCKED = 4, _("Blocked")
        TIME_CONFLICT = 5, _("Time conflict")
        TIME_CONFLICT_FOLLOWUP = 6, _("Followup event")

    def get_event_lead_data(self):
        return self.teacher_event_group

    def check_time_lead_active(self):
        event_group = self.get_event_lead_data()
        event_in_future = self.start > timezone.now()
        lead_started = event_group.lead_start <= timezone.now().date()
        event_same_day = (
            event_group.lead_allow_same_day or self.start.date() > timezone.now().date()
        )

        if (
            event_in_future and lead_started and event_same_day
        ) or self.lead_status == 3:
            return True

        return False

    def check_time_lead_inquiry_active(self):
        event_group = self.get_event_lead_data()
        event_in_future = event_group.start > timezone.now()
        lead_inquiry_started = event_group.lead_inquiry_start <= timezone.now().date()
        event_same_day = (
            event_group.lead_allow_same_day or self.start.date() > timezone.now().date()
        )

        if (
            event_in_future and lead_inquiry_started and event_same_day
        ) or self.lead_status >= 2:
            return True

        return False

    def update_event_lead_status(self, automatic=True, force=False):
        if automatic and self.disable_automatic_changes and not force:
            pass
        else:
            if timezone.now() >= self.end:
                self.lead_status = LeadStatusChoices.NOBODY
                self.lead_manual_override = True
                self.disable_automatic_changes = True
                self.save()
            elif (
                self.teacher_event_group.lead_status_last_change
                >= self.lead_status_last_change
                and (
                    not self.lead_manual_override
                    or (self.lead_manual_override and force)
                )
            ):
                self.lead_status = self.teacher_event_group.lead_status
                self.lead_status_last_change = timezone.now()

                self.save()

    def check_parent_can_book_event(self, parent: CustomUser) -> bool:
        """This function is designed to check if a specified parent user account is allowed to book the specific event.

        Args:
            parent (CustomUser): Pass in the parent

        Returns:
            bool: Describes wether or not the parent is able to book this specific event
        """
        if parent.role != 0:
            raise ValueError(
                _("This user is not a parent.")
            )  # The specified user is not a parent.
        if self.lead_status == LeadStatusChoices.ALL:
            return True
        elif (
            self.lead_status == LeadStatusChoices.INQUIRY
            and Inquiry.objects.filter(
                Q(requester=self.teacher), Q(respondent=parent), Q(processed=False)
            ).exists()
        ):
            return True
        elif self.lead_status == LeadStatusChoices.CONDITION and parent.has_perm(
            "dashboard.condition_prebook_event"
        ):
            return True
        return False

    def get_parent_event_individual_status(self, parent: CustomUser):
        match self.status:
            case self.StatusChoices.OCCUPIED:
                if self.parent == parent:
                    return True, self.PersonalEventStatusChoices.BOOKED
                else:
                    return False, self.PersonalEventStatusChoices.OCCUPIED
            case self.StatusChoices.INQUIRY:
                if self.parent == parent:
                    return True, self.PersonalEventStatusChoices.INQUIRY_PENDING
                else:
                    return False, self.PersonalEventStatusChoices.OCCUPIED
            case self.StatusChoices.UNOCCUPIED:
                match self.lead_status:
                    case LeadStatusChoices.NOBODY:
                        return False, self.PersonalEventStatusChoices.BLOCKED
                    case LeadStatusChoices.CONDITION:
                        if parent.has_perm("dashboard.condition_prebook_event"):
                            return True, self.PersonalEventStatusChoices.EVENT_BOOKABLE
                        else:
                            return False, self.PersonalEventStatusChoices.BLOCKED
                    case LeadStatusChoices.INQUIRY:
                        if Inquiry.objects.filter(
                            Q(respondent=parent),
                            Q(processed=False),
                            Q(base_event=self.get_base_event()),
                        ).exists():
                            return True, self.PersonalEventStatusChoices.EVENT_BOOKABLE
                        else:
                            return False, self.PersonalEventStatusChoices.BLOCKED
                    case LeadStatusChoices.ALL:
                        min_event_seperation = (
                            SiteSettings.objects.first().min_event_seperation
                        )
                        if (
                            Event.objects.filter(Q(parent=parent))
                            .exclude(end__lte=self.start)
                            .exclude(start__gte=self.end)
                            .exists()
                        ):
                            return False, self.PersonalEventStatusChoices.TIME_CONFLICT
                        elif (
                            Event.objects.filter(Q(parent=parent))
                            .exclude(start__gt=self.end + min_event_seperation)
                            .exclude(end__lt=self.start - min_event_seperation)
                            .exists()
                        ):
                            follow_up_event_bookable = (
                                SiteSettings.objects.first().event_in_seperation_bookable
                            )
                            if follow_up_event_bookable:
                                return (
                                    True,
                                    self.PersonalEventStatusChoices.TIME_CONFLICT_FOLLOWUP,
                                )
                            else:
                                return (
                                    False,
                                    self.PersonalEventStatusChoices.TIME_CONFLICT,
                                )
                        else:
                            return True, self.PersonalEventStatusChoices.EVENT_BOOKABLE

    def get_base_event(self):
        return self.teacher_event_group.day_group.base_event

    def __str__(self):
        return (
            _("Appointment from ")
            + f"{self.teacher}"
            + _(" on ")
            + f"{self.start.date()}"
            + _(" from ")
            + f"{self.start.time()}"
            + _(" to ")
            + f"{self.end.time()}"
        )
        # return f"Termin von {self.teacher} am {self.start.date()} von {self.start.time()} bis {self.end.time()}"

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        permissions = [
            (
                "book_event",
                _(
                    "The user is allowed to book an event. Without this permission the user will be completely blocked from booking."
                ),  # Dieser User darf Termin buchen. Ohne diese Berechtigung ist er komplett ausgeschlossen vom Buchen von Terminen.
            ),  #! Aktuell nicht in Benutzung
            (
                "condition_prebook_event",
                _(
                    "The user is allowed to book an event before the official booking period because he has an e.g. medical condition."
                ),  # Dieser User darf aus z.B. medizinischen Gründen einen Termin vor der offiziellen Buchungsphasen anfragen.
            ),
            (
                "book_double_event",
                _(
                    "The user is allowed to book a double event with all teachers because of an medical condition."
                ),  # Dieser User darf aus z.B. medizinischen Gründen auch Doppeltermine bei einer Lehrkraft anfragen.
            ),  #! Aktuell nicht in Benutzung
        ]


class EventChangeFormula(models.Model):
    """
    Dieses Model dient dazu, jedem Lehrer die Möglichkeit zu geben, seine Zeiten für den Elternsprtechtag selber einzurrichten. In Zukunft können hier auch Anträge auf die Blockierung einzelner Termine eingereicht werden.
    """

    # id = models.UUIDField(unique=True, default=uuid.uuid4, primary_key=True)

    class FormularTypeChoices(models.IntegerChoices):
        TIME_PERIODS = 0, _("Time period")
        BREAKS = 1, _("Break request")
        ILLNESS = 2, _("Sick leave")

    # TYPE_CHOICES = ((0, _("Submit own time periods.")),)  # Submit of personal timeslots
    type = models.IntegerField(
        choices=FormularTypeChoices, default=FormularTypeChoices.TIME_PERIODS
    )
    # parent_formular = models.ForeignKey(
    #     "self",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     related_name="childformular",
    # )
    day_group = models.ForeignKey(
        DayEventGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    teacher_event_group = models.ForeignKey(
        TeacherEventGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={"role": 1},
        blank=False,
        verbose_name=_("Teacher"),
    )
    date = models.DateField(blank=False, default=timezone.now, verbose_name=_("Date"))
    start_time = models.TimeField(blank=True, null=True, verbose_name=_("Start time"))
    end_time = models.TimeField(blank=True, null=True, verbose_name=_("End time"))

    no_events = models.BooleanField(default=False, verbose_name=_("No events"))

    class FormularStatusChoices(models.IntegerChoices):
        PENDING_PROCESSING = 0, _("Wait for processing")
        PENDING_CONFIRMATION = 1, _("Wait for confirmation")
        APPROVED = 2, _("Approved")
        DECLINED = 3, _("Declined")
        REMOVED = 4, _("Removed")

    # CHOICES_STATUS = (
    #     (0, _("Wait for processing")),  # Waiting to be filled
    #     (1, _("Wait for confirmation")),  # Waiting for approval
    #     (2, _("Approved")),  # Approved
    #     (3, _("Declined")),  # Disapproved
    # )
    status = models.IntegerField(
        choices=FormularStatusChoices, default=FormularStatusChoices.PENDING_PROCESSING
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = _("Event creation formula")
        verbose_name_plural = _("Event creation formulas")
        permissions = [
            (
                "approve_disapprove",
                _(
                    "Can accept or reject submitted time periods for other users."
                ),  # Can approve/disapprove the formulars for other users
            )
        ]


# Allgemeine Anfragen, also Terminanfragen von den Eltern an die Lehrer und die ufforderung für ein Termin von den Eltern an die Schüler
class Inquiry(models.Model):
    class InquiryTypeChoices(models.IntegerChoices):
        TEACHER_REQUEST = 0, _("Inquiry to book an appointment (teacher->parents)")
        APPOINTEMENT_REQUEST = 1, _(
            "Request for confirmation of an appointment (parent->teacher)"
        )

    # CHOICES_INQUIRYTYPE = (
    #     (0, _("Inquiry to book an appointment (teacher->parents)")),
    #     (1, _("Request for confirmation of an appointment (parent->teacher)")),
    # )
    base_event = models.ForeignKey(BaseEventGroup, on_delete=models.CASCADE, null=True)
    type = models.IntegerField(
        choices=InquiryTypeChoices, default=InquiryTypeChoices.TEACHER_REQUEST
    )
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

    class InquiryReactionChoices(models.IntegerChoices):
        NO_RESPONSE = 0, _("No response")
        ACCEPTED = 1, _("Inquiry accepted")
        DECLINED = 3, _("Inquiry declined")

    # REACTION_CHOICES = (
    #     (0, _("No response")),  # No response
    #     (1, _("Inquiry accepted")),  # Inquiry accepted
    #     (3, _("Inquiry declined")),  # Inquiry dismissed
    # )
    respondent_reaction = models.IntegerField(
        choices=InquiryReactionChoices, default=InquiryReactionChoices.NO_RESPONSE
    )
    notified = models.BooleanField(default=False)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Inquiry")
        verbose_name_plural = _("Inquries")


class Announcements(models.Model):
    class AnnouncementTypeChoices(models.IntegerChoices):
        BOOKINK_INQUIRY = 0, _("New booking inquiry")
        APPOINTEMENT_CANCELLATION = 1, _("Appointment cancellation")
        SYSTEM_NOTIFICATION = 2, _("System notification")

    # TYPE_CHOICES = (
    #     (0, _("New booking inquiry")),
    #     (1, _("Appointment cancellation")),
    #     (2, _("System notification")),
    # )
    announcement_type = models.IntegerField(
        choices=AnnouncementTypeChoices, default=AnnouncementTypeChoices.BOOKINK_INQUIRY
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    action_link = models.TextField(null=True, blank=True)
    action_name = models.CharField(max_length=200, null=True, blank=True)

    read = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now)

    def encodedID(self):
        return urlsafe_base64_encode(force_bytes(self.id))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


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
    lead_start = models.DateField(
        default=timezone.now,
        help_text=_("Set a date from which all parents can request appointments."),
    )
    lead_inquiry_start = models.DateField(
        default=timezone.now,
        help_text=_("Determine when teachers' enquiries can be answered."),
    )
    event_duration = models.DurationField(
        default=datetime.timedelta(minutes=7, seconds=30),
        help_text=_(
            "Here you define the general length of an appointment. It applies to all appointments created with this function."
        ),  # Here you can set the general length of an event. The lenth applies to all events created with the function.
    )
    min_event_seperation = models.DurationField(
        default=timezone.timedelta(minutes=5),
        help_text=_(
            "Here you can set the interval between two appointments. You should allow some time to change rooms etc."
        ),  # Here you can set the time between two events a parent can book. You should enter some time here to account for overtime and change of rooms.
    )
    event_in_seperation_bookable = models.BooleanField(default=False)
    impressum = models.URLField(max_length=200, default="")
    keep_events = models.DurationField(default=timezone.timedelta(days=30))
    delete_events = models.BooleanField(default=True)
    keep_student_changes = models.DurationField(default=timezone.timedelta(days=60))
    delete_student_changes = models.BooleanField(default=False)
    keep_announcements = models.DurationField(default=timezone.timedelta(days=30))
    delete_announcements = models.BooleanField(default=True)
    keep_event_change_formulas = models.DurationField(
        default=timezone.timedelta(days=30)
    )
    delete_event_change_formulas = models.BooleanField(default=False)

    def get_default_inquiry_behavior():
        return [
            dict({"type": 0, "delete": True, "keep_for_days": 30}),
            dict({"type": 1, "delete": True, "keep_for_days": 30}),
        ]

    iquiry_bahvior = models.JSONField(default=get_default_inquiry_behavior)

    class Meta:
        verbose_name = _("SiteSettings")
        verbose_name_plural = _("SiteSettings")
