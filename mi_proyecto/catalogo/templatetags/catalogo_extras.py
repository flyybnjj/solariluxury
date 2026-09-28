"""Custom template filters for the catalogo app."""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Return dictionary[key] — used in admin templates to access dict by variable key."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)
