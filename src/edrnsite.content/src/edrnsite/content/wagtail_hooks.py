# encoding: utf-8

'''😌 EDRN Site content: hooks for Wagtail.'''


from .models import CDEPermissibleValue, CDEExplorerAttribute, CDEExplorerObject
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


class CDEPermissibleValueAdmin(SnippetViewSet):
    model = CDEPermissibleValue
    menu_label = 'Permissible Values'
    icon = 'tag'
    list_display = ('value',)


class CDEExplorerAttributeAdmin(SnippetViewSet):
    model = CDEExplorerAttribute
    menu_label = 'Attributes'
    icon = 'list-ul'
    list_display = ('text', 'required')


class CDEExplorerObjectAdmin(SnippetViewSet):
    model = CDEExplorerObject
    menu_label = 'Objects'
    icon = 'folder'
    list_display = ('name',)


class CDEGroup(SnippetViewSetGroup):
    menu_label = 'CDEs'
    icon = 'folder-open-inverse'
    menu_order = 475
    items = (CDEExplorerObjectAdmin, CDEExplorerAttributeAdmin, CDEPermissibleValueAdmin)


register_snippet(CDEGroup)
