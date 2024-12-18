# Generated by Django 4.2.14 on 2024-08-21 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("edrnsitecontrols", "0009_informatics_override_version"),
    ]

    operations = [
        migrations.AlterField(
            model_name="informatics",
            name="override_version",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Version number to override in footer; blank determines from software",
            ),
        ),
    ]