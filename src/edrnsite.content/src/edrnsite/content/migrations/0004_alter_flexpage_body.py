# Generated by Django 4.1.4 on 2023-01-03 22:10

from django.db import migrations
import edrnsite.streams.blocks
import wagtail.blocks
import wagtail.contrib.typed_table_block.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('edrnsitecontent', '0003_alter_flexpage_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flexpage',
            name='body',
            field=wagtail.fields.StreamField([('rich_text', wagtail.blocks.RichTextBlock(help_text='Richly formatted text', icon='doc-full', label='Rich Text')), ('cards', wagtail.blocks.StructBlock([('cards', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(help_text='Title of this card, max 100 chars', max_length=100))])))])), ('table', edrnsite.streams.blocks.TableBlock()), ('block_quote', edrnsite.streams.blocks.BlockQuoteBlock(help_text='Block quote')), ('typed_table', wagtail.contrib.typed_table_block.blocks.TypedTableBlock([('text', wagtail.blocks.CharBlock(help_text='Plain text cell')), ('rich_text', wagtail.blocks.RichTextBlock(help_text='Rich text cell')), ('numeric', wagtail.blocks.FloatBlock(help_text='Numeric cell')), ('integer', wagtail.blocks.IntegerBlock(help_text='Integer cell')), ('page', wagtail.blocks.PageChooserBlock(help_text='Page within the site'))])), ('carousel', wagtail.blocks.StructBlock([('media', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock()), ('label', wagtail.blocks.CharBlock(help_text='Overlaid label, if any', max_length=120, required=False)), ('caption', wagtail.blocks.CharBlock(help_text='Overlaid caption, if any', max_length=400, required=False))])))])), ('raw_html', wagtail.blocks.RawHTMLBlock(help_text='Raw HTML (use with care)'))], blank=True, null=True, use_json_field=True),
        ),
    ]
