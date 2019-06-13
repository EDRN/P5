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

We'll also have a second browser that's unprivileged for some later
demonstrations::

    >>> unprivilegedBrowser = Browser(app)

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
    >>> publicationsFolder = portal['publications']
    >>> publicationsFolder.rdfDataSources= [u'testscheme://localhost/rdf/publications1', u'testscheme://localhost/rdf/publications2']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (4)...'
    >>> len(publicationsFolder.keys())
    4
    >>> keys = publicationsFolder.keys()
    >>> keys.sort()
    >>> keys
    ['15613711-evaluation-of-serum-protein-profiling-by', '23585862-early-detection-of-nsclc-with-scfv', '27845339-a-combination-of-muc5ac-and-ca19-9', '28520829-association-between-combined-tmprss2-erg']
    >>> publication = publicationsFolder['15613711-evaluation-of-serum-protein-profiling-by']
    >>> publication.title
    u'Evaluation of serum protein profiling by surface-enhanced laser desorption/ionization time-of-flight mass spectrometry for the detection of prostate cancer: I. Assessment of platform reproducibility.'
    >>> authors = list(publication.authors)
    >>> authors.sort()
    >>> authors
    [u'Adam BL', u'Banez LL', u'Bigbee WL', u'Campos D', u'Cazares LH', u'Chan DW', u'Feng Z', u'Grizzle WE', u'Izbicka E', u'Kagan J', u'Malik G', u'McLerran D', u'Moul JW', u'Partin A', u'Prasanna P', u'Rosenzweig J', u'Semmes OJ', u'Sokoll LJ', u'Srivastava S', u'Srivastava S', u'Thompson I', u'Welsh MJ', u'White N', u'Winget M', u'Yasui Y', u'Zhang Z', u'Zhu L']
    >>> publication.volume
    u'51'
    >>> publication.journal
    u'Clin. Chem.'
    >>> publication.pubMedID
    u'15613711'
    >>> publication.year
    u'2005'
    >>> publication.siteID
    u'http://edrn.nci.nih.gov/data/sites/815'

The statistical graphics made a comeback::

    >>> browser.open(portalURL + '/publications/@@publication_timeline_report')
    >>> browser.contents
    '...<style>...<script>...'


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
    >>> sitesFolder = portal['sites']
    >>> sitesFolder.rdfDataSources= [u'testscheme://localhost/rdf/sites']
    >>> sitesFolder.peopleDataSources = [u'testscheme://localhost/rdf/people']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'sites']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (19)...'
    >>> len(sitesFolder.keys())
    2
    >>> keys = sitesFolder.keys()
    >>> keys.sort()
    >>> keys
    ['240-vanderbilt-ingram-cancer-center', '815-h-lee-moffitt-cancer-center-and-research']
    >>> site = sitesFolder['240-vanderbilt-ingram-cancer-center']
    >>> site.identifier
    u'http://edrn.nci.nih.gov/data/sites/240'
    >>> site.dmccSiteID
    u'240'
    >>> site.piName
    u'Massion, Pierre'
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

There's not just a PI, there are other people too::

    >>> len(site.keys())
    12
    >>> peopleObjects = list(site.keys())
    >>> peopleObjects.sort()
    >>> peopleObjects
    ['antic-sanja', 'banerjee-priyanka', 'chambliss-katelyn', 'cleary-jaclyn', 'davis-harriet-stratton', 'massion-pierre', 'muterspaugh-anel-w', 'owens-janiqua', 'shah-chirayu', 'spencer-brady', 'sullivan-amy', 'walker-ronald-clark']

