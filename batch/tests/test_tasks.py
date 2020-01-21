import pytest


from batch.tests import factories
from batch import tasks, models


@pytest.mark.django_db
def test_job_submission(settings):
    """A basic test to execute the get_users_count Celery task."""

    created_jobs = factories.JobFactory.create_batch(3, status=models.JobStatus.created.value)
    settings.CELERY_TASK_ALWAYS_EAGER = True

    tasks.submit_new_jobs()
    db_jobs = models.Job.objects.filter(id__in=[j.id for j in created_jobs])

    assert len(db_jobs) == 3
    for job in db_jobs:
        assert models.JobStatus.running.value == job.status
