# encoding: utf-8

'''🎨 EDRN Theme: Django filters.'''

from django import template


register = template.Library()


@register.filter(is_safe=False)
def edrn_sorted_menu(menu_items):
    '''Sort menu items by their titles.

    Note that after years of having alphabetical menus, Christos now wants the drop-downs to be
    in "significance" order (#207). So this function is no longer being called from the
    ``sub_menu_dropdown.html`` template. It's preserved here in case he changes his mind again.
    '''
    menu_items.sort(key=lambda item: item.title)
    return menu_items
