from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from edc_base.utils import get_utcnow


class SubjectScheduleError(Exception):
    pass


class SubjectSchedule:
    """A class that puts a subject on to a schedule or takes a subject
    off of a schedule.

    Use `resave` to re-create any missing Appointments, for example, when the
    off study model instance is deleted.

    The visit schedule name and schedule name is taken from the
    onschedule model Meta class option.
    """

    def __init__(self, onschedule_model=None, onschedule_model_cls=None,
                 subject_identifier=None, consent_identifier=None, eligible=None,
                 onschedule_datetime=None):
        self._object = None
        self.onschedule_model_cls = onschedule_model_cls
        self.onschedule_datetime = onschedule_datetime or get_utcnow()
        if not self.onschedule_model_cls:
            self.onschedule_model_cls = django_apps.get_model(
                onschedule_model)
        self.subject_identifier = subject_identifier
        self.consent_identifier = consent_identifier
        self.eligible = eligible

    def put_on_schedule(self):
        """Returns an on-schedule model instance by get or create.
        """
        try:
            obj = self.onschedule_model_cls.objects.get(
                subject_identifier=self.subject_identifier)
        except ObjectDoesNotExist:
            self.consented_or_raise()
            obj = self.onschedule_model_cls.objects.create(
                subject_identifier=self.subject_identifier,
                consent_identifier=self.consent_identifier,
                is_eligible=self.eligible,
                onschedule_datetime=self.onschedule_datetime)
        return obj

    def take_off_schedule(self, offschedule_datetime=None, offschedule_model=None,
                          offschedule_model_cls=None):
        if not offschedule_model_cls:
            offschedule_model_cls = django_apps.get_model(
                offschedule_model)
        try:
            obj = offschedule_model_cls.objects.get(
                subject_identifier=self.subject_identifier)
        except ObjectDoesNotExist:
            self.consented_or_raise()
            obj = offschedule_model_cls.objects.create(
                subject_identifier=self.subject_identifier,
                offschedule_datetime=offschedule_datetime)
        return obj

    def resave(self):
        """Resaves the onschedule model instance to trigger, for example,
        appointment creation (if using edc_appointment mixin).
        """
        obj = self.onschedule_model_cls.objects.get(
            subject_identifier=self.subject_identifier)
        obj.save()

    def consented_or_raise(self):
        """Raises an exception if one or more consents do not exist.
        """
        consent_model_cls = django_apps.get_model(
            self.onschedule_model_cls._meta.consent_model)
        try:
            consent_model_cls.objects.get(
                subject_identifier=self.subject_identifier)
        except ObjectDoesNotExist:
            raise SubjectScheduleError(
                f'Failed to put subject on schedule. Consent not found. '
                f'Using consent model \'{self.onschedule_model_cls._meta.consent_model}\' '
                f'subject identifier={self.subject_identifier}.')
        except MultipleObjectsReturned:
            pass