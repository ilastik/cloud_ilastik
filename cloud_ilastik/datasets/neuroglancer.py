import json
import urllib.parse
from typing import List

from django.conf import settings

__all__ = ["viewer_url"]


class _Color:
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
        return [cls(*rgb) for rgb in cls.VISUALY_DISTINCT_COLORS_RGB[:num_colors]]

    def __repr__(self):
        return f"<Color ({self.r},{self.g},{self.b})>"


def _create_fragment_shader(channel_colors: List[_Color]):
    color_lines: List[str] = []
    colors_to_mix: List[str] = []

    for idx, color in enumerate(channel_colors):
        color_line = f"vec3 color{idx} = ({color.as_normalized_vec3()} / 255.0) * toNormalized(getDataValue({idx}));"
        color_lines.append(color_line)
        colors_to_mix.append(f"color{idx}")

    shader_lines = [
        "void main() {",
        "    " + "\n    ".join(color_lines),
        "    emitRGBA(",
        f"        vec4({' + '.join(colors_to_mix)}, 1.0)",
        "    );",
        "}",
    ]
    return "\n".join(shader_lines)


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
                "shader": _create_fragment_shader(_Color.get_distinct_colors(num_channels)),
            }
        ],
        "selectedLayer": {"layer": "exported_data", "visible": True},
        "layout": "xy",  # TODO: Fix layout detection based on dataset properties
    }
    quoted_config = urllib.parse.quote(json.dumps(ng_config))
    return ng_url + quoted_config
