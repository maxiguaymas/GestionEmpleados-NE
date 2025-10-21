from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='split')
def split(value, key):
    """
    Returns the value turned into a list.
    """
    return value.split(key)

@register.filter(name='strip_ul_li')
def strip_ul_li(value):
    cleaned_value = re.sub(r'</?ul>|<\/?li>', '', value)
    return mark_safe(cleaned_value)