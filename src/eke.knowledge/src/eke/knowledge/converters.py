# encoding: utf-8


from collective.dexteritytextindexer.converters import DefaultDexterityTextIndexFieldConverter
from collective.dexteritytextindexer.interfaces import IDexterityTextIndexFieldConverter
from plone.dexterity.interfaces import IDexterityContent
from z3c.form.interfaces import IWidget
from z3c.relationfield.interfaces import IRelationChoice, IRelationList
from zope.component import adapter
from zope.interface import implementer

# TODO: If this works, we can try it for mutli-valued relations too:
# from z3c.relationfield.interfaces import IRelationList  #


@implementer(IDexterityTextIndexFieldConverter)
@adapter(IDexterityContent, IRelationChoice, IWidget)
class RelationChoiceFieldConverter(DefaultDexterityTextIndexFieldConverter):
    u'''Make relation 1–1 fields searchable by de-referencing their objects and using their
    titles their search corpus.  Maybe the Plone Collectiive would find this useful?
    '''
    def convert(self):
        storage = self.field.interface(self.context)
        rv = self.field.get(storage)
        if rv and rv.to_object and rv.to_object.title:
            return rv.to_object.title.encode('utf-8')
        return ''


@implementer(IDexterityTextIndexFieldConverter)
@adapter(IDexterityContent, IRelationList, IWidget)
class RelationListFieldConverter(DefaultDexterityTextIndexFieldConverter):
    u'''Make relation 1–n fields searchable by de-referencing their objects and using
    their titles as the search corpus. Maybe the Plone Collective would find this useful?
    '''
    def convert(self):
        storage = self.field.interface(self.context)
        rvs = self.field.get(storage)
        titles = []
        if rvs:
            for rv in rvs:
                if rv.to_object and rv.to_object.title:
                    titles.append(rv.to_object.title.encode('utf-8'))
        return ' '.join(titles)
