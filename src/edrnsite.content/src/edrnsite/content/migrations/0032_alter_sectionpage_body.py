# Generated by Django 4.1.9 on 2023-10-02 18:23

from django.db import migrations
import wagtail.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0031_cdeexplorerobject_stewardship'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sectionpage',
            name='body',
            field=wagtail.fields.StreamField([('title', wagtail.blocks.StructBlock([('text', wagtail.blocks.CharBlock(help_text='Title to display', max_length=100, required=True))])), ('section_cards', wagtail.blocks.StructBlock([('cards', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(help_text='Title of this Site Section Card', max_length=200, required=True)), ('style', wagtail.blocks.ChoiceBlock(choices=[('aqua', 'Aqua'), ('cerulean', 'Cerulean'), ('teal', 'Teal'), ('cyan', 'Cyan'), ('navy', 'Navy')], help_text='Background style for this card', required=False)), ('image', wagtail.images.blocks.ImageChooserBlock(help_text='Little picture to show in the corner of the card', required=False)), ('page', wagtail.blocks.PageChooserBlock(help_text='Site page to which this card links, optional', required=False)), ('description', wagtail.blocks.RichTextBlock(features=['bold', 'italic', 'hr', 'link', 'document-link'], help_text='Short introductory text', required=False)), ('links', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('link_text', wagtail.blocks.CharBlock(help_text="Label for the link; don't use ‘here’", max_length=120, required=False)), ('internal_page', wagtail.blocks.PageChooserBlock(help_text='Page in the site to link to', required=False)), ('external_link', wagtail.blocks.URLBlock(help_text='External URL to link to', required=False)), ('view_name', wagtail.blocks.CharBlock(help_text='Name of a view to link to', max_length=32, required=False))])))])))])), ('raw_html', wagtail.blocks.RawHTMLBlock(help_text='Raw HTML (use with care)')), ('rich_text', wagtail.blocks.RichTextBlock(help_text='Richly formatted text', icon='doc-full', label='Rich Text'))], blank=True, null=True, use_json_field=True),
        ),
    ]