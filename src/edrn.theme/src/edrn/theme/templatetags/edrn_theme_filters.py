# encoding: utf-8

'''🎨 EDRN Theme: Django filters.'''

from django import template


register = template.Library()


@register.filter(is_safe=False)
def edrn_sorted_menu(menu_items):
    '''Sort menu items by their titles.'''
    menu_items.sort(key=lambda item: item.title)
    return menu_items