And some of those people have positions of (lesser) power::

    >>> len(site.coPrincipalInvestigators)
    2
    >>> coPIs = [i.to_object.title for i in site.coPrincipalInvestigators]
    >>> coPIs.sort()
    >>> coPIs
    [u'Schabath, Matthew', u'Thompson, Zachary']
    >>> site.coInvestigators[0].to_object.title
    u'Shah, Chirayu'
    >>> site.investigators[0].to_object.title
    u'Shah, Chirayu'


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
    >>> protocolsFolder = portal['protocols']
    >>> protocolsFolder.rdfDataSources= [u'testscheme://localhost/rdf/protocols']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'sites', u'protocols']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (19)...'
    >>> len(protocolsFolder.keys())
    2
    >>> keys = protocolsFolder.keys()
    >>> keys.sort()
    >>> keys
    ['279-lung-reference-set-a-application-edward', '316-hepatocellular-carcinoma-early-detection']
    >>> protocol = protocolsFolder['279-lung-reference-set-a-application-edward']
    >>> protocol.description
    u'Sticky'


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
    >>> dataFolder = portal['datasets']
    >>> dataFolder.rdfDataSources= [u'testscheme://localhost/rdf/datasets']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'sites', u'protocols', u'datasets']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (19)...'
    >>> len(dataFolder.keys())
    2
    >>> keys = dataFolder.keys()
    >>> keys.sort()
    >>> keys
    ['gstp1-methylation', 'university-of-pittsburg-ovarian-data']
    >>> dataset = dataFolder['gstp1-methylation']
    >>> dataset.bodySystemName
    u'Prostate'

And the statistical graphics are back::

    >>> browser.open(portalURL + '/datasets/@@dataset_summary_report')
    >>> browser.contents
    '...<style>...<script>...datasetColor...'


Groups
======

