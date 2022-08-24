# Generated by Django 4.0.6 on 2022-08-22 21:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0069_log_entry_jsonfield'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvestigatorAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(default='742 EVERGREEN TERRACE, SPRINGFIELD, OR, 97057, UNITED STATES', help_text='Full street address', max_length=512, unique=True)),
                ('lat', models.FloatField(default=0.0, help_text='Latitude')),
                ('lon', models.FloatField(default=0.0, help_text='Longitude')),
            ],
        ),
        migrations.CreateModel(
            name='Geocoding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_key', models.CharField(default='key', help_text='AWS Access Key', max_length=192)),
                ('secret_key', models.CharField(default='key', help_text='AWS Secret Access Key', max_length=192)),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'verbose_name': 'Geocoding',
            },
        ),
    ]
