.. P5 EDRN Theme

EDRN Theme
==========

The EDRN theme package, ``edrn.theme``, is a generic Plone-5–compatible theme
add-on that gives the EDRN look and feel to a Plone 5 website. Although it can
be used in any Plone 5 site, it's mainly intended to be used as an add-on for
the Early Detection Research Network site at https://edrn.nci.nih.gov/. Of
course, if other EDRN efforts are built around the Plone content management
system, this add-on can be used as a theme.


Packaging
---------

Please note that this package is currently treated as a source dependency of
the P5_ package. It is currently not shipped separately or registered with the
Python Package Index (also known as the Cheeseshop_).


Installation
------------

There is no need to install this package separately as it is listed as a
dependency of the "policy" package, ``edrnsite.policy``. However, if it needed
to be used externally, it could be added to the Plone site's
``plone.recipe.zope2instance`` list of ``eggs`` or even installed as a
site-package in the Python installation used for Plone—although this is not at
all recommended.


EDRN Theme Module: `edrn.theme`
-------------------------------

.. automodule:: edrn.theme

This module contains some sub-modules and other items of note, detailed below.
Of course, since this is a Plone (and therefore Zope) module, it also contains
a ``configure.zcml`` file that describes how Zope should configure this
package when loaded.


Constants
~~~~~~~~~

.. autodata:: edrn.theme._

This is the message factory for translating strings into various languages.
The traditional name for this, ``_``, makes for ease of typing during ode
development.


Interfaces Module: ``edrn.theme.interfaces``
--------------------------------------------

.. automodule:: edrn.theme.interfaces

This module contains interfaces specific to the theme. There's currently just
one interface:

.. autoclass:: edrn.theme.interfaces.IEdrnThemeLayer

If you need to define additional artifacts specific to the EDRN theme, you
assign them to this marker interface.


Setup Handlers Module: ``edrn.theme.setuphandlers``
---------------------------------------------------

.. automodule:: edrn.theme.setuphandlers

Those experienced with Plone_ (as well as GenericSetup_) will recognize this
as the usual module providing functions for customizations that need Python
code to perform that can't be handled by the XML (and other) configuration
profile files.

For the ``edrn.theme`` package, this is currently nothing and contains just
boilerplate which may be needed in the future.


Testing Module: ``edrn.theme.testing``
--------------------------------------

.. automodule:: edrn.theme.testing

This module builds on `plone.app.testing`_ to provide a "testing layer" on top
of the Plone sandbox layer for building test fixtures for unit, integration,
functional, and acceptance testing of the EDRN theme package.

.. autoclass:: edrn.theme.testing.EdrnThemeLayer

This is the layer implementation for testing the theme. It's used to create the four following fixtures:

.. autodata:: edrn.theme.testing.EDRN_THEME_FIXTURE

Unit tests.

.. autodata:: edrn.theme.testing.EDRN_THEME_INTEGRATION_TESTING

Integration tests.

.. autodata:: edrn.theme.testing.EDRN_THEME_FUNCTIONAL_TESTING

Functional tests.

.. autodata:: edrn.theme.testing.EDRN_THEME_ACCEPTANCE_TESTING

A separate instance of the functional testing layer except specifically for *acceptance* tests.


Upgrades 



.. _Plone: https://plone.org/
.. _GenericSetup: https://docs.plone.org/develop/addons/components/genericsetup.html
.. _`plone.app.testing`: https://github.com/plone/plone.app.testing







Doc Trials
----------

.. tIp:: This is a tip!
   Use just the tip, please.

..  caution:: this hurts!
    Even if it's more than the tip.

..  danger:: WOW!
    This'll kill ya.

..  error:: Segmentation fault.
    Core dumped.


..  hint:: Try veganism.
    Plants are great.

..  Important:: Heed this well.
    It needs heeding.

..  Note:: Take note.
    This is a note.

..  WARNING:: Will Robinson.
    Wait, this should be a danger note.



.. _P5: https://github.com/EDRN/P5
.. _Cheeseshop: https://pypi.org/
