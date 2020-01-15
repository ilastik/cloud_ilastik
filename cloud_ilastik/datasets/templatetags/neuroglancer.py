import urllib.parse
import json
from typing import List

from django import template
from django.conf import settings

register = template.Library()


class Color:
    VISUALY_DISTINCT_COLORS_RGB = [
        (125, 135, 185),
        (190, 193, 212),
        (214, 188, 192),
        (187, 119, 132),
        (2, 63, 165),
        (142, 6, 59),
        (74, 111, 227),
        (133, 149, 225),
        (181, 187, 227),
        (230, 175, 185),
        (224, 123, 145),
        (211, 63, 106),
        (17, 198, 56),
        (141, 213, 147),
        (198, 222, 199),
        (234, 211, 198),
        (240, 185, 141),
        (239, 151, 8),
        (15, 207, 192),
        (156, 222, 214),
        (213, 234, 231),
        (243, 225, 235),
        (246, 196, 225),
        (247, 156, 212),
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


@register.filter(is_safe=True)
def viewer_url(url: str, num_channels: int) -> str:
    ng_url = "http://web.ilastik.org/viewer/#!"
    data_url = url.replace(settings.SWIFT_PREFIX, "http://web.ilastik.org/ngdata/")
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
        "layout": "yz",  # TODO: Fix layout detection based on dataset properties
    }
    quoted_config = urllib.parse.quote(json.dumps(ng_config))
    return ng_url + quoted_config
