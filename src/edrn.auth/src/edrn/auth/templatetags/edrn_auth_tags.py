# encoding: utf-8

'''🔐 EDRN auth: tags.'''

from django import template
from django.template.context import Context
from django.urls import reverse
from edrnsite.controls.models import Informatics
from wagtail.models import Site

register = template.Library()


@register.inclusion_tag('edrn.auth/personal-links.html', takes_context=True)
def edrn_personal_links(context: Context) -> dict:
    informatics = Informatics.for_site(Site.objects.filter(is_default_site=True).first())
    params = {'authenticated': False, 'dmcc': informatics.dmcc_url}
    request = context.get('request')
    if request.user.is_authenticated:
        params['authenticated'] = True
        try:
            params['name'] = request.user.ldap_user.attrs['cn'][0]
        except (AttributeError, KeyError, IndexError, TypeError):
            params['name'] = f'{request.user.first_name} {request.user.last_name}'.strip()
        params['logout'] = reverse('logout') + '?next=' + request.path
    else:
        params['login'] = reverse('wagtailcore_login') + '?next=' + request.path
    return params
