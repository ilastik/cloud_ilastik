import contextlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Union, Mapping
from urllib.parse import urljoin

import jwt
import pyunicore.client
from django.conf import settings
from keystoneauth1 import session
from keystoneauth1.extras._saml2 import V3Saml2Password
from keystoneauth1.identity import v3

from batch import models, job_runner


class UnicoreJobRunner(job_runner.JobRunner):
    _STATUSES = {
        "SUCCESSFUL": models.JobStatus.done,
        "QUEUED": models.JobStatus.running,
        "STAGINGIN": models.JobStatus.running,
        "STAGINGOUT": models.JobStatus.running,
        "READY": models.JobStatus.running,
        "RUNNING": models.JobStatus.running,
        "FAILED": models.JobStatus.failed,
    }

    def __init__(self, *, auth_token=None, openstack_auth_token=None):
        self.client = get_client(auth_token=auth_token)

        if openstack_auth_token is None:
            openstack_auth_token = get_openstack_auth_token()
        self.openstack_auth_token = openstack_auth_token

    def submit(self, *, project_path: Union[str, bytes, os.PathLike], data_urls: Mapping[str, str]) -> str:
        config = {
            "inputs": {k: _parse_data_url(url) for k, url in data_urls.items()},
            "ilastik": {
                "project": Path(project_path).name,
                "export_source": "Probabilities",
                **settings.ILASTIK_OPTIONS,
            },
            "node_count": settings.HBP_NODE_COUNT,
            "output_bucket": settings.HBP_OUTPUT_BUCKET,
            "report_url_prefix": settings.HPC_JOB_RESULT_ENDPOINT,
        }

        script_path = Path(__file__).parent / "ilastik_wrapper.py"
        job_description = {
            "Executable": script_path.name,
            "Environment": {"OS_STORAGE_URL": settings.OS_STORAGE_URL, "OS_AUTH_TOKEN": self.openstack_auth_token},
            "Tags": settings.HBP_TAGS,
        }

        with _temp_json(config, "config.json", indent=4) as config_path:
            inputs = list(map(str, [script_path, config_path, project_path]))
            job = self.client.new_job(job_description, inputs=inputs)
            return job.job_id

    def status(self, id: str) -> models.JobStatus:
        return self._STATUSES[self._job(id).properties["status"]]

    def delete(self, id: str) -> None:
        self._job(id).delete()

    def _job(self, id):
        return pyunicore.client.Job(self.client.transport, urljoin(self.client.site_urls["jobs"] + "/", id))


def get_client(*, auth_token=None):
    refresh_config = {
        "client_id": settings.HBP_APP_ID,
        "client_secret": settings.HBP_APP_SECRET,
        "refresh_token": settings.HBP_REFRESH_TOKEN,
        "url": settings.HBP_REFRESH_URL,
    }
    refresh_handler = _LeewayRefreshHandler(refresh_config, token=auth_token, leeway=settings.HBP_REFRESH_LEEWAY)
    transport = pyunicore.client.Transport(auth_token, refresh_handler=refresh_handler)
    sites = pyunicore.client.get_sites(transport)
    return pyunicore.client.Client(transport, sites[settings.HBP_SITE])


def get_openstack_auth_token():
    # https://user.cscs.ch/storage/object_storage/usage_examples/tokens/
    unscoped_auth = V3Saml2Password(
        username=settings.OS_USERNAME, password=settings.OS_PASSWORD, **settings.OS_AUTH_PARAMS
    )
    unscoped_token = session.Session(auth=unscoped_auth).get_token()
    scoped_auth = v3.Token(auth_url=unscoped_auth.auth_url, token=unscoped_token, project_id=settings.OS_PROJECT_ID)
    scoped_token = session.Session(auth=scoped_auth).get_token()
    return scoped_token


class _LeewayRefreshHandler(pyunicore.client.RefreshHandler):
    """Add leeway to pyunicore.client.RefreshHandler.

    See https://pyjwt.readthedocs.io/en/latest/usage.html#expiration-time-claim-exp.

    Note that a negative leeway is required in order
    to trigger a refresh of an otherwise valid token.
    """

    OPTIONS = {"verify_signature": False, "verify_nbf": False, "verify_exp": True, "verify_aud": False}

    def __init__(self, *args, **kwargs):
        self.leeway = kwargs.pop("leeway")
        super().__init__(*args, **kwargs)

    def is_valid_token(self):
        try:
            jwt.decode(self.token, options=self.OPTIONS, leeway=self.leeway)
            return True
        except jwt.exceptions.ExpiredSignatureError:
            return False


def _parse_data_url(data_url):
    match = re.search(r"AUTH_[^/]+/(?P<bucket>[^/]+)/(?P<prefix>.+)", data_url)
    if not match:
        raise ValueError(f"cannot submit job with invalid data_url {data_url!r}")

    path = match["prefix"].strip("/").split("/")
    rev_group = []

    while path and "." not in path[-1]:
        rev_group.append(path.pop())

    d = {"bucket": match["bucket"], "path": "/".join(path)}
    if rev_group:
        d["group"] = "/".join(reversed(rev_group))

    return d


@contextlib.contextmanager
def _temp_json(obj, name, **json_kwargs):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / name

        with open(path, "w") as f:
            json.dump(obj, f, **json_kwargs)

        yield path
