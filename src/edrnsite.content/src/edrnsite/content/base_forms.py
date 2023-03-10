# encoding: utf-8

'''😌 EDRN Site Content: Django forms.'''

from django import forms
from django.forms.utils import ErrorList


class BootstrapErrorList(ErrorList):
    '''Custom ErrorList that uses a Bootstrap-compatible default CSS class.'''
    def __init__(self, initlist=None, error_class=None, renderer=None):
        if error_class is None:
            error_class = 'text-danger'
        super().__init__(initlist, error_class, renderer)


class AbstractEDRNForm(forms.Form):
    '''This is an abstract form that sets up our preferred styles.'''
    template_name = 'edrnsite.content/form-rendering.html'
    template_name_label = 'edrnsite.content/label-rendering.html'
    error_css_class = 'is-invalid'
    required_css_class = 'is-required'

    def __init__(
        self,
        data=None,
        files=None,
        auto_id='id_%s',
        prefix=None,
        initial=None,
        error_class=BootstrapErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
        page=None
    ):
        super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
            use_required_attribute, renderer
        )
        self.page = page

    @staticmethod
    def get_encoding_type() -> str:
        '''Subclasses can override this if they need something other than ``application/x-www-form-urlencoded``.'''
        return 'application/x-www-form-urlencoded'

    class Meta:
        abstract = True
