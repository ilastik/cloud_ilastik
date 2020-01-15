import urllib.parse
import json

from django import template
from django.conf import settings

register = template.Library()


@register.filter(is_safe=True)
def viewer_url(url):
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
            }
        ],
        "selectedLayer": {"layer": "exported_data", "visible": True},
        "layout": "yz",  # TODO: Fix layout detection based on dataset properties
    }
    quoted_config = urllib.parse.quote(json.dumps(ng_config))
    return ng_url + quoted_config
