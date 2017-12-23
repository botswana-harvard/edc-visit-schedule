import re

from django.apps import apps as django_apps

from .forms_collection import FormsCollection
from .window_period import WindowPeriod


class VisitCodeError(Exception):
    pass


class VisitDateError(Exception):
    pass


class VisitError(Exception):
    pass


class VisitDate:

    window_period_cls = WindowPeriod

    def __init__(self, **kwargs):
        self._base = None
        self._window = self.window_period_cls(**kwargs)
        self.lower = None
        self.upper = None

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self, dt=None):
        self._base = dt
        window = self._window.get_window(dt=dt)
        self.lower = window.lower
        self.upper = window.upper


class Visit:

    code_regex = r'^([A-Z0-9])+$'
    forms_collection_cls = FormsCollection
    visit_date_cls = VisitDate

    def __init__(self, code=None, timepoint=None, rbase=None, rlower=None,
                 rupper=None, crfs=None, requisitions=None, crfs_unscheduled=None,
                 requisitions_unscheduled=None, title=None,
                 instructions=None, grouping=None,
                 allow_unscheduled=None, facility_name=None):

        self.instructions = instructions
        self.timepoint = timepoint
        self.rbase = rbase
        self.rlower = rlower
        self.rupper = rupper
        self.grouping = grouping
        self.dates = self.visit_date_cls(rlower=rlower, rupper=rupper)
        self.title = title or f'Visit {code}'
        if not code or isinstance(code, int) or not re.match(self.code_regex, code):
            raise VisitCodeError(f'Invalid visit code. Got \'{code}\'')
        else:
            self.code = code  # unique
        self.name = self.code
        self.facility_name = facility_name
        self.crfs = self.forms_collection_cls(
            *(crfs or []), name=f'crfs for {self.name}').forms
        self.requisitions = self.forms_collection_cls(
            *(requisitions or []), name=f'requisitions for {self.name}').forms

        self.allow_unscheduled = allow_unscheduled
        if self.allow_unscheduled:
            self.crfs_unscheduled = self.forms_collection_cls(
                *(crfs_unscheduled or []),
                name=f'crfs crfs_unscheduled for {self.name}').forms
            self.requisitions_unscheduled = self.forms_collection_cls(
                *(requisitions_unscheduled or []),
                name=f'requisitions unscheduled for {self.name}').forms
            if not self.crfs_unscheduled and not self.requisitions_unscheduled:
                raise VisitError(
                    'allow_unscheduled is True but no unscheduled crfs '
                    f'or requisitions have been declared. See {repr(self)}')
        else:
            self.crfs_unscheduled = None
            self.requisitions_unscheduled = None

    def __repr__(self):
        return f'{self.__class__.__name__}({self.code}, {self.timepoint})'

    def __str__(self):
        return self.title

    @property
    def forms(self):
        return self.crfs + self.requisitions

    @property
    def unscheduled_forms(self):
        return self.crfs_unscheduled + self.requisitions_unscheduled

    def next_form(self, model=None, panel=None):
        """Returns the next required "form" or None.
        """
        next_form = None
        for index, form in enumerate(self.forms):
            if form.model == model and form.required:
                try:
                    next_form = self.forms[index + 1]
                except IndexError:
                    pass
        return next_form

    def get_form(self, model=None):
        for form in self.forms:
            if form.model == model:
                return form
        return None

    def get_crf(self, model=None):
        for form in self.crfs:
            if form.model == model:
                return form
        return None

    def get_requisition(self, model=None, panel_name=None):
        for form in self.requisitions:
            if form.model == model and form.panel.name == panel_name:
                return form
        return None

    @property
    def facility(self):
        """Returns a Facility object.
        """
        if self.facility_name:
            app_config = django_apps.get_app_config('edc_facility')
            return app_config.get_facility(name=self.facility_name)
        return None

    @property
    def timepoint_datetime(self):
        return self.dates.base

    @timepoint_datetime.setter
    def timepoint_datetime(self, dt=None):
        self.dates.base = dt
