import pyunicore.client as unicore_client
import json
import time
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import jwt
import requests
from numbers import Number
from urllib.parse import urljoin
import enum
from collections.abc import Mapping, Iterable

from hpc.openstack_environment import OpenstackEnvironment

def dict_to_json_data(dictionary, strip_nones=True):
    out_dict = {}
    for k, v in dictionary.items():
        json_value = to_json_data(v, strip_nones=strip_nones)
        if strip_nones and json_value is None:
            continue
        out_dict[k] = json_value
    return out_dict

def to_json_data(value, strip_nones=True):
    if isinstance(value, (str, int, float, type(None))):
        return value
    if hasattr(value, 'to_json_data'):
        return value.to_json_data()
    if hasattr(value, '__dict__'):
        return dict_to_json_data(value.__dict__, strip_nones=strip_nones)
    if isinstance(value, Mapping):
        return dict_to_json_data(value, strip_nones=strip_nones)
    if isinstance(value, Iterable):
        return [to_json_data(v) for v in value]
    raise ValueError("Don't know how to convert {value} to json data")

_FIVE_MINUTES = 5 * 50
class JobResources:
    def __init__(
        self,
        *,
        Memory: Optional[str] = None,
        Runtime: int = _FIVE_MINUTES,
        CPUs: Optional[int] = None,
        Nodes: Optional[int] = None,
        CPUsPerNode: Optional[int] = None,
        Reservation: Optional[str] = None
    ):
        self.Memory = Memory
        self.Runtime = Runtime
        self.CPUs = CPUs
        self.Nodes = Nodes
        self.CPUsPerNode = CPUsPerNode
        self.Reservation = Reservation

class JobImport:
    def __init_(self, *, From: str, To: str):
        self.From = From
        self.To = To

class JobSpec:
    def __init__(
        self,
        *,
        Executable: str,
        Arguments: Optional[List[str]] = None,
        Environment: Dict[str, str] = None,
        Exports: Optional[List[str]] = None,
        Resources: Optional[JobResources] = None,
        Imports: Optional[JobImport] = None,
        Tags: Optional[List[str]] = None,
        Project: Optional[str] = None
    ):
        self.Executable = Executable
        self.Arguments = Arguments
        self.Environment = Environment
        self.Exports = Exports
        self.Resources = Resources
        self.Imports = Imports
        self.Tags = Tags
        self.Project = Project

    def raw(self):
        raw = {
            "Executable": self.Executable,
            "Arguments": self.Arguments,
            "Environment": self.Environment,
            "Exports": self.Exports,
            "Resources": self.Resources,
            "Imports": self.Imports,
            "Tags": self.Tags,
            "Project": self.Project
        }
        return to_json_data(raw)


