Python Version and Set Up
-------------------------

When attempting to build this site (or any of its components under ``src``),
use Python 2.7 with the following packages pre-installed:

• ``setuptools==38.5.1``
• ``pip==18.1``
• ``wheel-0.32.2``


Notes
-----

``p5pyp2.7`` aliased to ``~/Documents/Development/python2.7/bin/python2.7``
which is the Python environment as described above.

To build::

    p5py2.7 bootstrap.py -c dev.cfg
    bin/buildout -c dev.cfg
    bin/buildout -c dev.cfg install basic-site
    bin/zope-debug fg
    curl http://localhost:6468/edrn
