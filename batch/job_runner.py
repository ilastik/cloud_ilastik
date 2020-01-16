from __future__ import annotations

from pathlib import Path

from django.conf import settings

import hpc


_30_MINUTES = 30 * 60


class HPC:
    def __init__(self):
        pass

    def run(self, project_path: Path, data_url: str) -> str:
        jobspec = hpc.IlastikJobSpec(
            ilp_project=project_path,
            raw_data_url=data_url,
            result_endpoint=settings.HPC_JOB_RESULT_ENDPOINT,
            Resources=hpc.JobResources(CPUs=10, Memory="32G", Runtime=_30_MINUTES),
        )
        unicore_job = jobspec.run()
        return unicore_job.job_id
