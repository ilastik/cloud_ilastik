import uuid
import enum

from django.contrib.auth import get_user_model
from django.db import models

from files import models as file_models


User = get_user_model()

__all__ = ["Project", "Job"]


class Project(models.Model):
    """
    User project
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(file_models.File, on_delete=models.SET_NULL, null=True)
    num_dimensions = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Project"


class JobStatus(enum.Enum):
    created = "created"
    running = "running"
    done = "done"
    failed = "failed"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class Job(models.Model):
    """
    Represents remote job
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=JobStatus.choices(), default=JobStatus.created.value)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, editable=False)
    created_on = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = "Job"
