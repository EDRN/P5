# Generated by Django 4.1.1 on 2022-09-14 14:27

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.fields
import wagtailmetadata.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0076_modellogentry_revision'),
        ('wagtailimages', '0024_index_image_file_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('value', models.CharField(default='Name', help_text='Author name', max_length=255)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('value', models.CharField(default='Data category', help_text='Category', max_length=256)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('value', models.CharField(default='Discipline', help_text='Branch of knowledge or study', max_length=256)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GrantNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('value', models.CharField(help_text='Grant Number', max_length=20)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KnowledgeFolder',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('ingest', models.BooleanField(default=True, help_text='Enable or disable ingest for this folder')),
                ('ingest_order', models.IntegerField(default=0, help_text='Relative ordering of ingest')),
                ('search_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image', verbose_name='Search image')),
            ],
            options={
                'ordering': ['ingest_order'],
            },
            bases=(wagtailmetadata.models.WagtailImageMetadataMixin, 'wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='KnowledgeObject',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('identifier', models.CharField(help_text='RDF subject URI that uniquely identifies this object', max_length=2000, unique=True, verbose_name='subject URI')),
                ('description', models.TextField(blank=True, help_text='A summary or descriptive abstract')),
                ('search_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image', verbose_name='Search image')),
            ],
            bases=(wagtailmetadata.models.WagtailImageMetadataMixin, 'wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='Organ',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('value', models.CharField(default='Name', help_text='Name of the organ', max_length=255)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PrincipalOwner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('value', models.CharField(default='Owner', help_text='DN of principal', max_length=512)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BodySystem',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='BodySystemIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='DataCollection',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('investigator_name', models.CharField(blank=True, help_text='Name of PI', max_length=80)),
                ('collaborative_group', models.CharField(blank=True, help_text='Collaborative group', max_length=80)),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='DataCollectionIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='DataStatistic',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('cardinality', models.PositiveIntegerField(default=0, help_text='Count of items')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='Disease',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('icd9Code', models.CharField(blank=True, help_text='International Statistical Classifiction of Disease Code (version 9)', max_length=10, verbose_name='ICD9')),
                ('icd10Code', models.CharField(blank=True, help_text='International Statistical Classifiction of Disease Code (version 10)', max_length=20, verbose_name='ICD10')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='DiseaseIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='MiscellaneousResource',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='MiscellaneousResourceIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('edrnTitle', models.CharField(blank=True, help_text='Title bestowed from on high', max_length=40)),
                ('mbox', models.EmailField(blank=True, help_text='Email address', max_length=254)),
                ('fax', models.CharField(blank=True, help_text='Who seriously uses fax?', max_length=40)),
                ('account_name', models.CharField(blank=True, help_text='DMCC-assigned login identifier', max_length=32)),
                ('personID', models.CharField(blank=True, help_text='Code assigned by DMCC', max_length=10)),
                ('address', models.CharField(blank=True, help_text='Mailing street address', max_length=250)),
                ('city', models.CharField(blank=True, help_text='Mailing city', max_length=60)),
                ('state', models.CharField(blank=True, help_text='Mailing state or province', max_length=60)),
                ('postal_code', models.CharField(blank=True, help_text='Mailing postal code', max_length=20)),
                ('country', models.CharField(blank=True, help_text='Mailing country', max_length=35)),
                ('lat', models.FloatField(blank=True, help_text='Latitude', null=True)),
                ('lon', models.FloatField(blank=True, help_text='Longitude', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='Protocol',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('piName', models.CharField(blank=True, help_text='De-normalized PI name from lead site', max_length=200)),
                ('isProject', models.BooleanField(default=False, help_text='True if this is a project, not a protcol')),
                ('protocolID', models.IntegerField(blank=True, help_text='Number assigned by the DMCC but could be blank for non-EDRN protocols', null=True)),
                ('abbreviation', models.CharField(blank=True, help_text='Short and more convenient name for the protocol', max_length=120)),
                ('fieldOfResearch', models.CharField(blank=True, help_text='Field this protocol studies', max_length=25)),
                ('phasedStatus', models.PositiveIntegerField(blank=True, help_text='Not sure what this is', null=True)),
                ('aims', models.TextField(blank=True, help_text='The long term goals of this protocol')),
                ('analyticMethod', models.TextField(blank=True, help_text='How things in this protocol are analyzed')),
                ('comments', models.TextField(blank=True, help_text='Your feedback on this protocol is appreciated!')),
                ('finish_date', models.TextField(blank=True, help_text='When this protocol ceased')),
                ('collaborativeGroup', models.CharField(blank=True, help_text='Collaborative Group', max_length=400)),
            ],
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='ProtocolIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('issue', models.CharField(blank=True, help_text='In what issue publication appeared', max_length=50)),
                ('volume', models.CharField(blank=True, help_text='In what volume publication appeared', max_length=50)),
                ('journal', models.CharField(blank=True, help_text='Name of the periodical', max_length=250)),
                ('pubMedID', models.CharField(blank=True, help_text='Entrez Medline ID code number', max_length=20)),
                ('year', models.IntegerField(blank=True, help_text='Year of publication', null=True)),
                ('pubURL', models.URLField(blank=True, help_text='URL to read the publication')),
                ('siteID', models.CharField(blank=True, help_text='RDF subject URI of site that wrote the publication', max_length=2000)),
                ('abstract', wagtail.fields.RichTextField(blank=True, help_text='A summary of the contents of this publication', verbose_name='abstract')),
            ],
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='PublicationIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('knowledgeobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgeobject')),
                ('abbreviation', models.CharField(blank=True, help_text='A short name for the site', max_length=40)),
                ('fundingStartDate', models.CharField(blank=True, help_text='When money was first given', max_length=25)),
                ('fundingEndDate', models.CharField(blank=True, help_text='When the money stopped flowing', max_length=25)),
                ('dmccSiteID', models.CharField(blank=True, help_text='DMCC-assigned number of the site', max_length=10)),
                ('memberType', models.CharField(blank=True, help_text='Kind of member site', max_length=80)),
                ('homePage', models.URLField(blank=True, help_text="Uniform Resource Locator of site's home page")),
                ('specialty', wagtail.fields.RichTextField(blank=True, help_text="What the site's really good at")),
                ('proposal', models.CharField(blank=True, help_text='BDL-only proposal title that produced this site', max_length=250)),
                ('coIs', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='site_i_co_investigate', to='ekeknowledge.person', verbose_name='Co-Investigators')),
                ('coPIs', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='site_i_co_lead', to='ekeknowledge.person', verbose_name='Co-Prinicipal Investigators')),
                ('investigators', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='site_i_investigate', to='ekeknowledge.person', verbose_name='Investigators')),
                ('pi', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_i_lead', to='ekeknowledge.person', verbose_name='Principal Investigator')),
                ('sponsor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sponsored_site', to='ekeknowledge.site', verbose_name='Sponsoring Site')),
            ],
            bases=('ekeknowledge.knowledgeobject',),
        ),
        migrations.CreateModel(
            name='SiteIndex',
            fields=[
                ('knowledgefolder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.knowledgefolder')),
            ],
            bases=('ekeknowledge.knowledgefolder',),
        ),
        migrations.CreateModel(
            name='RDFSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('name', models.CharField(default='Some RDF Source', max_length=255)),
                ('url', models.URLField(default='https://some.source/rdf', max_length=2000)),
                ('active', models.BooleanField(default=True, help_text='Toggle whether to use this source')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='rdf_sources', to='ekeknowledge.knowledgefolder')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RDFIngest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='Global enable/disable RDF ingest')),
                ('timeout', models.PositiveIntegerField(default=120, help_text='Max time limit for ingest in minutes; 0 disables timeout')),
                ('edrn_protocol_limit', models.IntegerField(default=1000, help_text='Protocol IDs over this number are considered non-EDRN')),
                ('last_ingest_start', models.DateTimeField(blank=True, help_text='When the last ingest started', null=True)),
                ('last_ingest_duration', models.IntegerField(blank=True, help_text='How long (seconds) last ingest took', null=True)),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'verbose_name': 'RDF Ingest',
            },
        ),
        migrations.CreateModel(
            name='SiteOrgan',
            fields=[
                ('organ_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='ekeknowledge.organ')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='organs', to='ekeknowledge.site')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=('ekeknowledge.organ',),
        ),
        migrations.AddIndex(
            model_name='publication',
            index=models.Index(fields=['pubMedID'], name='ekeknowledg_pubMedI_0d2474_idx'),
        ),
        migrations.AddIndex(
            model_name='publication',
            index=models.Index(fields=['year'], name='ekeknowledg_year_124173_idx'),
        ),
        migrations.AddField(
            model_name='protocol',
            name='cancer_types',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='protocols_analyzing', to='ekeknowledge.disease', verbose_name='Cancers Studied'),
        ),
        migrations.AddField(
            model_name='protocol',
            name='coordinatingInvestigatorSite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coordinated_protocols', to='ekeknowledge.site', verbose_name='Coordinating Investigator Site'),
        ),
        migrations.AddField(
            model_name='protocol',
            name='involvedInvestigatorSites',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='involving_protocols', to='ekeknowledge.site', verbose_name='Involved Investigator Sites'),
        ),
        migrations.AddField(
            model_name='protocol',
            name='leadInvestigatorSite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leading_protocols', to='ekeknowledge.site', verbose_name='Lead Investigator Site'),
        ),
        migrations.AddField(
            model_name='principalowner',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner_principals', to='ekeknowledge.datacollection'),
        ),
        migrations.AddField(
            model_name='person',
            name='photo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='person_photograph', to='wagtailimages.image'),
        ),
        migrations.AddField(
            model_name='grantnumber',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='grant_numbers', to='ekeknowledge.publicationindex'),
        ),
        migrations.AddField(
            model_name='disease',
            name='affectedOrgans',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='diseases', to='ekeknowledge.bodysystem', verbose_name='Affected Organs'),
        ),
        migrations.AddField(
            model_name='discipline',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_collection_disciplines', to='ekeknowledge.datacollection'),
        ),
        migrations.AddField(
            model_name='datacollection',
            name='associated_organs',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, related_name='organs_in_data', to='ekeknowledge.bodysystem', verbose_name='Associated Organs'),
        ),
        migrations.AddField(
            model_name='datacollection',
            name='generating_protocol',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_data_collections', to='ekeknowledge.protocol', verbose_name='Protocol that produced this data'),
        ),
        migrations.AddField(
            model_name='datacategory',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_collection_categories', to='ekeknowledge.datacollection'),
        ),
        migrations.AddField(
            model_name='author',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='authors', to='ekeknowledge.publication'),
        ),
    ]
