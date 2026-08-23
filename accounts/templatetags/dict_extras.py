"""
Shared template filters.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Look up a dictionary value by key in templates: {{ mydict|get_item:key }}"""
    if dictionary is None:
        return None
    return dictionary.get(key)
