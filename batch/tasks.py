import logging
import contextlib

from config import celery_app
from pathlib import Path
from django.core.cache import cache
from redis.exceptions import LockError

from . import models, job_runner

logger = logging.getLogger(__name__)


@celery_app.task()
def submit_new_jobs():
    """Submit newly created tasks"""
    jobs_to_submit = models.Job.objects.only("project__file", "raw_data__url").filter(
        status=models.JobStatus.created.value
    )

    runner = job_runner.HPC()

    for job in jobs_to_submit:
        project_path = Path(job.project.file.data.path)
        try:
            external_id = runner.run(project_path, job.raw_data.tar_url)
        except Exception:
            logger.error("Failed to submit job", exc_info=1)
        else:
            job.external_id = external_id
            job.status = models.JobStatus.running.value
            job.save()


@celery_app.task()
def check_for_failed_jobs(auth_code, job_id, external_id):
    with contextlib.suppress(LockError), cache.lock(f"task_{job_id}", timeout=30, blocking_timeout=0.001):
        runner = job_runner.HPC(auth_code)
        status = runner.check_status(external_id)
        if status == models.JobStatus.failed:
            models.Job.objects.filter(pk=job_id, status=models.JobStatus.running.value).update(status=status.value)


@celery_app.task()
def check_running_jobs():
    jobs_to_check = models.Job.objects.only("external_id").filter(
        external_id__isnull=False, status=models.JobStatus.running.value
    )
    runner = job_runner.HPC()
    token = runner.get_token()

    for job in jobs_to_check:
        check_for_failed_jobs.delay(token, job.pk, job.external_id)
