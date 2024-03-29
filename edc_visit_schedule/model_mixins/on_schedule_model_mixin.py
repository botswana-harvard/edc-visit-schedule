from django.db import models
from edc_base import get_utcnow
from edc_base.model_validators.date import datetime_not_future
from edc_protocol.validators import datetime_not_before_study_start

from ..site_visit_schedules import site_visit_schedules
from .schedule_model_mixin import ScheduleModelMixin


class OnScheduleModelMixin(ScheduleModelMixin):
    """A model mixin for a schedule's onschedule model.
    """
    onschedule_datetime = models.DateTimeField(
        validators=[
            datetime_not_before_study_start,
            datetime_not_future],
        default=get_utcnow)

    schedule_name = models.CharField(
        max_length=25,
        null=True,
        blank=True)

    def save(self, *args, **kwargs):
        self.report_datetime = self.onschedule_datetime
        super().save(*args, **kwargs)

    def put_on_schedule(self):
        _, schedule = site_visit_schedules.get_by_onschedule_model(
            self._meta.label_lower)
        schedule.put_on_schedule(onschedule_model_obj=self)

    class Meta:
        abstract = True
