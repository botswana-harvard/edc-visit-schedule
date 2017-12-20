from django.db import models
from django.db.models import options
from edc_base.model_validators import datetime_not_future
from edc_base.utils import get_utcnow
from edc_identifier.model_mixins import NonUniqueSubjectIdentifierFieldMixin
from edc_protocol.validators import datetime_not_before_study_start

from ..offschedule_validator import OffScheduleValidator
from .subject_schedule_model_mixin import SubjectScheduleModelMixin


if 'visit_schedule_name' not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('visit_schedule_name',)


class OffScheduleModelMixin(NonUniqueSubjectIdentifierFieldMixin,
                            SubjectScheduleModelMixin, models.Model):
    """A model mixin for a schedule's offschedule model.
    """

    offschedule_validator_cls = OffScheduleValidator

    offschedule_datetime = models.DateTimeField(
        validators=[
            datetime_not_before_study_start,
            datetime_not_future],
        default=get_utcnow)

    def save(self, *args, **kwargs):
        self.offschedule_validator_cls(
            subject_identifier=self.subject_identifier,
            offschedule_datetime=self.offschedule_datetime,
            visit_schedule_name=self._meta.visit_schedule_name.split('.')[0],
            schedule_name=self._meta.visit_schedule_name.split('.')[1])
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        visit_schedule_name = None
        unique_together = (
            'subject_identifier', 'visit_schedule_name', 'schedule_name')