# encoding: utf-8

from edrnsite.content.models import HomePage
from wagtail.models import Site


_search_description = '''
The Early Detection Research Network pioneers the discovery and clinical application of biomarkers.
'''


def set_site(hostname=None):
    '''Set up the Wagtail ``Site`` object for EDRN.

    We assume the default site is the EDRN site. Returns both the site and the home page.
    If the ``hostname`` is given, it'll be used to set the hostname for the EDRN site.
    Defaults to ``edrn.nci.nih.gov``.
    '''
    site = Site.objects.filter(is_default_site=True).first()
    site.site_name = 'Early Detection Research Network'
    site.hostname = hostname if hostname else 'edrn.nci.nih.gov'
    site.save()
    old_root = site.root_page.specific
    if old_root.title == 'EDRN':
        return site, old_root

    mega_root = old_root.get_parent()
    home_page = HomePage(
        title='EDRN', draft_title='🧬 EDRN', seo_title='Early Detection Research Network',
        search_description=_search_description.strip(),
        live=True, slug=old_root.slug, path=old_root.path, depth=old_root.depth, url_path=old_root.url_path,
    )
    site.root_page = home_page
    old_root.delete()
    mega_root.save()
    home_page.save()
    site.save()
    return site, home_page
