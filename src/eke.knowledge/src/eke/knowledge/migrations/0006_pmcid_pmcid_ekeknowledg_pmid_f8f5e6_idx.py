# Generated by Django 4.1.7 on 2023-03-24 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ekeknowledge', '0005_datacollectionindex_metadata_collection_form'),
    ]

    operations = [
        migrations.CreateModel(
            name='PMCID',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pmid', models.CharField(blank=True, help_text='Entrez Medline PMID code number', max_length=20)),
                ('pmcid', models.CharField(blank=True, help_text='Entrez Medline PMCID code number', max_length=20)),
            ],
        ),
        migrations.AddIndex(
            model_name='pmcid',
            index=models.Index(fields=['pmid'], name='ekeknowledg_pmid_f8f5e6_idx'),
        ),
    ]