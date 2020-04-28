import urllib.parse

from django import template

register = template.Library()


@register.filter
def doi_url(value):
    return urllib.parse.urljoin("https://doi.org/", urllib.parse.quote(value))
