# encoding: utf-8

'''😌 EDRN Site content: hooks for Wagtail.'''


from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register, ModelAdminGroup
from .models import CDEPermissibleValue, CDEExplorerAttribute, CDEExplorerObject


class CDEPermissibleValueAdmin(ModelAdmin):
    model = CDEPermissibleValue
    menu_label = 'Permissible Values'
    menu_icon = 'tag'
    list_display = ('value',)


class CDEExplorerAttributeAdmin(ModelAdmin):
    model = CDEExplorerAttribute
    menu_label = 'Attributes'
    menu_icon = 'list-ul'
    list_display = ('text', 'required')


class CDEExplorerObjectAdmin(ModelAdmin):
    model = CDEExplorerObject
    menu_label = 'Objects'
    menu_icon = 'folder'
    list_display = ('name',)


class CDEGroup(ModelAdminGroup):
    menu_label = 'CDEs'
    menu_icon = 'folder-open-inverse'
    menu_order = 475
    items = (CDEExplorerObjectAdmin, CDEExplorerAttributeAdmin, CDEPermissibleValueAdmin)


modeladmin_register(CDEGroup)
