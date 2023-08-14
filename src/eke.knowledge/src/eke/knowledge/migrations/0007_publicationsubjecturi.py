# Generated by Django 4.1.9 on 2023-08-03 15:40

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ekeknowledge', '0006_pmcid_pmcid_ekeknowledg_pmid_f8f5e6_idx'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicationSubjectURI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('identifier', models.CharField(help_text='RDF subject URI that uniquely identifies this object', max_length=2000, unique=True, verbose_name='Subject URI')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject_uris', to='ekeknowledge.publication')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]
