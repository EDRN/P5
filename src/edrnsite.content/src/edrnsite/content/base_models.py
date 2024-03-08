# encoding: utf-8

'''😌 EDRN site content's models.'''


from django import forms
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm
from wagtail.fields import RichTextField
from wagtail.models import Page


class AbstractFormPage(Page):
    '''Abstract base class for Wagtail pages holding Django forms.'''
    intro = RichTextField(blank=True, help_text='Introductory text to appear above the form')
    outro = RichTextField(blank=True, help_text='Text to appear below the form')
    preview_modes = []
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('outro')
    ]

    def get_form(self) -> type:
        '''Return the class of the form this page will display.'''
        raise NotImplementedError('Subclasses must implement get_form')

    def get_encoding_type(self) -> str:
        cls = self.get_form()
        return cls.get_encoding_type()

    def get_initial_values(self, request: HttpRequest) -> dict:
        '''Return any initial values for the form. By default this is an empty dict.
        Subclasses may override this.'''
        return dict()

    def process_submission(self, form: forms.Form) -> dict:
        '''Process the submitted and cleaned ``form``.

        Return a dict of any other parameters that may be needed in the thank you page.
        '''
        raise NotImplementedError('Subclasses must implement process_submission')

    def get_landing_page(self) -> str:
        '''Get the name of the landing (thank you) page for successful submission.'''
        raise NotImplementedError('Subclasses must implement get_landing_page')

    def _bootstrap(self, form: forms.Form):
        '''Add Boostrap class to every widget except checkboxes & radio buttons.'''
        for field in form.fields.values():
            if not isinstance(
                field.widget, (
                    forms.widgets.CheckboxInput, forms.widgets.CheckboxSelectMultiple, forms.widgets.RadioSelect
                )
            ):
                field.widget.attrs.update({'class': 'form-control'})

    def serve(self, request: HttpRequest) -> HttpResponse:
        form_class = self.get_form()
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES, page=self)
            if form.is_valid():
                params = {'page': self, **self.process_submission(form)}
                return render(request, self.get_landing_page(), params)
        else:
            form = form_class(initial=self.get_initial_values(request), page=self)
        self._bootstrap(form)
        return render(request, 'edrnsite.content/form.html', {'page': self, 'form': form})  # Fix this

    class Meta:
        abstract = True


class BaseEmailForm(Page):
    '''Abstract base Wagtail model for a through-the-web form (not a Django form).'''
    subpage_types = []
    intro = RichTextField(blank=True, help_text='Introductory text to appear above the form')
    outro = RichTextField(blank=True, help_text='Text to appear below the form')
    thank_you_text = RichTextField(blank=True, help_text='Gratitude to display after form submission')
    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        InlinePanel('form_fields', label='Form Fields ✍️'),
        FieldPanel('outro'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname='col6', help_text='From whom this email will originate'),
                FieldPanel('to_address', classname='col6', help_text='Who should receive this email; commas in between multiple addresses')
            ]),
            FieldPanel('subject')
        ], 'Email')
    ]
    class Meta:
        abstract = True
