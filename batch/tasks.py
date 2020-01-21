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

    for job in jobs_to_submit:
        _submit_new_job.delay(job.id, job.project.file.data.path, job.raw_data.tar_url)


@celery_app.task(soft_time_limit=60, time_limit=90)
def _submit_new_job(job_id, project_path, tar_url):
    with contextlib.suppress(LockError), cache.lock(f"submit_job_{job_id}", timeout=90, blocking_timeout=0.001):
        project_path = Path(project_path)
        runner_cls = job_runner.get_job_runner_cls()
        runner = runner_cls()

        try:
            external_id = runner.run(project_path, tar_url)
        except Exception:
            logger.error("Failed to submit job", exc_info=1)
        else:
            updated = models.Job.objects.filter(pk=job_id, status=models.JobStatus.created.value).update(
                status=models.JobStatus.running.value, external_id=external_id
            )
            if updated != 1:
                logger.error(
                    "Conflict job %s changed state during submission orphan external_id: %s", job_id, external_id
                )


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


@celery_app.task()
def delete_done_job(auth_code, job_id, external_id):
    with contextlib.suppress(LockError), cache.lock(f"delete_task_{job_id}", timeout=30, blocking_timeout=0.001):
        runner = job_runner.HPC(auth_code)
        runner.delete_job(external_id)
        models.Job.objects.filter(pk=job_id).update(status=models.JobStatus.collected.value)


@celery_app.task()
def collect_done_jobs():
    jobs_to_collect = models.Job.objects.only("external_id").filter(
        external_id__isnull=False, status=models.JobStatus.done.value
    )

    runner = job_runner.HPC()
    token = runner.get_token()

    for job in jobs_to_collect:
        delete_done_job.delay(token, job.pk, job.external_id)
