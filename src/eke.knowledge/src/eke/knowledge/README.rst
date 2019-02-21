Knowledge objects and RDF ingest for the EDRN Knowledge Environment.


Functional Tests
================

First, we shall require a test browser::

    >>> app = layer['app']
    >>> from plone.testing.z2 import Browser
    >>> from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
    >>> browser = Browser(app)
    >>> browser.handleErrors = False
    >>> browser.addHeader('Authorization', 'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD))
    >>> portal = layer['portal']    
    >>> portalURL = portal.absolute_url()

Now to exercise the code.


Body System Folders
===================

Body systems (aka Organs) are contained in folders that can go anywhere::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-bodysystemfolder')
    >>> l.url.endswith('++add++eke.knowledge.bodysystemfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Body Systems'
    >>> browser.getControl(name='form.widgets.description').value = u'Some of testing organs.'
    >>> browser.getControl(name='form.widgets.rdfDataSource').value = u'testscheme://localhost/rdf/bodysystems'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = False
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'body-systems' in portal.keys()
    True

Currently empty::

    >>> folder = portal['body-systems']
    >>> len(folder.keys())
    0

We set ``ingestEnabled`` to ``False``.  So if we try to ingest that folder,
nothing will happen.  Proof::

    >>> from plone.registry.interfaces import IRegistry
    >>> from zope.component import getUtility
    >>> registry = getUtility(IRegistry)
    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems']
    >>> import transaction
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> len(folder.keys())
    0

Let's enable ingest and try again::

    >>> browser.open(portalURL + '/body-systems/@@edit')    
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (2)...'
    >>> len(folder.keys())
    2
    >>> keys = folder.keys()
    >>> keys.sort()
    >>> keys
    ['anus', 'rectum']
    >>> obj1 = folder['anus']
    >>> obj1.title
    u'Anus'
    >>> obj1.identifier
    u'urn:edrn:organs:anus'
    >>> obj2 = folder['rectum']
    >>> obj2.title
    u'Rectum'
    >>> obj2.identifier
    u'urn:edrn:organs:rectum'
