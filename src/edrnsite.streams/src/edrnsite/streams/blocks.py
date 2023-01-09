# encoding: utf-8

'''🦦 EDRN Site streams: blocks.'''


from django.forms.utils import ErrorList
from django.utils.html import format_html
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.table_block.blocks import TableBlock as BaseTableBlock
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock as BaseTypedTableBlock
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock


class TitleBlock(blocks.StructBlock):
    '''A large title.'''
    text = blocks.CharBlock(max_length=100, required=True, help_text='Title to display')
    class Meta:
        template = 'edrnsite.streams/title-block.html'
        icon = 'title'
        label = 'Title'
        help_text = 'Large title text to display on the page'


class CaptionedImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    label = blocks.CharBlock(max_length=120, required=False, help_text='Overlaid label, if any')
    caption = blocks.CharBlock(max_length=400, required=False, help_text='Overlaid caption, if any')
    class Meta:
        icon = 'placeholder'
        label = 'Captioned Image'
        help_text = 'An image with both a shorter label and a longer caption'


class CarouselBlock(blocks.StructBlock):
    media = blocks.ListBlock(CaptionedImageBlock())
    class Meta:
        template = 'edrnsite.streams/carousel-block.html'
        icon = 'image'
        title = 'Carousel'
        help_text = 'A series of one or more images in rotating display'


class Link(blocks.StructBlock):
    '''A hyperlink to a page in the site or to an external resource.'''
    link_text = blocks.CharBlock(max_length=120, required=False, help_text="Label for the link; don't use ‘here’")
    internal_page = blocks.PageChooserBlock(required=False, help_text='Page in the site to link to')
    external_link = blocks.URLBlock(required=False, help_text='External URL to link to')
    view_name = blocks.CharBlock(max_length=32, required=False, help_text='Name of a view to link to')

    def clean(self, value: blocks.StructValue) -> blocks.StructValue:
        link_text = value.get('link_text')
        internal_page = value.get('internal_page')
        external_link = value.get('external_link')
        view_name = value.get('view_name')
        errors = {}
        if link_text.lower() in ('here', 'click here', 'tap here'):
            errors['link_text'] = ErrorList(["Don't make your hyperlink be ‘here’; use something descriptive."])

        the_sum = int(bool(internal_page)) + int(bool(external_link)) + int(bool(view_name))
        if the_sum > 1:
            error_message = 'Only one of these fields can be filled.'
            errors['internal_page'] = ErrorList([error_message])
            errors['external_link'] = ErrorList([error_message])
            errors['view_name'] = ErrorList([error_message])
        elif the_sum == 0:
            error_message = 'Exactly one of these fields must be filled.'
            errors['internal_page'] = ErrorList([error_message])
            errors['external_link'] = ErrorList([error_message])
            errors['view_name'] = ErrorList([error_message])
        if errors:
            raise StructBlockValidationError(block_errors=errors)

        return super().clean(value)

    class Meta:
        template = 'edrnsite.streams/link.html'
        icon = 'link'
        title = 'Link'
        help_text = 'A hyperlink that may be internal to the site or to an external resource'


class SiteSectionCard(blocks.StructBlock):
    _features = ['bold', 'italic', 'hr', 'link', 'document-link']
    _styles = ['aqua', 'cerulean', 'teal', 'cyan', 'navy']
    title = blocks.CharBlock(max_length=200, required=True, help_text='Title of this Site Section Card')
    style = blocks.ChoiceBlock(
        choices=[(i, i.capitalize()) for i in _styles], required=False, help_text='Background style for this card'
    )
    image = ImageChooserBlock(required=False, help_text='Little picture to show in the corner of the card')
    page = blocks.PageChooserBlock(required=False, help_text='Site page to which this card links, optional')
    description = blocks.RichTextBlock(required=False, help_text='Short introductory text', features=_features)
    links = blocks.ListBlock(Link())
    class Meta:
        template = 'edrnsite.streams/site-section-card.html'
        icon = 'clipboard-list'
        label = 'Site Section Card'
        help_text = 'A single card depicting all there is to know about a single major section of the web site'


class SiteSectionCardsBlock(blocks.StructBlock):
    cards = blocks.ListBlock(SiteSectionCard())
    class Meta:
        template = 'edrnsite.streams/site-section-cards-block.html'
        icon = 'duplicate'
        label = 'Site Section Cards Block'
        help_text = 'A block of cards each of which describe a major section of the web site'


class Card(blocks.StructBlock):
    '''An EDRN style "card".'''
    title = blocks.CharBlock(max_length=100, help_text='Title of this card, max 100 chars')


class CardsBlock(blocks.StructBlock):
    '''A block of "cards".'''
    cards = blocks.ListBlock(Card())
    class Meta(object):
        template = 'edrnsite.streams/cards-block.html'
        icon = 'placeholder'
        label = 'EDRN Style Cards'


class TableBlock(BaseTableBlock):
    '''A basic table to appear in the EDRN site.'''
    class Meta(object):
        template = 'edrnsite.streams/table-block.html'
        icon = 'table'
        label = 'Basic (Plain Text) Table'


class TypedTableBlock(BaseTypedTableBlock):
    '''A more advanced table to appear in the EDRN site.'''
    class Meta(object):
        template = 'edrnsite.streams/typed-table-block.html'
        icon = 'table'
        label = 'Advanced Table'


class BlockQuoteBlock(blocks.BlockQuoteBlock):
    '''Override Wagtail's own BlockQuoteBlock so we can use Bootstrap styling.'''
    def render_basic(self, value, context=None):
        if value:
            return format_html('<blockquote class="blockquote">{0}</blockquote>', value)
        else:
            return ''


TYPED_TABLE_BLOCK = TypedTableBlock([
    ('text', blocks.CharBlock(help_text='Plain text cell')),
    ('rich_text', blocks.RichTextBlock(help_text='Rich text cell')),
    ('numeric', blocks.FloatBlock(help_text='Numeric cell')),
    ('integer', blocks.IntegerBlock(help_text='Integer cell')),
    ('page', blocks.PageChooserBlock(help_text='Page within the site')),
])


# 🔮 Postpone this for now
#
# class HeroBlock(blocks.StructBlock):
#     '''A "hero unit", or large section of highlighted content.'''
#     _features = ['bold', 'italic', 'hr', 'link', 'document-link']
#     _styles = ['left-light', 'right-light', 'left-dark', 'right-dark']
#
#     title = blocks.CharBlock(max_length=250, required=True, help_text='Heroic Headline')
#     image = ImageChooserBlock(required=True, help_text='Large picture to show on the hero unit')
#     description = blocks.RichTextBlock(required=False, help_text='Summary of this hero unit', features=_features)
#     style = blocks.ChoiceBlock(
#         choices=[(i, i.capitalize()) for i in _styles], required=False, help_text='Style for this hero unit'
#     )
#     links = blocks.ListBlock(Link())
#     class Meta:
#         template = 'edrnsite.streams/hero-block.html'
#         icon = 'user'
#         label = 'Hero Unit'
#         help_text = 'An eye-catching display of a headline, imagery, optional text, and buttoned-links'
