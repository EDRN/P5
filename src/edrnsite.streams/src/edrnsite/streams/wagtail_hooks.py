# encoding: utf-8

'''🦦 EDRN Site streams: hooks for Wagtail.'''


from .models import DataElementExplorerPermissibleValue, DataElementExplorerAttribute, DataElementExplorerObject
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


class DEPermissibleValueAdmin(SnippetViewSet):
    model = DataElementExplorerPermissibleValue
    menu_label = 'Permissible Values'
    icon = 'tag'
    list_display = ('value', 'attribute')


class DEExplorerAttributeAdmin(SnippetViewSet):
    model = DataElementExplorerAttribute
    menu_label = 'Attributes'
    icon = 'list-ul'
    list_display = ('text', 'data_type', 'obj')


class DEExplorerObjectAdmin(SnippetViewSet):
    model = DataElementExplorerObject
    menu_label = 'Objects'
    icon = 'folder'
    list_display = ('name', 'parent')


class DEGroup(SnippetViewSetGroup):
    menu_label = 'DE Explorer'
    icon = 'folder-open-inverse'
    menu_order = 475
    items = (DEExplorerObjectAdmin, DEExplorerAttributeAdmin, DEPermissibleValueAdmin)


register_snippet(DEGroup)
