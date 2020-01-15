import enum
import re

from django.db import models

import batch.models as batch_models


TAR_URL_RE = re.compile("/data$")


class DType(str, enum.Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    uint8 = enum.auto()
    uint16 = enum.auto()
    uint32 = enum.auto()
    uint64 = enum.auto()
    int8 = enum.auto()
    int16 = enum.auto()
    int32 = enum.auto()
    int64 = enum.auto()
    float16 = enum.auto()
    float32 = enum.auto()
    float64 = enum.auto()

    @classmethod
    def choices(cls):
        return tuple((item.name, item.value) for item in cls)

    @classmethod
    def values(cls):
        return tuple(item.value for item in cls)


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    dtype = models.CharField(max_length=15, choices=DType.choices())
    size_t = models.PositiveIntegerField(default=1)
    size_z = models.PositiveIntegerField(default=1)
    size_y = models.PositiveIntegerField()
    size_x = models.PositiveIntegerField()
    size_c = models.PositiveIntegerField(default=1)
    job = models.ForeignKey(batch_models.Job, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    @property
    def owner(self):
        return self.job.owner if self.job else None

    @property
    def sizes(self):
        return {"t": self.size_t, "z": self.size_z, "y": self.size_y, "x": self.size_x, "c": self.size_c}

    @property
    def tar_url(self):
        return TAR_URL_RE.sub(".tar", self.url)

    def __str__(self):
        return f"{self.name} {self.sizes} <{self.url}>"
