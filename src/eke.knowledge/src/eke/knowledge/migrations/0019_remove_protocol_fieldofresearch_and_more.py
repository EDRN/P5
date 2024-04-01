# Generated by Django 4.2.10 on 2024-03-27 19:50

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):
    dependencies = [
        ("ekeknowledge", "0018_protocol_outcome_protocol_secure_outcome"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="protocol",
            name="fieldOfResearch",
        ),
        migrations.CreateModel(
            name="ProtocolFieldOfResearch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "value",
                    models.CharField(
                        default="Field of research",
                        help_text="Field of research",
                        max_length=25,
                    ),
                ),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fields_of_research",
                        to="ekeknowledge.protocol",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
    ]
