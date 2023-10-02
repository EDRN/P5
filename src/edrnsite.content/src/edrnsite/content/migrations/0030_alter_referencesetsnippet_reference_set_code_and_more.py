# Generated by Django 4.1.9 on 2023-08-15 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0029_alter_referencesetsnippet_reference_set_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='referencesetsnippet',
            name='reference_set_code',
            field=models.CharField(default='code', help_text='Reference set ID code', max_length=80, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='specimentypesnippet',
            name='specimen_type_code',
            field=models.CharField(default='code', help_text='Specimen type ID code', max_length=80, primary_key=True, serialize=False, unique=True),
        ),
    ]