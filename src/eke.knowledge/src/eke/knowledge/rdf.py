# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Resource Description Format (RDF) services.'''

from dataclasses import dataclass
from django.db.models.fields import Field
from django.core.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


@dataclass
class RDFAttribute:
    '''An attribute of a model object controlled by the Resource Description Format.'''
    name: str            # Name of the field in the model 
    scalar: bool = True  # True if the field is a scalar, False if it's multi-valued

    def compute_new_value(self, modelField: Field, value: str, predicates: dict) -> object:
        '''Figure out what the new value should be.

        For the given ``field`` and a new string `value`, compute what the Python object for that
        value is. Frequently, it's just another string, but it could be a number, a ``datetime``,
        etc. Subclasses can override this if they need to compute a more exotic value, and access
        to the ``predicates`` is provided for such computations.
        '''
        return modelField.to_python(value)

    def modify_field(self, obj: object, values: list, modelField: Field, predicates: dict) -> bool:
        '''Potentially modify a field.

        In the ``KnowledgeObject`` obj which has a ``modelField``, we set its value(s) from ``values``.
        The ``predicates`` are passed in in case they're needed too. We return True if we changed the
        value(s) and False if the value(s) were unchanged.
        '''
        modified = False
        try:
            # Get the narrowed Wagtail class
            obj = obj.specific
        except AttributeError:
            # Nope, it's just a plain Djanog model
            pass

        # We're dealing with just literal values, not messy relations to other objects.
        if self.scalar:
            # It's a single value to contend with, the easiest case of all. Compare and see if they're
            # different.
            currentValue = modelField.value_from_object(obj)
            try:
                newValue = self.compute_new_value(modelField, str(values[0]), predicates)
                if currentValue != newValue:
                    # Different, so simply make the update
                    setattr(obj, self.name, newValue)
                    modified = True
            except ValidationError:
                # Whatever the string was, it didn't turn into a valid python type, so leave it "unmodified"
                pass
        else:
            # For "multi-valued" RDF fields, we do strings only, and we do clustered Orderables that have
            # a single ``value`` field that contains the string.
            accessorName = modelField.get_accessor_name()
            currentValues = [i.value for i in getattr(obj, accessorName).all()]
            newValues = [str(i) for i in values]
            if currentValues != newValues:
                cls = modelField.related_model
                values = [cls(value=i) for i in newValues]
                try:
                    # Clustered orderable
                    setattr(obj, accessorName, values)
                except TypeError:
                    # Django many
                    getattr(obj, accessorName).set(values, bulk=False)
                obj.save()
                for i in values: i.save()
                modified = True
        return modified


class RelativeRDFAttribute(RDFAttribute):
    '''An attribute of a model that refers to other model instances and is controlled by RDF.'''

    def modify_field(self, obj: object, values: list, modelField: Field, predicates: dict) -> bool:
        '''Potentially modify a relative field.

        In the `KnowledgeObject` obj which has a `modelField`, we set its relations from `values`.
        The `predicates` are passed in in case they're needed too. We return True if we changed the
        value(s) and False if the value(s) were unchanged.
        '''
        from .knowledge import KnowledgeObject
        modified = False
        try:
            # Narrow the Wagtail based object
            obj = obj.specific
        except AttributeError:
            # Nope, it's a plain Django model
            pass
        if self.scalar:
            # It's a ForeignKey field, meaning a single relation object … get its ID and the ID of the
            # potentially new object
            current, newID = getattr(obj, self.name), str(values[0])
            if current is None or current.identifier != newID:
                # They're different, so find the object of our desire
                results = KnowledgeObject.objects.filter(identifier__exact=newID).specific()
                if len(results) == 0:
                    # It's not in the database, so just log it
                    _logger.info('Object %s references unknown object %s; ignoring', obj.identifier, newID)
                else:
                    # Got it, so set it
                    setattr(obj, self.name, results[0])
                    modified = True
        else:
            # It's a ParentalManyToManyField, meaning potentially many objects. Find the current set of
            # identifiers and the new set and compare.
            currentRelatives = frozenset([i.identifier for i in getattr(obj, self.name).all()])
            newRelatives = frozenset([str(i) for i in values])
            if currentRelatives != newRelatives:
                # They're different, so out with the old and in with the new
                relatives = KnowledgeObject.objects.filter(identifier__in=newRelatives).specific()
                getattr(obj, self.name).set(relatives)  # 🤔 Should clear=True be passed?
                modified = True
        return modified
