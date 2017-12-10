from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(some_dict, key):
    return some_dict.get(key, '')
