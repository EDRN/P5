# Generated by Django 4.1.9 on 2023-05-31 13:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0012_uploadeddocument'),
        ('wagtailcore', '0083_workflowcontenttype'),
        ('edrnsitecontent', '0011_postmanapipage_taxonomypage'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TaxonomyPage',
            new_name='SantiagoTaxonomyPage',
        ),
    ]
