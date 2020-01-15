import pyunicore.client as unicore_client
from typing import Union
import json, time, os
from typing import Dict, List, Optional
from pathlib import Path
import json
import jwt
import requests

class JobResources:
    def __init__(
        self,
        *,
        Memory: Optional[str] = None,
        Runtime: int = 60 * 5, #seconds
        CPUs: Optional[int] = None,
        Nodes: Optional[int] = None,
        CPUsPerNode: Optional[int] = None,
        Reservation: Optional[str] = None
    ):
        self.data = {
            'Runtime': Runtime
        }
        if Memory:
            self.data['Memory'] = Memory
        if CPUs:
            self.data['CPUs'] = CPUs
        if Nodes:
            self.data['Nodes'] = Nodes
        if CPUsPerNode:
            self.data['CPUsPerNode'] = CPUsPerNode
        if Reservation:
            self.data['Reservation'] = Reservation

    def to_dict(self):
        return self.data.copy()

class JobImport:
    def __init__(self, From:str, To:str):
        self.From = From
        self.To = To

    def to_dict(self) -> Dict:
        return self.__dict__.copy()

class JobSpec:
    def __init__(
        self,
        *,
        Executable: str,
        Arguments: Optional[List[str]] = None,
        Environment: Dict[str, str] = None,
        Exports: Optional[List[str]] = None,
        Resources: Optional[JobResources]  = None,
        Imports: Optional[JobImport] = None
    ):
        self.data = {
            'Executable': Executable,
            'Resources': (Resources or JobResources()).to_dict(),
        }
        if Arguments:
            self.data['Arguments'] = Arguments
        if Environment:
            self.data['Environment'] = Environment
        if Exports:
            self.data['Exports'] = Exports
        if Resources:
            self.data['Resources'] = Resources.to_dict()
        if Imports:
            self.data['Imports'] = [imp.to_dict() for imp in Imports]

    def to_dict(self):
        return self.data.copy()


class HpcEnvironment:
    def __init__(
        self,
        *,
        HBP_REFRESH_TOKEN: Optional[str] = None,
        HBP_APP_ID : Optional[str] = None,
        HBP_APP_SECRET : Optional[str] = None,

        HPC_PYTHON_EXECUTABLE : Optional[str] = None,
        HPC_ILASTIK_PATH : Optional[str] = None,

        S3_KEY : Optional[str] = None,
        S3_SECRET : Optional[str] = None
    ):
        self.access_token = None
        self.HBP_REFRESH_TOKEN = HBP_REFRESH_TOKEN or os.environ['HBP_REFRESH_TOKEN']
        self.HBP_APP_ID = HBP_APP_ID or os.environ['HBP_APP_ID']
        self.HBP_APP_SECRET = HBP_APP_SECRET or os.environ['HBP_APP_SECRET']

        self.HPC_PYTHON_EXECUTABLE = HPC_PYTHON_EXECUTABLE or os.environ['HPC_PYTHON_EXECUTABLE']
        self.HPC_ILASTIK_PATH = HPC_ILASTIK_PATH or os.environ['HPC_ILASTIK_PATH']

        self.S3_KEY = S3_KEY or os.environ['S3_KEY']
        self.S3_SECRET = S3_SECRET or os.environ['S3_SECRET']

    def token_is_valid(self):
        if self.access_token is None:
            return False
        token = json.loads(jwt.utils.base64url_decode(self.access_token.split('.')[1]).decode('ascii'))
        if token['exp'] < time.time() - (15 * 60):
            return False
        return True

    def get_token(self):
        if not self.token_is_valid():
            resp = requests.post("https://services.humanbrainproject.eu/oidc/token", data={
                "refresh_token": self.HBP_REFRESH_TOKEN,
                "client_id": self.HBP_APP_ID,
                "client_secret": self.HBP_APP_SECRET,
                "grant_type": "refresh_token"
            })
            print("Refreshed token!")
            #FIXME: do we need to verify the token's signature?
            self.access_token = resp.json()['access_token']
        return self.access_token


class IlastikJobSpec(JobSpec):
    def __init__(
        self,
        *,
        hpc_environment: Optional[HpcEnvironment] = None,
        ilp_project: Path,
        raw_data_url: str,
        result_endpoint: str,
        Resources: JobResources,
        block_size: int = 1024,
        export_dtype: str = 'uint8'
    ):
        self.hpc_environment = hpc_environment or HpcEnvironment()
        self.inputs = [
            ilp_project.as_posix(),
            Path(__file__).parent.joinpath('remote_scripts/run_ilastik.sh').as_posix(),
            Path(__file__).parent.joinpath('remote_scripts/upload_dir.py').as_posix()
        ]
        super().__init__(
            Executable='./run_ilastik.sh',
            Environment={ #These variables are expected bu the run_ilastik.sh script
                'ILASTIK_PROJECT_FILE': ilp_project.name,
                'HPC_PYTHON_EXECUTABLE': self.hpc_environment.HPC_PYTHON_EXECUTABLE,
                'HPC_ILASTIK_PATH': self.hpc_environment.HPC_ILASTIK_PATH,
                'ILASTIK_BLOCK_SIZE': block_size,
                'S3_KEY': self.hpc_environment.S3_KEY,
                'S3_SECRET': self.hpc_environment.S3_SECRET,
                'ILASTIK_JOB_RESULT_ENDPOINT': result_endpoint,
                'ILASTIK_EXPORT_DTYPE': export_dtype
            },
            Imports=[JobImport(From=raw_data_url, To='raw_data.n5.tar')], #FIXME: allow for non-n5
            Resources=Resources
        )

    def __repr__(self) -> str:
        data = self.to_dict()
        data["inputs"] = self.inputs
        return json.dumps(data, indent=4)

    def run(self):
        tr = unicore_client.Transport(self.hpc_environment.get_token())
        registry = unicore_client.Registry(tr, unicore_client._HBP_REGISTRY_URL)
        site = registry.site('DAINT-CSCS')
        return site.new_job(
            job_description=self.to_dict(),
            inputs=self.inputs
        )
