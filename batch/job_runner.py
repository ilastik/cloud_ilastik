from pathlib import Path

from django.conf import settings

import hpc


_30_MINUTES = 30 * 60


class HPC:
    def __init__(self):
        self._env = hpc.HpcEnvironment(
            HBP_REFRESH_TOKEN=settings.HBP_REFRESH_TOKEN,
            HBP_APP_ID=settings.HBP_APP_ID,
            HBP_APP_SECRET=settings.HBP_APP_SECRET,
            HPC_PYTHON_EXECUTABLE=settings.HPC_PYTHON_EXECUTABLE,
            HPC_ILASTIK_PATH=settings.HPC_ILASTIK_PATH,
            S3_KEY=settings.S3_KEY,
            S3_SECRET=settings.S3_SECRET,
        )

    def run(self, project_path: Path, data_url: str) -> str:
        jobspec = hpc.IlastikJobSpec(
            hpc_environment=self._env,
            ilp_project=project_path,
            raw_data_url=data_url,
            result_endpoint=settings.HPC_JOB_RESULT_ENDPOINT,
            Resources=hpc.JobResources(CPUs=10, Memory="32G", Runtime=_30_MINUTES),
        )
        unicore_job = jobspec.run()
        return unicore_job.job_id
