import logging
from pathlib import Path

from django.conf import settings
from django.utils import module_loading

import hpc

from . import models


logger = logging.getLogger(__name__)

_30_MINUTES = 30 * 60


def get_job_runner_cls():
    return module_loading.import_string(settings.JOB_RUNNER)


class HPC:
    _OWN_STATUS_BY_UNICORE = {
        "SUCCESSFUL": models.JobStatus.done,
        "QUEUED": models.JobStatus.running,
        "STAGINGIN": models.JobStatus.running,
        "STAGINGOUT": models.JobStatus.running,
        "READY": models.JobStatus.running,
        "RUNNING": models.JobStatus.running,
        "FAILED": models.JobStatus.failed,
    }

    def __init__(self, access_token=None):
        self._env = hpc.HpcEnvironment(
            HBP_REFRESH_TOKEN=settings.HBP_REFRESH_TOKEN,
            HBP_APP_ID=settings.HBP_APP_ID,
            HBP_APP_SECRET=settings.HBP_APP_SECRET,
            HPC_PATH_PREFIX=settings.HPC_PATH_PREFIX,
            access_token=access_token,
        )
        self._os_env = hpc.CscsOpenstackEnvironment(
            OS_USERNAME=settings.OS_USERNAME,
            OS_PASSWORD=settings.OS_PASSWORD
        )

    def run(self, project_path: Path, data_url: str) -> str:
        jobspec = hpc.PixelClassificationJobSpec(
            hpc_environment=self._env,
            openstack_environment=self._os_env,
            ILASTIK_PROJECT_FILE=project_path,
            ILASTIK_RAW_DATA=data_url,
            ILASTIK_JOB_RESULT_ENDPOINT=settings.HPC_JOB_RESULT_ENDPOINT,
            Resources=hpc.JobResources(CPUs=10, Memory="32G", Runtime=_30_MINUTES),
        )
        unicore_job = jobspec.run()
        return unicore_job.job_id

    def check_status(self, job_id: str) -> models.JobStatus:
        job = self._env.get_job(job_id)
        unicore_status = job.properties["status"]
        own_status = self._OWN_STATUS_BY_UNICORE.get(unicore_status, None)

        if own_status is None:
            logger.warning("Unknown status %s for job %s", unicore_status, job_id)
            own_status = models.JobStatus.running

        return own_status

    def delete_job(self, job_id: str) -> None:
        job = self._env.get_job(job_id)
        job.delete()

    def get_token(self):
        return self._env.get_token()
