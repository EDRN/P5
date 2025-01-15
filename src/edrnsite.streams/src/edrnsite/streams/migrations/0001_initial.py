# Generated by Django 4.2.17 on 2025-01-10 22:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DataElementExplorerObject",
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
                    "name",
                    models.CharField(
                        help_text="Name of this object in a CDE hierarchy",
                        max_length=200,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="A nice long description of this object"
                    ),
                ),
                (
                    "stewardship",
                    models.TextField(
                        blank=True, help_text="Who's responsible for this object"
                    ),
                ),
                (
                    "spreadsheet_id",
                    models.CharField(
                        blank=True,
                        help_text="If a root node, the spreadsheet that generates this node",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="edrnsitestreams.dataelementexplorerobject",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DataElementExplorerAttribute",
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
                    "text",
                    models.CharField(
                        help_text="Name of this common data element", max_length=100
                    ),
                ),
                (
                    "definition",
                    models.TextField(
                        blank=True, help_text="A thorough definition of this CDE"
                    ),
                ),
                (
                    "required",
                    models.CharField(
                        blank=True,
                        help_text="Required, not, or something else?",
                        max_length=50,
                    ),
                ),
                (
                    "data_type",
                    models.CharField(
                        blank=True, help_text="Kind of data", max_length=30
                    ),
                ),
                (
                    "explanatory_note",
                    models.TextField(
                        blank=True, help_text="Note helping explain use of the CDE"
                    ),
                ),
                (
                    "inheritance",
                    models.BooleanField(
                        default=False, help_text="Attribute inherits values"
                    ),
                ),
                (
                    "obj",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributes",
                        to="edrnsitestreams.dataelementexplorerobject",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CDEPermissibleValue",
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
                    "value",
                    models.CharField(
                        help_text="An enumerated value allowed for a data element that uses permissible values",
                        max_length=200,
                    ),
                ),
                (
                    "attribute",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permissible_values",
                        to="edrnsitestreams.dataelementexplorerattribute",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="dataelementexplorerobject",
            index=models.Index(
                fields=["spreadsheet_id"], name="edrnsitestr_spreads_e6c691_idx"
            ),
        ),
    ]
