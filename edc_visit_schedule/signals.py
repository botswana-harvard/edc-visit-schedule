from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .constants import ON_SCHEDULE
from .site_visit_schedules import site_visit_schedules, SiteVisitScheduleError


@receiver(post_save, weak=False, dispatch_uid='offschedule_model_on_post_save')
def offschedule_model_on_post_save(instance, raw, update_fields, **kwargs):
    if not raw and not update_fields:
        try:
            instance.take_off_schedule()
        except AttributeError:
            pass


@receiver(post_save, weak=False, dispatch_uid='onschedule_model_on_post_save')
def onschedule_model_on_post_save(instance, raw, update_fields, **kwargs):
    if not raw and not update_fields:
        try:
            instance.put_on_schedule()
        except AttributeError:
            pass


@receiver(post_delete, weak=False, dispatch_uid='offschedule_model_on_post_delete')
def offschedule_model_on_post_delete(instance, **kwargs):
    try:
        _, schedule = site_visit_schedules.get_by_offschedule_model(
            instance._meta.label_lower)
    except SiteVisitScheduleError:
        pass
    else:
        if schedule.offschedule_model == instance._meta.label_lower:
            history_obj = schedule.history_model_cls.objects.get(
                subject_identifier=instance.subject_identifier,
                onschedule_model=schedule.onschedule_model)
            history_obj.offschedule_datetime = None
            history_obj.schedule_status = ON_SCHEDULE
            history_obj.save()
            onschedule_model_obj = schedule.onschedule_model_cls.objects.get(
                subject_identifier=instance.subject_identifier)
            onschedule_model_obj.save()


@receiver(post_delete, weak=False, dispatch_uid='onschedule_model_on_post_delete')
def onschedule_model_on_post_delete(instance, **kwargs):
    try:
        _, schedule = site_visit_schedules.get_by_offschedule_model(
            instance._meta.label_lower)
    except SiteVisitScheduleError:
        pass
    else:
        if schedule.onschedule_model == instance._meta.label_lower:
            schedule.history_model_cls.objects.filter(
                subject_identifier=instance.subject_identifier).delete()
