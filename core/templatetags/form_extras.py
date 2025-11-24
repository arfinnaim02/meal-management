"""
Custom template filters for form rendering.

Provides an ``add_class`` filter to append CSS classes to form widgets
during rendering. This allows Tailwind classes to be applied in
templates without modifying the form definition.
"""

from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class: str):
    """Return a form field rendered with an additional CSS class."""
    return field.as_widget(attrs={**field.field.widget.attrs, 'class': css_class})