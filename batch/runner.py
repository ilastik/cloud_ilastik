import abc
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Union
from urllib.parse import urljoin

import jwt
import pyunicore.client
from django.conf import settings
from keystoneauth1 import session
from keystoneauth1.extras._saml2 import V3Saml2Password
from keystoneauth1.identity import v3

from batch import models


class JobRunner(abc.ABC):
    @abc.abstractmethod
    def submit(self, *, project_path: Union[str, bytes, os.PathLike], data_url: str) -> str:
        pass

    @abc.abstractmethod
    def status(self, id: str) -> models.JobStatus:
        pass

    @abc.abstractmethod
    def delete(self, id: str) -> None:
        pass


class UnicoreJobRunner(JobRunner):
    _STATUSES = {
        "SUCCESSFUL": models.JobStatus.done,
        "QUEUED": models.JobStatus.running,
        "STAGINGIN": models.JobStatus.running,
        "STAGINGOUT": models.JobStatus.running,
        "READY": models.JobStatus.running,
        "RUNNING": models.JobStatus.running,
        "FAILED": models.JobStatus.failed,
    }

    def __init__(self):
        refresh_config = {
            "client_id": settings.HBP_APP_ID,
            "client_secret": settings.HBP_APP_SECRET,
            "refresh_token": settings.HBP_REFRESH_TOKEN,
            "url": settings.HBP_REFRESH_URL,
        }
        transport = pyunicore.client.Transport(
            None, refresh_handler=_LeewayRefreshHandler(refresh_config, leeway=settings.HBP_REFRESH_LEEWAY)
        )
        sites = pyunicore.client.get_sites(transport)
        self._client = pyunicore.client.Client(transport, sites[settings.HBP_SITE])

        # https://user.cscs.ch/storage/object_storage/usage_examples/tokens/
        unscoped_auth = V3Saml2Password(
            username=settings.OS_USERNAME, password=settings.OS_PASSWORD, **settings.OS_SAML_PASSWORD_AUTH_PARAMS
        )
        scoped_auth = v3.Token(
            auth_url=unscoped_auth.auth_url,
            token=session.Session(auth=unscoped_auth).get_token(),
            project_id=settings.OS_PROJECT_ID,
        )
        self._openstack_auth_token = session.Session(auth=scoped_auth).get_token()

    def submit(self, *, project_path: Union[str, bytes, os.PathLike], data_url: str) -> str:
        match = re.search(r"AUTH_[^/]+/(?P<bucket>[^/]+)/(?P<prefix>.+)", data_url)
        if not match:
            raise ValueError(f"cannot submit job with invalid data_url {data_url!r}")

        input_path = match["prefix"].strip("/").split("/")
        input_group = []
        while input_path and "." not in input_path[-1]:
            input_group.append(input_path.pop())
        input_path = "/".join(input_path)
        input_group = "/".join(reversed(input_group))

        config = {
            "input_bucket": match["bucket"],
            "input_path": input_path,
            "input_group": input_group,
            "ilastik": {
                "project": str(Path(project_path).name),
                "export_source": "Probabilities",
                **settings.ILASTIK_OPTIONS,
            },
            "node_count": settings.HBP_NODE_COUNT,
            "output_bucket": settings.HBP_OUTPUT_BUCKET,
            "report_url_prefix": settings.HPC_JOB_RESULT_ENDPOINT,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(__file__).parent / "ilastik_wrapper.py"
            config_path = Path(temp_dir) / "config.json"

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2, sort_keys=True)

            job = self._client.new_job(
                {
                    "Executable": script_path.name,
                    "Environment": {
                        "OS_STORAGE_URL": settings.OS_STORAGE_URL,
                        "OS_AUTH_TOKEN": self._openstack_auth_token,
                    },
                    "Tags": settings.HBP_TAGS,
                },
                inputs=list(map(str, [script_path, config_path, project_path])),
            )

            return job.job_id

    def status(self, id: str) -> models.JobStatus:
        return self._STATUSES[self._job(id).properties["status"]]

    def delete(self, id: str) -> None:
        self._job(id).delete()

    def _job(self, id: str):
        return pyunicore.client.Job(self._client.transport, urljoin(self._client.site_urls["jobs"] + "/", id))


class _LeewayRefreshHandler(pyunicore.client.RefreshHandler):
    """Add leeway to pyunicore.client.RefreshHandler.

    See https://pyjwt.readthedocs.io/en/latest/usage.html#expiration-time-claim-exp.

    Note that a negative leeway is required in order
    to trigger a refresh of an otherwise valid token.
    """

    def __init__(self, *args, **kwargs):
        self.leeway = kwargs.pop("leeway")
        super().__init__(*args, **kwargs)

    def is_valid_token(self):
        try:
            jwt.decode(
                self.token,
                options={"verify_signature": False, "verify_nbf": False, "verify_exp": True, "verify_aud": False},
                leeway=self.leeway,
            )
            return True
        except jwt.exceptions.ExpiredSignatureError:
            return False
