# Generated by Django 4.2.9 on 2024-01-29 22:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ekeknowledge", "0016_protocol_publications"),
    ]

    operations = [
        migrations.AddField(
            model_name="protocol",
            name="estimated_finish_date",
            field=models.TextField(
                blank=True, help_text="A guess as to when this protocol will end"
            ),
        ),
        migrations.AddField(
            model_name="protocol",
            name="start_date",
            field=models.TextField(blank=True, help_text="When this protocol began"),
        ),
    ]