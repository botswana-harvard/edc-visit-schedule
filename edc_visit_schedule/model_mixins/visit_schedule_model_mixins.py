from django.db import models
from django.db.models import options


from ..site_visit_schedules import site_visit_schedules, RegistryNotLoaded
from ..site_visit_schedules import SiteVisitScheduleError
from ..visit_schedule import VisitScheduleError

if 'visit_schedule_name' not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('visit_schedule_name',)


class VisitScheduleMethodsError(Exception):
    pass


class VisitScheduleMetaMixin(models.Model):

    """Adds the \'visit_schedule_name\' Meta class attribute.
    """

    class Meta:
        abstract = True
        visit_schedule_name = None


class VisitScheduleMethodsModelMixin(models.Model):
    """A model mixin that adds methods used to work with the visit schedule.

    Declare with VisitScheduleFieldsModelMixin or the fields from
    VisitScheduleFieldsModelMixin
    """

    @property
    def visit(self):
        return self.schedule.visits.get(self.visit_code)

    @property
    def visits(self):
        return self.schedule.visits

    @property
    def schedule(self):
        """Returns a schedule object from Meta.visit_schedule_name or
        self.schedule_name.

        Declared on Meta like this:
            visit_schedule_name = 'visit_schedule_name.schedule_name'
        """
        try:
            _, schedule_name = self._meta.visit_schedule_name.split('.')
        except ValueError as e:
            raise VisitScheduleMethodsError(
                f'{self.__class__.__name__}. Got {e}') from e
        except AttributeError as e:
            if 'visit_schedule_name' in str(e):
                return self.visit_schedule.get_schedule(schedule_name=self.schedule_name)
        return self.visit_schedule.get_schedule(schedule_name=schedule_name)

    @property
    def visit_schedule(self):
        """Returns a visit schedule object from Meta.visit_schedule_name.

        Declared on Meta like this:
            visit_schedule_name = 'visit_schedule_name.schedule_name'
        """
        try:
            visit_schedule_name, _ = self._meta.visit_schedule_name.split('.')
        except ValueError as e:
            raise VisitScheduleMethodsError(
                f'{self.__class__.__name__}. Got {e}') from e
        except AttributeError as e:
            visit_schedule_name = self.visit_schedule_name
        try:
            visit_schedule = site_visit_schedules.get_visit_schedule(
                visit_schedule_name=visit_schedule_name)
        except RegistryNotLoaded as e:
            raise VisitScheduleMethodsError(
                f'visit_schedule_name: \'{visit_schedule_name}\'. Got {e}') from e
        except SiteVisitScheduleError as e:
            raise VisitScheduleMethodsError(
                f'visit_schedule_name: \'{visit_schedule_name}\'. Got {e}') from e
        return visit_schedule

    class Meta:
        abstract = True


class VisitScheduleFieldsModelMixin(models.Model):
    """A model mixin that adds fields required to work with the visit
    schedule methods on the VisitScheduleMethodsModelMixin.

    Note: visit_code is not included."""

    visit_schedule_name = models.CharField(
        max_length=25,
        editable=False,
        help_text='the name of the visit schedule used to find the "schedule"')

    schedule_name = models.CharField(
        max_length=25,
        editable=False)

    class Meta:
        abstract = True


class VisitScheduleModelMixin(VisitScheduleFieldsModelMixin,
                              VisitScheduleMethodsModelMixin,
                              models.Model):

    """A model mixin that adds adds field attributes and methods that
    link a model instance to its schedule.

    This mixin is used with Appointment and Visit models via their
    respective model mixins.
    """

    visit_code = models.CharField(
        max_length=25,
        null=True,
        editable=False)

    visit_code_sequence = models.IntegerField(
        verbose_name=('Sequence'),
        default=0,
        null=True,
        blank=True,
        help_text=('An integer to represent the sequence of additional '
                   'appointments relative to the base appointment, 0, needed '
                   'to complete data collection for the timepoint. (NNNN.0)'))

    def save(self, *args, **kwargs):
        # set field attrs
        self.visit_schedule_name, self.schedule_name = (
            self._meta.visit_schedule_name.split('.'))
        # Asserts model's visit schedule/schedule is
        # registered/added or raises.
        try:
            visit_schedule = site_visit_schedules.get_visit_schedule(
                visit_schedule_name=self.visit_schedule_name)
        except (SiteVisitScheduleError, VisitScheduleError) as e:
            raise VisitScheduleError(
                f'Visit Schedule not found. Model {repr(self)} Got {e}') from e
        try:
            visit_schedule.get_schedule(
                schedule_name=self.schedule_name)
        except (SiteVisitScheduleError, VisitScheduleError) as e:
            raise VisitScheduleError(
                f'Schedule not found. Model {repr(self)} Got {e}') from e
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        visit_schedule_name = None
