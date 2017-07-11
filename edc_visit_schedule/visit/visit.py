import re

from .forms_collection import FormsCollection
from .window_period import WindowPeriod


class VisitCodeError(Exception):
    pass


class VisitDateError(Exception):
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
        if not self._base:
            self._base = dt
            window = self._window.get_window(dt=dt)
            self.lower = window.lower
            self.upper = window.upper


class Visit:

    code_regex = r'^([A-Z0-9])+$'
    forms_collection_cls = FormsCollection
    visit_date_cls = VisitDate

    def __init__(self, code=None, timepoint=None, rbase=None,
                 crfs=None, requisitions=None, title=None,
                 instructions=None, grouping=None, **kwargs):

        self.dates = self.visit_date_cls(**kwargs)
        self.title = title or f'Visit {code}'
        if not code or isinstance(code, int) or not re.match(self.code_regex, code):
            raise VisitCodeError(f'Invalid visit code. Got \'{code}\'')
        else:
            self.code = code  # unique
        self.name = self.code
        self.crfs = self.forms_collection_cls(*(crfs or []), **kwargs).items
        self.requisitions = self.forms_collection_cls(
            *(requisitions or []), **kwargs).items

        self.instructions = instructions
        self.timepoint = timepoint
        self.rbase = rbase
        self.grouping = grouping

    def __repr__(self):
        return f'Visit({self.code}, {self.timepoint})'

    def __str__(self):
        return self.title

    @property
    def timepoint_datetime(self):
        return self.dates.base

    @timepoint_datetime.setter
    def timepoint_datetime(self, dt=None):
        self.dates.base = dt