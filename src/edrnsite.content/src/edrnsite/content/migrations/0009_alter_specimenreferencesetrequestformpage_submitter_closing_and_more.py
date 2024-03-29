# Generated by Django 4.1.7 on 2023-04-20 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0008_specimenreferencesetrequestformpage_submitter_closing_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specimenreferencesetrequestformpage',
            name='submitter_closing',
            field=models.TextField(default='For your reference, a copy of your proposal is attached. If you have any questions or concerns, please reach out to the DMCC by email to edrndmcc@fredhutch.org.', help_text='Closing to the message body for the copy of the form data sent to the submitter of the request'),
        ),
        migrations.AlterField(
            model_name='specimenreferencesetrequestformpage',
            name='submitter_preamble',
            field=models.TextField(default='Thank you for your specimen reference set request. This email can serve as a receipt for your request should you need to refer back to it in the future. It is also a reminder of the affirmations you made as part of the request. For your information, here are the answers you supplied in the form:', help_text='Preamble to the message body for the copy of the form data sent to the submitter of the request'),
        ),
    ]
