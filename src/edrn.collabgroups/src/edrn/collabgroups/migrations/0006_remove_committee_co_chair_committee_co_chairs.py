# Generated by Django 4.2.14 on 2024-09-10 18:17

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ("ekeknowledge", "0019_remove_protocol_fieldofresearch_and_more"),
        ("edrncollabgroups", "0005_committee_documents_heading"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="committee",
            name="co_chair",
        ),
        migrations.AddField(
            model_name="committee",
            name="co_chairs",
            field=modelcluster.fields.ParentalManyToManyField(
                blank=True,
                related_name="committees_I_co_chair",
                to="ekeknowledge.person",
                verbose_name="Co-Chair(s)",
            ),
        ),
    ]
