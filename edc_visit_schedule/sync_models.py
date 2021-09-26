# sync_models.py
from edc_sync.site_sync_models import site_sync_models
from edc_sync.sync_model import SyncModel

sync_models = [
    'edc_visit_schedule.SubjectScheduleHistory',
]

site_sync_models.register(sync_models, SyncModel)
