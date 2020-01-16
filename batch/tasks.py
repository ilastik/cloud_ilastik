import logging

from config import celery_app
from pathlib import Path

from . import models, job_runner

logger = logging.getLogger(__name__)


@celery_app.task()
def submit_new_tasks():
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
