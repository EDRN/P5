# Generated by Django 4.1.5 on 2023-01-10 16:42

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ekebiomarkers', '0001_initial'),
        ('wagtailcore', '0078_referenceindex'),
        ('ekeknowledge', '0002_committeeindex'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportIndex',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='DataQualityReport',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('biomarkerless_data', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='dqr_biomarkerless', to='ekeknowledge.datacollection', verbose_name='Data collections without biomarkers')),
                ('dataless_biomarkers', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='dqr_dataless', to='ekebiomarkers.biomarker', verbose_name='Biomarkers without science data')),
                ('piless_data', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='dqr_piless', to='ekeknowledge.datacollection', verbose_name='Data collections without PIs')),
                ('piless_pubs', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='dqr_pubs', to='ekeknowledge.publication', verbose_name='Publications without PIs')),
                ('publess_biomarkers', modelcluster.fields.ParentalManyToManyField(blank=True, related_name='dqr_publess', to='ekebiomarkers.biomarker', verbose_name='Biomarkers without publications')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