First, a folder to hold them all, and in the darkness bind them::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-collaborationsfolder')
    >>> l.url.endswith('++add++eke.knowledge.collaborationsfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Collaborative Groups'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing collaborative groups.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> browser.open(portalURL + '/collaborative-groups/content_status_modify?workflow_action=publish')
    >>> 'collaborative-groups' in portal.keys()
    True
    >>> collaborationsFolder = portal['collaborative-groups']
    >>> collaborationsFolder.title
    u'Collaborative Groups'
    >>> collaborationsFolder.description
    u'Some testing collaborative groups.'
    >>> collaborationsFolder.ingestEnabled
    True
    >>> collaborationsFolder.rdfDataSources = [u'testscheme://localhost/rdf/committees']
    >>> len(collaborationsFolder.rdfDataSources)
    1
    >>> collaborationsFolder.rdfDataSources[0]
    u'testscheme://localhost/rdf/committees'
    >>> transaction.commit()    


Group Spaces
------------

Now let's try group workspaces::

    >>> browser.open(portalURL + '/collaborative-groups')
    >>> l = browser.getLink(id='eke-knowledge-groupspacefolder')
    >>> l.url.endswith('++add++eke.knowledge.groupspacefolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'MySpace'
    >>> browser.getControl(name='form.widgets.description').value = u'A defunct workspace.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> browser.open(portalURL + '/collaborative-groups/myspace/content_status_modify?workflow_action=publish')
    >>> browser.open(portalURL + '/collaborative-groups/myspace/index_html/content_status_modify?workflow_action=publish')
    >>> group = collaborationsFolder['myspace']

The index page is automatically created::

    >>> groupIndex = group['index_html']
    >>> from z3c.relationfield import RelationValue
    >>> from zope.intid.interfaces import IIntIds
    >>> from z3c.relationfield import RelationValue
    >>> intIDUtil = getUtility(IIntIds)
    >>> groupIndex.chair = RelationValue(intIDUtil.getId(site['antic-sanja']))
    >>> groupIndex.coChair = RelationValue(intIDUtil.getId(site['banerjee-priyanka']))
    >>> groupIndex.members = [RelationValue(intIDUtil.getId(site[i])) for i in ('spencer-brady', 'sullivan-amy')]
    >>> from zope.lifecycleevent import ObjectModifiedEvent
    >>> from zope.event import notify
    >>> notify(ObjectModifiedEvent(groupIndex))
    >>> transaction.commit()
    >>> groupIndex.chair.to_object.title
    u'Antic, Sanja'
    >>> groupIndex.coChair.to_object.title
    u'Banerjee, Priyanka'
    >>> members = [i.to_object.title for i in groupIndex.members]
    >>> members.sort()
    >>> members
    [u'Spencer, Brady', u'Sullivan, Amy']

Group workspaces—which are folders—should automatically create an index page
that's the default view of the folder, and turn off the right-side portlets::

    >>> 'portal-column-two' in browser.contents
    False
    >>> 'index_html' in group.keys()
    True
    >>> group.getDefaultPage()
    'index_html'

They also let you add various items but use the constrain-types feature to
keep the "index" type off the menu::

    >>> from Products.CMFPlone.interfaces.constrains import ENABLED, IConstrainTypes
    >>> i = IConstrainTypes(group)
    >>> i.getConstrainTypesMode() == ENABLED
    True

At this point I'd want to see if ``i.getImmediatelyAddableTypes()`` was right,
and it works in operation, but here in this test it always returns an empty 
list. Nuts to that.

Well, at least you can comment::

    >>> browser.open(portalURL + '/collaborative-groups/myspace')
    >>> 'Add comment' in browser.contents
    True

But only if you're privileged::

    >>> unprivilegedBrowser.open(portalURL + '/collaborative-groups/myspace')
    >>> 'Add comment' in unprivilegedBrowser.contents
    False

Check out these members::

    >>> browser.contents
    '...Chair...Antic, Sanja...Co-Chair...Banerjee, Priyanka...Members...Spencer, Brady...Sullivan, Amy...'

Plus tabs for the group's stuff::

    >>> overview = browser.contents.index('overviewTab')
    >>> calendar = browser.contents.index('calendarTab')
    >>> documents = browser.contents.index('documentsTab')
    >>> overview < calendar < documents
    True

Since we're logged in, the special note about logging in to view additional
information doesn't appear (eventually)::

    >>> 'If you are a member of this group,' in browser.contents
    False


Collaborative Groups
--------------------

These are group workspaces but linked data::

    >>> browser.open(portalURL + '/collaborative-groups')
    >>> l = browser.getLink(id='eke-knowledge-collaborativegroupfolder')
    >>> l.url.endswith('++add++eke.knowledge.collaborativegroupfolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Guts'
    >>> browser.getControl(name='form.widgets.description').value = u'The guts collaborative group.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> browser.open(portalURL + '/collaborative-groups/guts/content_status_modify?workflow_action=publish')
    >>> browser.open(portalURL + '/collaborative-groups/guts/index_html/content_status_modify?workflow_action=publish')
    >>> group = collaborationsFolder['guts']    

Just like group spaces, the index page is automatically created::

    >>> groupIndex = group['index_html']
    >>> from z3c.relationfield import RelationValue
    >>> from zope.intid.interfaces import IIntIds
    >>> from z3c.relationfield import RelationValue
    >>> intIDUtil = getUtility(IIntIds)
    >>> groupIndex.chair = RelationValue(intIDUtil.getId(site['antic-sanja']))
    >>> groupIndex.coChair = RelationValue(intIDUtil.getId(site['banerjee-priyanka']))
    >>> groupIndex.members = [RelationValue(intIDUtil.getId(site[i])) for i in ('spencer-brady', 'sullivan-amy')]
    >>> groupIndex.biomarkers = []
    >>> groupIndex.protocols = [RelationValue(intIDUtil.getId(protocolsFolder[i])) for i in protocolsFolder.keys()]
    >>> groupIndex.datasets = [RelationValue(intIDUtil.getId(dataFolder[i])) for i in dataFolder.keys()]
    >>> from zope.lifecycleevent import ObjectModifiedEvent
    >>> from zope.event import notify
    >>> notify(ObjectModifiedEvent(groupIndex))
    >>> transaction.commit()
    >>> groupIndex.chair.to_object.title
    u'Antic, Sanja'
    >>> groupIndex.coChair.to_object.title
    u'Banerjee, Priyanka'
    >>> members = [i.to_object.title for i in groupIndex.members]
    >>> members.sort()
    >>> members
    [u'Spencer, Brady', u'Sullivan, Amy']
    >>> groupIndex.biomarkers
    []
    >>> groupProtocols = [i.to_object.title for i in groupIndex.protocols]
    >>> groupProtocols.sort()
    >>> groupProtocols
    [u'Hepatocellular carcinoma Early Detection Strategy study', u'Lung Reference Set A Application:  Edward Hirschowitz - University of Kentucky (2009)']
    >>> groupDatasets = [i.to_object.title for i in groupIndex.datasets]
    >>> groupDatasets.sort()
    >>> groupDatasets
    [u'GSTP1 Methylation', u'University of Pittsburg Ovarian Data']

It's also set as the display for the collaborative group::

    >>> 'index_html' in group.keys()
    True
    >>> group.getDefaultPage()
    'index_html'

And we also make room::

    >>> 'portal-column-two' in browser.contents
    False

Also like plain group spaces, it uses the constrain-types feature to keep the
"index" type off the menu::

    >>> from Products.CMFPlone.interfaces.constrains import ENABLED, IConstrainTypes
    >>> i = IConstrainTypes(group)
    >>> i.getConstrainTypesMode() == ENABLED
    True

And you can comment::

    >>> browser.open(portalURL + '/collaborative-groups/guts')
    >>> 'Add comment' in browser.contents
    True

But only if you're privileged::

    >>> unprivilegedBrowser.open(portalURL + '/collaborative-groups/guts')
    >>> 'Add comment' in unprivilegedBrowser.contents
    False

And there are members::

    >>> browser.contents
    '...Chair...Antic, Sanja...Co-Chair...Banerjee, Priyanka...Members...Spencer, Brady...Sullivan, Amy...'

And space for stuff:

    >>> overview = browser.contents.index('overviewTab')
    >>> biomarkers = browser.contents.index('biomarkersTab')
    >>> protocols = browser.contents.index('protocolsTab')
    >>> data = browser.contents.index('dataTab')
    >>> calendar = browser.contents.index('calendarTab')
    >>> documents = browser.contents.index('documentsTab')
    >>> overview < biomarkers < protocols < data < calendar < documents
    True

Note also that, due to lack of room, we've combined Projects and Protocols::

    >>> browser.contents
    '...Projects/Protocols...'


Committees RDF
--------------

Note that there's RDF ingest for the ``eke.knowledge.collaborationsfolder``::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'sites', u'protocols', u'datasets', u'collaborative-groups']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...Objects Created (37)...'


Miscellaneous Resources
=======================

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='eke-knowledge-resourcefolder')
    >>> l.url.endswith('++add++eke.knowledge.resourcefolder')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Resources'
    >>> browser.getControl(name='form.widgets.description').value = u'Some testing resources.'
    >>> browser.getControl(name='form.widgets.ingestEnabled:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'resources' in portal.keys()
    True
    >>> resourcesFolder = portal['resources']
    >>> resourcesFolder.rdfDataSources= [u'testscheme://localhost/rdf/resources']

Ingesting::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'body-systems', u'diseases', u'publications', u'sites', u'protocols', u'datasets', u'collaborative-groups', u'resources']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (39)...'
    >>> len(resourcesFolder.keys())
    2
    >>> keys = resourcesFolder.keys()
    >>> keys.sort()
    >>> keys
    ['http-google-com', 'http-yahoo-com']
    >>> resource = resourcesFolder['http-google-com']
    >>> resource.title
    u'A search engine'
    >>> resource.identifier
    u'http://google.com/'

Note that it's properly hyperlinked too::

    >>> browser.open(portalURL + '/resources/http-google-com')
    >>> browser.contents
    '...href="http://google.com/"...'


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
    >>> browser.getControl(name='form.widgets.bmoDataSource').value = u'testscheme://localhost/rdf/biomarker-organs-a'
    >>> browser.getControl(name='form.widgets.bmuDataSource').value = u'testscheme://localhost/rdf/bmu'
    >>> browser.getControl(name='form.widgets.idDataSource').value = u'https://edrn.jpl.nasa.gov/cancerdataexpo/idsearch'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'biomarkers' in portal.keys()
    True
    >>> biomarkersFolder = portal['biomarkers']
    >>> biomarkersFolder.rdfDataSources = [u'testscheme://localhost/rdf/biomarker-a']
    >>> transaction.commit()

Before ingesting, let's make sure the types work, like the folder we just made::

    >>> biomarkersFolder.title
    u'Biomarkers'
    >>> biomarkersFolder.description
    u'Some testing biomarkers.'
    >>> biomarkersFolder.ingestEnabled
    True
    >>> biomarkersFolder.rdfDataSources
    [u'testscheme://localhost/rdf/biomarker-a']
    >>> biomarkersFolder.bmoDataSource
    u'testscheme://localhost/rdf/biomarker-organs-a'
    >>> biomarkersFolder.bmuDataSource
    u'testscheme://localhost/rdf/bmu'
    >>> biomarkersFolder.idDataSource
    u'https://edrn.jpl.nasa.gov/cancerdataexpo/idsearch'

These folders contain biomarkers (both elemental and panel)::

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
    >>> 'sticky-biomarker' in biomarkersFolder.keys()
    True
    >>> biomarker = biomarkersFolder['sticky-biomarker']

Now let's link it up::

    >>> from zope.component import getUtility
    >>> from zope.intid.interfaces import IIntIds
    >>> from z3c.relationfield import RelationValue
    >>> intIDUtil = getUtility(IIntIds)
    >>> protocolRVs = [RelationValue(intIDUtil.getId(obj)) for (identifier, obj) in protocolsFolder.contentItems()]
    >>> pubRVs = [RelationValue(intIDUtil.getId(obj)) for (identifier, obj) in publicationsFolder.contentItems()]
    >>> biomarker.protocols, biomarker.publications = protocolRVs, pubRVs
    >>> from zope.lifecycleevent import ObjectModifiedEvent
    >>> from zope.event import notify
    >>> notify(ObjectModifiedEvent(biomarker))

And check it out::

    >>> biomarker.biomarkerType
    u'Sticky'
    >>> biomarker.shortName
    u'SHRT'
    >>> biomarker.hgncName
    u'SHRT-1'
    >>> linkedProtocols = [i.to_path for i in biomarker.protocols]
    >>> linkedProtocols.sort()
    >>> linkedProtocols
    ['/plone/protocols/279-lung-reference-set-a-application-edward', '/plone/protocols/316-hepatocellular-carcinoma-early-detection']
    >>> linkedPubs = [i.to_path for i in biomarker.publications]
    >>> linkedPubs.sort()
    >>> linkedPubs
    ['/plone/publications/15613711-evaluation-of-serum-protein-profiling-by', '/plone/publications/23585862-early-detection-of-nsclc-with-scfv', '/plone/publications/27845339-a-combination-of-muc5ac-and-ca19-9', '/plone/publications/28520829-association-between-combined-tmprss2-erg']


Child objects work too::

    >>> browser.open(portalURL + '/biomarkers/sticky-biomarker')
    >>> l = browser.getLink(id='eke-knowledge-biomarkerbodysystem')
    >>> l.url.endswith('++add++eke.knowledge.biomarkerbodysystem')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Colon'
    >>> browser.getControl(name='form.widgets.description').value = u'Longish organ.'
    >>> browser.getControl(name='form.widgets.identifier').value = u'urn:biomarker:sticky:colon'
    >>> browser.getControl(name='form.widgets.qaState').value = u'High'
    >>> browser.getControl(name='form.widgets.phase').value = u'Laservision'
    >>> browser.getControl(name='form.widgets.performanceComment').value = u'Oh yeah baby.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'colon' in biomarker.keys()
    True
    >>> biomarkerBodySystem = biomarker['colon']
    >>> biomarkerBodySystem.protocols = protocolRVs
    >>> biomarkerBodySystem.publications = pubRVs
    >>> notify(ObjectModifiedEvent(biomarkerBodySystem))

Did it work?

    >>> biomarkerBodySystem.qaState
    u'High'
    >>> biomarkerBodySystem.phase
    u'Laservision'
    >>> biomarkerBodySystem.performanceComment
    u'Oh yeah baby.'
    >>> linkedProtocols = [i.to_path for i in biomarkerBodySystem.protocols]
    >>> linkedProtocols.sort()
    >>> linkedProtocols
    ['/plone/protocols/279-lung-reference-set-a-application-edward', '/plone/protocols/316-hepatocellular-carcinoma-early-detection']
    >>> linkedPubs = [i.to_path for i in biomarkerBodySystem.publications]
    >>> linkedPubs.sort()
    >>> linkedPubs
    ['/plone/publications/15613711-evaluation-of-serum-protein-profiling-by', '/plone/publications/23585862-early-detection-of-nsclc-with-scfv', '/plone/publications/27845339-a-combination-of-muc5ac-and-ca19-9', '/plone/publications/28520829-association-between-combined-tmprss2-erg']

But it can have child objects too::

    >>> browser.open(portalURL + '/biomarkers/sticky-biomarker/colon')
    >>> l = browser.getLink(id='eke-knowledge-bodysystemstudy')
    >>> l.url.endswith('++add++eke.knowledge.bodysystemstudy')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.decisionRule').value = u'It rules all right.'
    >>> browser.getControl(name='form.widgets.title').value = u'Colon Study'
    >>> browser.getControl(name='form.widgets.description').value = u'A deep study of the colon.'
    >>> browser.getControl(name='form.widgets.identifier').value = u'urn:biomarker:sticky:colon:colon-study'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'colon-study' in biomarkerBodySystem.keys()
    True
    >>> bodySystemStudy = biomarkerBodySystem['colon-study']
    >>> myProtocolRV, otherProtocolRVs = protocolRVs[0], protocolRVs[1:]
    >>> bodySystemStudy.protocol = myProtocolRV
    >>> bodySystemStudy.protocols = otherProtocolRVs
    >>> bodySystemStudy.publications = pubRVs
    >>> notify(ObjectModifiedEvent(bodySystemStudy))

Working? Yes::

    >>> bodySystemStudy.decisionRule
    u'It rules all right.'
    >>> bodySystemStudy.title
    u'Colon Study'
    >>> bodySystemStudy.protocol.to_path
    '/plone/protocols/279-lung-reference-set-a-application-edward'
    >>> linkedProtocols = [i.to_path for i in bodySystemStudy.protocols]
    >>> linkedProtocols.sort()
    >>> linkedProtocols
    ['/plone/protocols/316-hepatocellular-carcinoma-early-detection']
    >>> linkedPubs = [i.to_path for i in bodySystemStudy.publications]
    >>> linkedPubs.sort()
    >>> linkedPubs
    ['/plone/publications/15613711-evaluation-of-serum-protein-profiling-by', '/plone/publications/23585862-early-detection-of-nsclc-with-scfv', '/plone/publications/27845339-a-combination-of-muc5ac-and-ca19-9', '/plone/publications/28520829-association-between-combined-tmprss2-erg']

Oh but we're not done::

    >>> browser.open(portalURL + '/biomarkers/sticky-biomarker/colon/colon-study')
    >>> l = browser.getLink(id='eke-knowledge-studystatistics')
    >>> l.url.endswith('++add++eke.knowledge.studystatistics')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Statistics for the Colon Study Part 1'
    >>> browser.getControl(name='form.widgets.description').value = u'See the title.'
    >>> browser.getControl(name='form.widgets.identifier').value = u'urn:biomarker:sticky:colon:colon-study:stat-1'
    >>> browser.getControl(name='form.widgets.sensitivity').value = u'12.3'
    >>> browser.getControl(name='form.widgets.specificity').value = u'3.45'
    >>> browser.getControl(name='form.widgets.npv').value = u'5.67'
    >>> browser.getControl(name='form.widgets.ppv').value = u'7.89'
    >>> browser.getControl(name='form.widgets.prevalence').value = u'0.95'
    >>> browser.getControl(name='form.widgets.details').value = u'Quite sticky results indeed.'
    >>> browser.getControl(name='form.widgets.specificAssayType').value = u'The sticky type.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'statistics-for-the-colon-study-part-1' in bodySystemStudy.keys()
    True
    >>> stats = bodySystemStudy['statistics-for-the-colon-study-part-1']
    >>> stats.title
    u'Statistics for the Colon Study Part 1'
    >>> stats.description
    u'See the title.'
    >>> stats.identifier
    u'urn:biomarker:sticky:colon:colon-study:stat-1'
    >>> stats.sensitivity
    u'12.3'
    >>> stats.specificity
    u'3.45'
    >>> stats.npv
    u'5.67'
    >>> stats.ppv
    u'7.89'
    >>> stats.prevalence
    u'0.95'
    >>> stats.details
    u'Quite sticky results indeed.'
    >>> stats.specificAssayType
    u'The sticky type.'

OK that's enough. RDF is the order of the day::

    >>> registry['eke.knowledge.interfaces.IPanel.objects'] = [u'biomarkers']
    >>> transaction.commit()
    >>> browser.open(portalURL + '/@@ingestRDF')
    >>> browser.contents
    '...RDF Ingest Report...Objects Created (2)...'
    >>> len(biomarkersFolder.keys())
    2
    >>> keys = biomarkersFolder.keys()
    >>> keys.sort()
    >>> keys
    ['apg1', 'panel-1']
    >>> a1 = biomarkersFolder['apg1']
    >>> a1.title
    u'Apogee 1'
    >>> a1.hgncName
    u'APG1'
    >>> a1.description
    u'A sticky bio-marker.'
    >>> a1.shortName
    u'A1'
    >>> u'Approach' in a1.bmAliases, u'Advent' in a1.bmAliases, u'Bigo' in a1.bmAliases
    (True, True, True)
    >>> a1.biomarkerType
    u'Colloidal'
    >>> a1.identifier
    u'http://edrn/bmdb/a1'
    >>> a1.publications[0].to_object.title
    u'Evaluation of serum protein profiling by surface-enhanced laser desorption/ionization time-of-flight mass spectrometry for the detection of prostate cancer: I. Assessment of platform reproducibility.'
    >>> a1.resources[0].to_object.title
    u'A web index'
    >>> a1.datasets[0].to_object.title
    u'GSTP1 Methylation'
    >>> a1.qaState
    u'Accepted'
    >>> o1 = a1['rectum']
    >>> o1.title
    u'Rectum'
    >>> o1.description
    u'Action on the rectum is amazing.'
    >>> o1.performanceComment
    u'The biomarker failed to perform as expected.'
    >>> o1.bodySystem.to_object.title
    u'Rectum'
    >>> o1.cliaCertification
    True
    >>> o1.fdaCertification
    False
    >>> o1.phase
    u'1'
    >>> o1.qaState
    u'Accepted'
    >>> o1.identifier
    u'http://edrn/bmdb/a1/o1'
    >>> o1.publications[0].to_object.title
    u'Evaluation of serum protein profiling by surface-enhanced laser desorption/ionization time-of-flight mass spectrometry for the detection of prostate cancer: I. Assessment of platform reproducibility.'
    >>> o1.keys()
    ['lung-reference-set-a-application-edward-hirschowitz-university-of-kentucky-2009']
    >>> s1 = o1['lung-reference-set-a-application-edward-hirschowitz-university-of-kentucky-2009']
    >>> s1.protocol.to_object.title
    u'Lung Reference Set A Application:  Edward Hirschowitz - University of Kentucky (2009)'
    >>> s1.decisionRule
    u'A sample decision rule'
    >>> s1.phase
    u'1'
    >>> for i in s1.objectIds():
    ...     stats = s1[i]
    ...     stats.sensitivity in (u'1.0', u'6.0')
    ...     True
    ...     stats.specificity in (u'2.0', u'7.0')
    ...     True
    ...     stats.npv in (u'4.0', u'9.0')
    ...     True
    ...     stats.ppv in (u'5.0', u'10.0')
    ...     True
    ...     stats.prevalence in (u'3.0', u'8.0')
    ...     True
    ...     stats.details in ('The first one', 'The second two')
    ...     True
    ...     stats.specificAssayType == 'Sample specific assay type details'
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    True
    >>> panel = biomarkersFolder['panel-1']
    >>> panel.title
    u'Panel 1'
    >>> panel.shortName
    u'P1'
    >>> panel.identifier
    u'http://edrn/bmdb/p1'
    >>> panel.description
    u'A very sticky panel.'
    >>> panel.members[0].to_object.title
    u'Apogee 1'

Ingesting also links protocols to biomarkers::

    >>> browser.open(portalURL + '/protocols/279-lung-reference-set-a-application-edward')
    >>> browser.contents
    '...Biomarkers:...Apogee 1...'


.. These will come later
    .. >>> a1.geneName
    .. u'APG1'
    .. >>> a1.uniProtAC
    .. u'P18847'
    .. >>> a1.mutCount
    .. u'12'
    .. >>> a1.pmidCount
    .. u'8'
    .. >>> a1.cancerDOCount
    .. u'11'
    .. >>> a1.affProtFuncSiteCount
    .. '0'

