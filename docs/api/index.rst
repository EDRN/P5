.. P5

API
===

Reference documentation for the EDRN P5 Application Programmer Interface.

The EDRN Portal P5 contains the following Python packages:

• The theme, ``edrn.theme``, which provides the look-and-feel for the site,
  converting the Plone 5 theme into the Early Detection Research Network
  theme.  This theme isn't specific to the EDRN Portal and can be re-used
  for any Plone-based site that also serves the Early Detection Research
  Network.
• The portlets, ``edrnsite.portlets``, provides side-bar like items for the
  portal.  While generically written for any Plone 5 site, these are really
  only at home in the EDRN site.
• The EDRN Knowledge Environment, or EKE. Previously (P4 days) this was
  spread into separate Python packages that each had a responsibility for
  a specific part of the EKE, such as ``eke.publications`` for publications
  and ``eke.biomarker`` for biomarkers. However, because of circular
  dependencies between knowledge artifacts, the entire EKE is now in a
  single pakcage, ``eke.knowledge``.
• The policy, ``edrnsite.policy``. This is the package that orchestrates all
  the dependencies (including the three packages above) and essentially turns
  a Plone 5 site into the EDRN Portal P5 site.

Given the above, all it takes then is to install ``edrnsite.policy`` add-on
and activate it in a Plone site. And indeed, that's what the supporting
scripts in this project like ``setupEDRN.py`` do.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   edrn.theme/index



.. Constants
.. ---------

.. Functions
.. ---------

.. Classes
.. -------

