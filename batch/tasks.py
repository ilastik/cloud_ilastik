from config import celery_app

from . import models


@celery_app.task()
def submit_new_tasks():
    """Submit newly created tasks"""
    jobs_to_submit = models.Job.objects.filter(status=models.JobStatus.created.value)
    return len(jobs_to_submit)
