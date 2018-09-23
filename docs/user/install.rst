.. _install:

Installation of Camelot
=======================

This part of the documentation covers the installation of Camelot. First, you'll need to install the dependencies, which include `tk`_ and `ghostscript`_.

.. _tk: https://packages.ubuntu.com/trusty/python-tk
.. _ghostscript: https://www.ghostscript.com/

These can be installed using your system's package manager. You can run the following based on your OS.

For Ubuntu::

    $ apt install python-tk ghostscript

For macOS::

    $ brew install tcl-tk ghostscript

$ pip install camelot-py
------------------------

After installing the dependencies, you can simply use pip to install Camelot::

    $ pip install camelot-py

Get the Source Code
-------------------

Alternatively, you can install from source by:

1. Cloning the GitHub repository.
::

    $ git clone https://www.github.com/socialcopsdev/camelot

2. And then simply using pip again.
::

    $ cd camelot
    $ pip install .