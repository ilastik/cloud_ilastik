import json
import enum
import urllib.parse

from typing import List

from django.conf import settings

from . import types

__all__ = ["viewer_url"]


class Layer:
    url: str
    num_channels: int
    role: str
    selected: bool
    color_table: types.ColorTable
    channel_type: types.ChannelType

    def __init__(
        self,
        url: str,
        num_channels: int,
        role: str = "data",
        selected: bool = False,
        color_table: types.ColorTable = types.ColorTable.RGB,
        channel_type: types.ChannelType = types.ChannelType.Intensity,
    ):
        self.url = url
        self.num_channels = num_channels
        self.role = role
        self.selected = selected
        self.color_table = color_table
        self.channel_type = channel_type


class _Color:
    # Taken from volumina.colortables
    COLORS_ILASTIK = [
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

    COLORS_RGB = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # red  # green  # blue

    COLORS_GRAYSCALE = [(255, 255, 255)]  # red

    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def as_normalized_vec3(self) -> str:
        return f"vec3({self.r}, {self.g}, {self.b})"

    @classmethod
    def get_colors(cls, num_colors: int, table: types.ColorTable) -> List["Color"]:
        color_table = {
            types.ColorTable.GRAYSCALE: cls.COLORS_GRAYSCALE,
            types.ColorTable.RGB: cls.COLORS_RGB,
            types.ColorTable.ILASTIK: cls.COLORS_ILASTIK,
        }[table]

        return [cls(*rgb) for rgb in color_table[:num_colors]]

    def __repr__(self):
        return f"<Color ({self.r},{self.g},{self.b})>"


def _create_intensity_fragment_shader(colors):
    color_lines: List[str] = []
    colors_to_mix: List[str] = []

    for idx, color in enumerate(colors):
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


def _create_indexed_color_fragment_shader(colors):
    color_lines: List[str] = ["vec4(0.0, 0.0, 0.0, 0.0)"]

    for color in colors:
        color_lines.append(f"vec4({color.r / 255.0}, {color.g / 255.0}, {color.b / 255.0}, 1.0)")

    return f"""vec4 COLOR_MASKS[{len(color_lines)}] = vec4[](
    {",".join(color_lines)}
);
void main() {{
  uint val = toRaw(getDataValue());
  emitRGB(COLOR_MASKS[val]);
}}"""


def _create_fragment_shader(colors: List[_Color], channel_type: types.ChannelType):
    if channel_type == types.ChannelType.Intensity:
        return _create_intensity_fragment_shader(colors)
    elif channel_type == types.ChannelType.IndexedColor:
        return _create_indexed_color_fragment_shader(colors)
    else:
        raise Exception(f"Unknown channel type {channel_type}")


def viewer_url(layers: List[Layer], show_control_panel=False) -> str:
    ng_url = "https://web.ilastik.org/viewer/#!"
    ng_layers = []
    selected_layer = None

    for layer in layers:
        data_url = layer.url.replace(settings.SWIFT_PREFIX, "https://web.ilastik.org/data/")
        colors = _Color.get_colors(layer.color_table)
        ng_layers.append(
            {
                "type": "image",
                "source": {"url": f"n5://{data_url}"},
                "tab": "source",
                "blend": "default",
                "name": layer.role,
                "shader": _create_fragment_shader(colors, layer.channel_type),
            }
        )

        if layer.selected:
            selected_layer = layer.role

    if selected_layer is None and layers:
        selected_layer = layers[-1].role

    ng_config = {
        "dimensions": {"c": [1e-9, "m"], "x": [1e-9, "m"], "y": [1e-9, "m"]},
        "crossSectionScale": 1,
        "projectionScale": 8192,
        "layers": ng_layers,
        "selectedLayer": {"layer": selected_layer, "visible": show_control_panel},
        "layout": "xy",  # TODO: Fix layout detection based on dataset properties
    }
    quoted_config = urllib.parse.quote(json.dumps(ng_config))
    return ng_url + quoted_config
