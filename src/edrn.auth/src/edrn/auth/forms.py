# encoding: utf-8

'''🔐 EDRN auth: forms.'''

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.utils.translation import gettext_lazy as _


class EDRNUsernameField(UsernameField):
    '''A username field for the Early Detection Research Network.

    The Invicti (NetSparker) scans say we cannot have autocomplete on the username field.
    So we overrride the field in order to ensure autocomplete is off.
    '''
    def widget_attrs(self, widget):
        return {**super().widget_attrs(widget), 'autocomplete': 'off'}


class EDRNAuthenticationForm(AuthenticationForm):
    '''Authentication form for the Early Detection Research Network.

    The Invicti (NetSparker) scans say we cannot have autocomplete on the username
    and password fields. So we override the form in order to ensure autocomplete is off
    on both of them.
    '''
    username = EDRNUsernameField(widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
    )
