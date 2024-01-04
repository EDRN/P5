# Generated by Django 4.2.7 on 2024-01-04 19:42

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):
    dependencies = [
        ("ekeknowledge", "0015_memberfinderpage"),
    ]

    operations = [
        migrations.AddField(
            model_name="protocol",
            name="publications",
            field=modelcluster.fields.ParentalManyToManyField(
                blank=True,
                related_name="protocols",
                to="ekeknowledge.publication",
                verbose_name="Publications",
            ),
        ),
    ]
