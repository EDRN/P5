# encoding: utf-8

'''💁‍♀️ EDRN Knowledge Environment: Django-style signals.'''

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .protocols import Protocol


@receiver(pre_save, sender=Protocol)
def synchronize_protocol_pi_name(sender, **kwargs):
    '''Synchronize a protocol's lead investigator site's PI name into the ``piName`` field.
    '''
    try:
        instance = kwargs['instance']
        instance.piName = instance.leadInvestigatorSite.pi.title
    except (KeyError, AttributeError):
        pass


# 🤬 Get bent
# @receiver(pre_save, sender=CollaborativeGroup)
# def synchronize_protocol_collab_group(sender, **kwargs):
#     try:
#         instance = kwargs['instance']
#         protocol = instance.page
#         cgs = set([i for i in protocol.collaborativeGroupsDeNormalized.split(',') if i])
#         if instance.value not in cgs:
#             cgs.add(instance.value)
#             protocol.collaborativeGroupsDeNormalized = ','.join(list(cgs))
#             protocol.save()
#     except (KeyError, AttributeError):
#         pass
