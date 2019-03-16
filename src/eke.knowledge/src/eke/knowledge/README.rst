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
    >>> with open('/tmp/log.html', 'w') as xxx: xxx.write(browser.contents)
    >>> browser.getControl(name='form.widgets.title').value = u'Body Systems'
    >>> browser.getControl(name='form.widgets.description').value = u'Some of testing organs.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = False
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'body-systems' in portal.keys()
    True

I have no idea how to fill in schema.List fields "through-the-web" using the
test browser, so::

    >>> folder = portal['body-systems']
    >>> folder.rdfDataSources = [u'testscheme://localhost/rdf/bodysystems']

Note that it's currently empty::

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
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'diseases' in portal.keys()
    True
    >>> folder = portal['diseases']
    >>> folder.rdfDataSources = [u'testscheme://localhost/rdf/diseases']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (2)...'
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


Publications
============

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-publicationfolder')
    >>> l.url.endswith('++add++eke.knowledge.publicationfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Publications'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing publications.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'publications' in portal.keys()
    True
    >>> folder = portal['publications']
    >>> folder.rdfDataSources= [u'testscheme://localhost/rdf/publications1', u'testscheme://localhost/rdf/publications2']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (4)...'
    >>> len(folder.keys())
    4
    >>> keys = folder.keys()
    >>> keys.sort()
    >>> keys
    ['a-combination-of-muc5ac-and-ca19-9-improves-the-diagnosis-of-pancreatic-cancer-a-multicenter-study', 'association-between-combined-tmprss2-erg-and-pca3-rna-urinary-testing-and-detection-of-aggressive-prostate-cancer', 'early-detection-of-nsclc-with-scfv-selected-against-igm-autoantibody', 'evaluation-of-serum-protein-profiling-by-surface-enhanced-laser-desorption-ionization-time-of-flight-mass-spectrometry-for-the-detection-of-prostate-cancer-i-assessment-of-platform-reproducibility']


Sites
=====

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-sitefolder')
    >>> l.url.endswith('++add++eke.knowledge.sitefolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Sites'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing sites.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'sites' in portal.keys()
    True
    >>> folder = portal['sites']
    >>> folder.rdfDataSources= [u'testscheme://localhost/rdf/sites']
    >>> folder.peopleDataSources = [u'testscheme://localhost/rdf/people']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'sites']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (4)...Objects Updated (2)...'
    >>> len(folder.keys())
    2
    >>> keys = folder.keys()
    >>> keys.sort()
    >>> keys
    ['240-vanderbilt-ingram-cancer-center', '815-h-lee-moffitt-cancer-center-and-research']
    >>> site = folder['240-vanderbilt-ingram-cancer-center']
    >>> site.keys()
    ['massion-pierre']
    >>> person = site['massion-pierre']
    >>> person.title
    u'Massion, Pierre'
    >>> person.surname
    u'Massion'
    >>> person.givenName
    u'Pierre'
    >>> person.edrnTitle
    u'EDRN Principal Investigator'
    >>> person.phone
    u'555-555-5555'
    >>> person.fax
    u'000-555-1212'
    >>> person.mbox
    u'mailto:pierre.massion@vanderbilt.edu'
    >>> person.accountName
    u'pmassion'


Protocols
=========

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-protocolfolder')
    >>> l.url.endswith('++add++eke.knowledge.protocolfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Protocols'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing protocols.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'protocols' in portal.keys()
    True
    >>> folder = portal['protocols']
    >>> folder.rdfDataSources= [u'testscheme://localhost/rdf/protocols']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'protocols']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (2)...'
    >>> len(folder.keys())
    2
    >>> keys = folder.keys()
    >>> keys.sort()
    >>> keys
    ['279-lung-reference-set-a-application-edward', '316-hepatocellular-carcinoma-early-detection']


Science Data
============

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-datasetfolder')
    >>> l.url.endswith('++add++eke.knowledge.datasetfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Datasets'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing datasets.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'datasets' in portal.keys()
    True
    >>> folder = portal['datasets']
    >>> folder.rdfDataSources= [u'testscheme://localhost/rdf/datasets']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'protocols', u'datasets']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (2)...'
    >>> len(folder.keys())
    2
    >>> keys = folder.keys()
    >>> keys.sort()
    >>> keys
    ['gstp1-methylation', 'university-of-pittsburg-ovarian-data']



Biomarkers
==========

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-biomarkerfolder')
    >>> l.url.endswith('++add++eke.knowledge.biomarkerfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Biomarkers'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing biomarkers.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.widgets.bmoDataSource').value = u'testscheme://localhost/rdf/bmo'
    >>> browser.getControl(name='form.widgets.bmuDataSource').value = u'testscheme://localhost/rdf/bmu'
    >>> browser.getControl(name='form.widgets.idDataSource').value = u'https://edrn.jpl.nasa.gov/cancerdataexpo/idsearch'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'biomarkers' in portal.keys()
    True
    >>> folder = portal['biomarkers']
    >>> folder.rdfDataSources = [u'testscheme://localhost/rdf/biomarkers']

Before ingesting, let's make sure the types work::

    >>> browser.open(portalURL + '/biomarkers')
    >>> l = browser.getLink(id='eke-knowledge-elementalbiomarker')
    >>> l.url.endswith('++add++eke.knowledge.elementalbiomarker')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.biomarkerType').value = u'Sticky'
    >>> browser.getControl(name='form.widgets.shortName').value = u'SHRT'
    >>> browser.getControl(name='form.widgets.hgncName').value = u'SHRT-1'
    >>> browser.getControl(name='form.widgets.bmAliases').value = u'ST-1\nST-2'
    >>> browser.getControl(name='form.widgets.indicatedBodySystems').value = u'Anus\nRectum'
    >>> browser.getControl(name='form.widgets.accessGroups').value = u'urn:group-1\nurn:group-2'
    >>> browser.getControl(name='form.widgets.biomarkerKind').value = u'Elemental'
    >>> browser.getControl(name='form.widgets.geneName').value = u'Eugene'
    >>> browser.getControl(name='form.widgets.uniProtAC').value = u'Accession Two'
    >>> browser.getControl(name='form.widgets.mutCount').value = u'123'
    >>> browser.getControl(name='form.widgets.pmidCount').value = u'456'
    >>> browser.getControl(name='form.widgets.cancerDOCount').value = u'789'
    >>> browser.getControl(name='form.widgets.affProtFuncSiteCount').value = u'10'
    >>> browser.getControl(name='form.widgets.qaState').value = u'Excellent'
    >>> browser.getControl(name='form.widgets.datasets').value = u'data-1\ndata-2'
    >>> browser.getControl(name='form.widgets.title').value = u'Sticky Biomarker'
    >>> browser.getControl(name='form.widgets.description').value = u'Careful, this one is sticky.'
    >>> browser.getControl(name='form.widgets.identifier').value = u'urn:biomarker:sticky'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'sticky-biomarker' in folder.keys()
    True
    >>> biomarker = folder['sticky-biomarker']
    >>> biomarker.biomarkerType
    u'Sticky'
    >>> biomarker.shortName
    u'SHRT'
    >>> biomarker.hgncName
    u'SHRT-1'

Need to post-form do: protocols, publications, datasets, and maybe bmAliases, and other multi-valued things above.
