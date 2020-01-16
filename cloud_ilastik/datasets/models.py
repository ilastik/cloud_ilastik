import enum
import json
import re
import urllib.parse
from typing import List

from django.conf import settings
from django.db import models

import batch.models as batch_models
import files.models as files_models

TAR_URL_RE = re.compile("/data$")


class Color:
    # Taken from volumina.colortables
    VISUALY_DISTINCT_COLORS_RGB = [
        (255, 225, 25),  # yellow
        (0, 130, 200),  # blue
        (230, 25, 75),  # red
        (70, 240, 240),  # cyan
        (60, 180, 75),  # green
        (250, 190, 190),  # pink
        (170, 110, 40),  # brown
        (145, 30, 180),  # purple
        (0, 128, 128),  # teal
        (245, 130, 48),  # orange
        (240, 50, 230),  # magenta
        (210, 245, 60),  # lime
        (255, 215, 180),  # coral
        (230, 190, 255),  # lavender
        (128, 128, 128),  # gray
    ]

    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def as_normalized_vec3(self) -> str:
        return f"vec3({self.r}, {self.g}, {self.b})"

    @classmethod
    def get_distinct_colors(cls, num_colors: int) -> List["Color"]:
        return [Color(*rgb) for rgb in cls.VISUALY_DISTINCT_COLORS_RGB[:num_colors]]

    def __repr__(self):
        return f"<Color ({self.r},{self.g},{self.b})>"


def createFragShader(channel_colors: List[Color]):
    colorLines: List[str] = []
    colorsToMix: List[str] = []

    for colorIdx, color in enumerate(channel_colors):
        colorLine = (
            f"vec3 color{colorIdx} = ({color.as_normalized_vec3()} / 255.0) * toNormalized(getDataValue({colorIdx}));"
        )
        colorLines.append(colorLine)
        colorsToMix.append(f"color{colorIdx}")

    fragShaderLines = [
        "void main() {",
        "    " + "\n    ".join(colorLines),
        "    emitRGBA(",
        f"        vec4({' + '.join(colorsToMix)}, 1.0)",
        "    );",
        "}",
    ]
    return "\n".join(fragShaderLines)


def viewer_url(url: str, num_channels: int) -> str:
    ng_url = "https://web.ilastik.org/viewer/#!"
    data_url = url.replace(settings.SWIFT_PREFIX, "https://web.ilastik.org/data/")
    ng_config = {
        "dimensions": {"c": [1e-9, "m"], "x": [1e-9, "m"], "y": [1e-9, "m"]},
        "crossSectionScale": 1,
        "projectionScale": 8192,
        "layers": [
            {
                "type": "image",
                "source": {"url": f"n5://{data_url}"},
                "tab": "source",
                "blend": "default",
                "name": "exported_data",
                "shader": createFragShader(Color.get_distinct_colors(num_channels)),
            }
        ],
        "selectedLayer": {"layer": "exported_data", "visible": True},
        "layout": "xy",  # TODO: Fix layout detection based on dataset properties
    }
    quoted_config = urllib.parse.quote(json.dumps(ng_config))
    return ng_url + quoted_config


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
    owner = models.ForeignKey(files_models.User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=False)

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

    @property
    def neuroglancer_url(self):
        return viewer_url(self.url, self.size_c)

    def __str__(self):
        return f"{self.name} {self.sizes} <{self.url}>"
