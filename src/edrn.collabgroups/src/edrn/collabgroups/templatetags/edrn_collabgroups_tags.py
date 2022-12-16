# encoding: utf-8

'''👥 EDRN Collaborative Groups: template tags.'''


from django import template
from eke.knowledge.models import Person

register = template.Library()


@register.inclusion_tag('edrn.collabgroups/chair-card.html', takes_context=False)
def chair_card(person: Person) -> dict:
    return {
        'gravatar_url': person.small_gravatar_url,
        'name': person.title,
        'photo': person.photo,
        'title': person.edrnTitle,
        'url': person.url,
    }
