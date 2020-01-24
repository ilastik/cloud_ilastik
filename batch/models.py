import datetime
import enum
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from files import models as file_models


User = get_user_model()

__all__ = ["Project", "Job"]


def not_negative(value):
    if value < 0:
        raise ValidationError(_("%(value)s should be positive or 0"), params={"value": value})


class ProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("file")


class Project(models.Model):
    """
    User project
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(file_models.File, on_delete=models.SET_NULL, null=True)
    num_channels = models.PositiveIntegerField()
    min_block_size_z = models.IntegerField(default=0, validators=[not_negative])
    min_block_size_y = models.IntegerField(validators=[not_negative])
    min_block_size_x = models.IntegerField(validators=[not_negative])

    objects = ProjectManager()

    @property
    def name(self):
        return self.file.name if self.file else self.id

    @property
    def min_block_sizes(self):
        return {"z": self.min_block_size_z, "y": self.min_block_size_y, "x": self.min_block_size_x}

    def __str__(self):
        name = self.file.name if self.file else f"<<<{self.id}>>>"
        channels = "1 channel" if self.num_channels == 1 else f"{self.num_channels} channels"
        return f"{name} [{channels}]"

    class Meta:
        verbose_name = "Project"


class JobStatus(enum.Enum):
    """
    State transition diagramm:

                          +--->done+--->collected
                          |
    created+--->running+--+
                          |
                          +--->failed

    created -> running: happens when we submit task to job runner
    running -> done: should happen when task reports it's results back
    running -> failed: task reports failure via rest
    done -> collected: only successful tasks should be cleaned up
    """

    created = "created"
    running = "running"
    done = "done"
    failed = "failed"
    collected = "collected"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class JobManager(models.Manager):
    _STATUS_TRANSITIONS = {
        (JobStatus.created, JobStatus.running): {"now": "started_on"},
        (JobStatus.running, JobStatus.done): {"now": "finished_on"},
        (JobStatus.running, JobStatus.failed): {"now": "finished_on"},
        (JobStatus.done, JobStatus.collected): {},
    }

    def update_status(self, *, old: JobStatus, new: JobStatus) -> int:
        """Update the job status of records with the old status to the new status.

        Returns:
            Number of changed rows.

        Raises:
            ValueError: Status transition is invalid.
        """
        transition_info = self._STATUS_TRANSITIONS.get((old, new))
        if transition_info is None:
            raise ValueError(f"invalid job status transition from {old.value} to {new.value}")

        extra_update_fields = {}
        if "now" in transition_info:
            extra_update_fields[transition_info["now"]] = datetime.datetime.utcnow()

        return self.filter(status=old).update(status=new, **extra_update_fields)


class Job(models.Model):
    """
    Represents remote job
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=255, unique=True, null=True, blank=True, editable=False)
    status = models.CharField(max_length=20, choices=JobStatus.choices(), default=JobStatus.created.value)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    created_on = models.DateTimeField(auto_now_add=True, editable=False)
    updated_on = models.DateTimeField(auto_now=True, editable=False)
    started_on = models.DateTimeField(editable=False, null=True, blank=True)
    finished_on = models.DateTimeField(editable=False, null=True, blank=True)

    # TODO: Should be many to many relation with roles
    raw_data = models.ForeignKey(
        "datasets.Dataset", editable=False, null=True, blank=False, on_delete=models.PROTECT, related_name="+"
    )
    project = models.ForeignKey(Project, editable=False, null=True, blank=False, on_delete=models.PROTECT)

    objects = JobManager()

    class Meta:
        verbose_name = "Job"
