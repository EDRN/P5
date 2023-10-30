# Generated by Django 4.1.9 on 2023-10-12 20:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0025_alter_image_file_alter_rendition_file'),
        ('ekeknowledge', '0012_datacollectionindex_preamble'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='photo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_photograph', to='wagtailimages.image'),
        ),
    ]