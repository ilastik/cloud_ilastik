import enum
import re

from django.db import models

import batch.models as batch_models
import files.models as files_models

from . import neuroglancer as ng

TAR_URL_RE = re.compile("/data$")


@enum.unique
class DType(enum.Enum):
    uint8 = "uint8"
    uint16 = "uint16"
    uint32 = "uint32"
    uint64 = "uint64"
    int8 = "int8"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    float16 = "float16"
    float32 = "float32"
    float64 = "float64"

    @classmethod
    def choices(cls):
        return tuple((item.name, item.value) for item in cls)

    @classmethod
    def values(cls):
        return tuple(item.value for item in cls)


@enum.unique
class ChannelType(enum.Enum):
    Intensity = "intensity"
    IndexedColor = "indexed"

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
    channel_type = models.CharField(max_length=15, choices=ChannelType.choices(), default=ChannelType.Intensity.value)
    size_t = models.PositiveIntegerField(default=1)
    size_z = models.PositiveIntegerField(default=1)
    size_y = models.PositiveIntegerField()
    size_x = models.PositiveIntegerField()
    size_c = models.PositiveIntegerField(default=1)
    job = models.ForeignKey(
        batch_models.Job, on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name="results"
    )
    owner = models.ForeignKey(files_models.User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.owner and self.job:
            self.owner = self.job.owner
        super().save(*args, **kwargs)


    @property
    def sizes(self):
        return {"t": self.size_t, "z": self.size_z, "y": self.size_y, "x": self.size_x, "c": self.size_c}

    @property
    def tar_url(self):
        return TAR_URL_RE.sub(".tar", self.url)

    def as_viewer_layer(self):
        if self.size_c == 1:
            mode = ng.ColorMode.GRAYSCALE
        elif self.size_c < 4:
            mode = ng.ColorMode.RGB
        else:
            mode = ng.ColorMode.ILASTIK
        return ng.Layer(self.url, self.size_c, color_mode=mode, role="data")

    @property
    def neuroglancer_url(self):
        return ng.viewer_url([self.as_viewer_layer()])

    def __str__(self):
        return f"{self.name} {self.sizes} <{self.url}>"
