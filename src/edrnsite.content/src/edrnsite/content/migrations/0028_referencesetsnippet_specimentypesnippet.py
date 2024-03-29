# Generated by Django 4.1.9 on 2023-08-15 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0027_cdeexplorerattribute_inheritance'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReferenceSetSnippet',
            fields=[
                ('reference_set_code', models.CharField(help_text='Reference set ID code', max_length=32, primary_key=True, serialize=False, unique=True)),
                ('label', models.CharField(default='label', help_text='Name of reference set', max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='SpecimenTypeSnippet',
            fields=[
                ('specimen_type_code', models.CharField(help_text='Specimen type ID code', max_length=32, primary_key=True, serialize=False, unique=True)),
                ('label', models.CharField(default='label', help_text='Kind of specimen', max_length=80)),
            ],
        ),
    ]
