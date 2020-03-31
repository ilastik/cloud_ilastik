import abc
import os
from typing import Union, Mapping

from batch import models


class JobRunner(abc.ABC):
    @abc.abstractmethod
    def submit(self, *, project_path: Union[str, bytes, os.PathLike], data_urls: Mapping[str, str]) -> str:
        pass

    @abc.abstractmethod
    def status(self, id: str) -> models.JobStatus:
        pass

    @abc.abstractmethod
    def delete(self, id: str) -> None:
        pass
