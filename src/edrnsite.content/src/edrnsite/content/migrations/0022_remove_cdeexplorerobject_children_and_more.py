# Generated by Django 4.1.9 on 2023-07-19 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0021_alter_cdeexplorerobject_page'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cdeexplorerobject',
            name='children',
        ),
        migrations.AddField(
            model_name='cdeexplorerobject',
            name='children',
            field=models.ManyToManyField(blank=True, null=True, related_name='parent', to='edrnsitecontent.cdeexplorerobject'),
        ),
    ]