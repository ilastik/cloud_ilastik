import pyunicore.client as unicore_client
from typing import Union
import json, time, os
from typing import Dict, List, Optional
from pathlib import Path

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

class IlastikJobSpec(JobSpec):
    HPC_PYTHON_EXECUTABLE=os.environ['HPC_PYTHON_EXECUTABLE']
    HPC_ILASTIK_PATH=os.environ['HPC_ILASTIK_PATH']
    HBP_TOKEN=os.environ['HBP_TOKEN']
    S3_KEY=os.environ['S3_KEY']
    S3_SECRET=os.environ['S3_SECRET']

    def __init__(
        self,
        ilp_project: Path,
        raw_data_url: str,
        result_endpoint: str,
        Resources: JobResources,
        block_size: int = 1024
    ):
        self.inputs = [
            ilp_project.as_posix(),
            Path(__file__).parent / 'remote_scripts/run_ilastik.sh',
            Path(__file__).parent / 'remote_scripts/upload_dir.py'
        ]
        super().__init__(
            Executable='./run_ilastik.sh',
            Environment={ #These variables are expected bu the run_ilastik.sh script
                'ILASTIK_PROJECT_FILE': ilp_project.name,
                'HPC_PYTHON_EXECUTABLE': self.HPC_PYTHON_EXECUTABLE,
                'HPC_ILASTIK_PATH': self.HPC_ILASTIK_PATH,
                'ILASTIK_BLOCK_SIZE': block_size,
                'S3_KEY': self.S3_KEY,
                'S3_SECRET': self.S3_SECRET,
                'ILASTIK_JOB_RESULT_ENDPOINT': result_endpoint
            },
            Imports=[JobImport(From=raw_data_url, To='raw_data.n5.tar')], #FIXME: allow for non-n5
            Resources=Resources
        )

    def run(self, token: str = ''):
        tr = unicore_client.Transport(self.HBP_TOKEN)
        registry = unicore_client.Registry(tr, unicore_client._HBP_REGISTRY_URL)
        site = registry.site('DAINT-CSCS')
        return site.new_job(
            job_description=self.to_dict(),
            inputs=self.inputs
        )
