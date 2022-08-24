# encoding: utf-8

'''🦦 EDRN Site streams: blocks.'''


from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
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
    internal_page = blocks.PageChooserBlock(required=False)
    external_link = blocks.URLBlock(required=False)

    def clean(self, value: blocks.StructValue) -> blocks.StructValue:
        link_text = value.get('link_text')
        internal_page = value.get('internal_page')
        external_link = value.get('external_link')
        errors = {}
        if link_text.lower() in ('here', 'click here', 'tap here'):
            errors['link_text'] = ErrorList(["Don't make your hyperlink be ‘here’; use something descriptive."])
        if internal_page and external_link:
            errors['internal_page'] = ErrorList(['Both of these fields cannot be filled. Please select or enter only one option.'])
            errors['external_link'] = ErrorList(['Both of these fields cannot be filled. Please select or enter only one option.'])
        elif not internal_page and not external_link:
            errors['internal_page'] = ErrorList(['Please select a page or enter a URL for one of these options.'])
            errors['external_link'] = ErrorList(['Please select a page or enter a URL for one of these options.'])
        if errors:
            raise ValidationError('Validation error in your Link', params=errors)
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
