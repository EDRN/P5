# Generated by Django 4.1.9 on 2023-07-20 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0023_remove_cdeexplorerobject_children_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cdeexplorerpage',
            name='spreadsheet_url',
            field=models.URLField(blank=True, help_text='Optional URL to a Google Drive spreadsheet'),
        ),
    ]
