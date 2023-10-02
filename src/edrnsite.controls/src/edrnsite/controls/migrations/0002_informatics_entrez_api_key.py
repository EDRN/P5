# Generated by Django 4.1.9 on 2023-08-10 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontrols', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='informatics',
            name='entrez_api_key',
            field=models.CharField(blank=True, default='', help_text='Optional Entrez API key', max_length=64),
        ),
    ]