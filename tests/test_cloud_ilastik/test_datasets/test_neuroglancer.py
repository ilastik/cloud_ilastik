from cloud_ilastik.datasets import neuroglancer as ng, types


def test_indexed_color_shader():
    colors = ng._Color.get_colors(None, types.ColorTable.RGB)
    shader = ng._create_indexed_color_fragment_shader(colors)
    expected_shader = f"""vec4 COLOR_MASKS[4] = vec4[](
    vec4(0.0, 0.0, 0.0, 0.0),vec4(1.0, 0.0, 0.0, 1.0),vec4(0.0, 1.0, 0.0, 1.0),vec4(0.0, 0.0, 1.0, 1.0)
);
void main() {{
  uint val = toRaw(getDataValue());
  emitRGB(COLOR_MASKS[val]);
}}"""
    assert shader == expected_shader
