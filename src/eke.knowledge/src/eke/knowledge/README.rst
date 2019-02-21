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


Body Systems
============

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


Diseases
========

Similar to body systems but also contain a reference field::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-diseasefolder')
    >>> l.url.endswith('++add++eke.knowledge.diseasefolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Diseases'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing diseases.'
    >>> browser.getControl(name='form.widgets.rdfDataSource').value = u'testscheme://localhost/rdf/diseases'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'diseases' in portal.keys()
    True

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (2)...'
    >>> folder = portal['diseases']
    >>> len(folder.keys())
    2
    >>> keys = folder.keys()
    >>> keys.sort()
    >>> keys
    ['anal-seepage', 'rectocele']
    >>> obj1 = folder['anal-seepage']
    >>> obj1.title
    u'Anal seepage'
    >>> obj1.identifier
    u'http://edrn.nci.nih.gov/data/diseases/1'
    >>> obj1.description
    u'Seepage of pus or mucus from the anus'
    >>> obj1.icd9Code
    u'204.9'
    >>> obj1.icd10Code
    u'C81-Q96'
    >>> len(obj1.affectedOrgans)
    1
    >>> obj1.affectedOrgans[0].to_object.title
    u'Anus'