class HpcEnvironment:
    _site = None

    def __init__(
        self,
        *,
        HBP_REFRESH_TOKEN: Optional[str] = None,
        HBP_APP_ID: Optional[str] = None,
        HBP_APP_SECRET: Optional[str] = None,
        HPC_PATH_PREFIX: Optional[str] = None,
        HPC_PROJECT_NAME: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.access_token = access_token
        self.HBP_REFRESH_TOKEN = HBP_REFRESH_TOKEN or os.environ["HBP_REFRESH_TOKEN"]
        self.HBP_APP_ID = HBP_APP_ID or os.environ["HBP_APP_ID"]
        self.HBP_APP_SECRET = HBP_APP_SECRET or os.environ["HBP_APP_SECRET"]
        self.HPC_PATH_PREFIX = HPC_PATH_PREFIX or os.environ.get("HPC_PATH_PREFIX", "")
        self.HPC_PROJECT_NAME = HPC_PROJECT_NAME or os.environ.get("HPC_PROJECT_NAME", None)

    def token_is_valid(self):
        if self.access_token is None:
            return False
        token = json.loads(jwt.utils.base64url_decode(self.access_token.split(".")[1]).decode("ascii"))
        if token["exp"] < time.time() - (15 * 60):
            return False
        return True

    def get_token(self):
        if not self.token_is_valid():
            resp = requests.post(
                "https://services.humanbrainproject.eu/oidc/token",
                data={
                    "refresh_token": self.HBP_REFRESH_TOKEN,
                    "client_id": self.HBP_APP_ID,
                    "client_secret": self.HBP_APP_SECRET,
                    "grant_type": "refresh_token",
                },
            )
            self.access_token = resp.json()["access_token"]
        return self.access_token

    def get_jobs(self):
        site = self._get_site()
        return site.transport.get(url=site.site_urls["jobs"])

    def get_job(self, job_id: str):
        site = self._get_site()
        jobs_url = site.site_urls["jobs"]
        return unicore_client.Job(site.transport, job_url=urljoin(f"{jobs_url}/", job_id))

    def _get_site(self):
        if self._site is None:
            tr = unicore_client.Transport(self.get_token())
            registry = unicore_client.Registry(tr, unicore_client._HBP_REGISTRY_URL)
            self._site = registry.site("DAINT-CSCS")
        return self._site


class IlastikJobSpec(JobSpec):
    def __init__(
        self,
        *,
        openstack_environment: OpenstackEnvironment,
        hpc_environment: Optional[HpcEnvironment] = None,
        Resources: JobResources,
        ILASTIK_RAW_DATA: str,
        ILASTIK_PROJECT_FILE: Path,
        ILASTIK_JOB_RESULT_ENDPOINT: str,
        ILASTIK_EXPORT_SOURCE: str,
        ILASTIK_BLOCK_SIZE: int = 1024,
    ):
        self.hpc_environment = hpc_environment or HpcEnvironment()
        self.inputs = [ILASTIK_PROJECT_FILE.as_posix()]
        self.inputs += [p.as_posix() for p in Path(__file__).parent.glob("remote_scripts/*")]
        super().__init__(
            Executable="./run_ilastik.sh",
            Environment={  # These variables are expected bu the run_ilastik.sh script
                "ILASTIK_RAW_DATA": ILASTIK_RAW_DATA,
                "ILASTIK_PROJECT_FILE": ILASTIK_PROJECT_FILE.name,
                "ILASTIK_JOB_RESULT_ENDPOINT": ILASTIK_JOB_RESULT_ENDPOINT,
                "ILASTIK_EXPORT_SOURCE": ILASTIK_EXPORT_SOURCE,
                "ILASTIK_BLOCK_SIZE": ILASTIK_BLOCK_SIZE,
                "HPC_PATH_PREFIX": self.hpc_environment.HPC_PATH_PREFIX,
                **to_json_data(openstack_environment)
            },
            Resources=Resources,
            Tags=["ILASTIK"],
            Project=hpc_environment.HPC_PROJECT_NAME
        )

    def __repr__(self) -> str:
        data = self.raw()
        data["inputs"] = self.inputs
        return json.dumps(data, indent=4)

    def run(self):
        site = self.hpc_environment._get_site()
        return site.new_job(job_description=self.raw(), inputs=self.inputs)

class PixelClassificationJobSpec(IlastikJobSpec):
    class ExportSource(enum.Enum):
        PROBABILITIES = "Probabilities"

    def __init__(
        self,
        *,
        ILASTIK_EXPORT_SOURCE: ExportSource = ExportSource.PROBABILITIES,
        **job_spec_kwargs
    ):
        super().__init__(ILASTIK_EXPORT_SOURCE=ILASTIK_EXPORT_SOURCE.value, **job_spec_kwargs)


class ObjectClassificationJobSpec(IlastikJobSpec):
    _PREDICTION_MAPS_FILE_NAME = ""
    class ExportSource(enum.Enum):
        OBJECT_PREDICTIONS = "Object Predictions"

    def __init__(
        self,
        *,
        ILASTIK_PREDICTION_MAPS: str,
        ILASTIK_EXPORT_SOURCE: ExportSource = ExportSource.OBJECT_PREDICTIONS,
        **job_spec_kwargs
    ):
        super().__init__(ILASTIK_EXPORT_SOURCE=ILASTIK_EXPORT_SOURCE.value, **job_spec_kwargs)
        self.Executable = "./run_obj_classification.sh"
        self.Environment["ILASTIK_PREDICTION_MAPS"] = ILASTIK_PREDICTION_MAPS
