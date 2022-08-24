# encoding: utf-8

'''🧬 EDRN Site: Wagtail hooks and interceptors.'''

from wagtail.core import hooks
from django.http import HttpRequest


@hooks.register('construct_page_action_menu')
def make_publish_default_action(menu_items: list, request: HttpRequest, context: dict):
    '''Instead of "Submit", make "Publish" the default on the save menu.

    Although it would be a cool feature to have writers submit their pages for review by executive
    editors, in practice @nutjob4life is the main writer/editor and the others who do so can be
    counted on just one hand—and a hand that suffered a terrible accident at that. So, to keep
    from having a repetitive stress injury, we make it so you can one-click "Publish" instead
    of having to click, navigate, and then hit "Publish".

    See https://www.yellowduck.be/posts/making-publish-default-action-wagtail
    '''
    for (index, item) in enumerate(menu_items):
        if item.name == 'action-publish':
            menu_items.pop(index)
            menu_items.insert(0, item)
            break
