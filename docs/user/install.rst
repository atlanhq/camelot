.. _install:

Installation of Camelot
=======================

This part of the documentation covers how to install Camelot. First, you'll need to install the dependencies, which include `tk`_ and `ghostscript`_.

.. _tk: https://packages.ubuntu.com/trusty/python-tk
.. _ghostscript: https://www.ghostscript.com/

These can be installed using your system's package manager. You can run one of the following, based on your OS.

For Ubuntu::

    $ apt install python-tk ghostscript

.. note:: For Python 3, install python3-tk.

For macOS::

    $ brew install tcl-tk ghostscript

$ pip install camelot-py
------------------------

After installing the dependencies, you can simply use pip to install Camelot::

    $ pip install camelot-py

Get the source code
-------------------

Alternatively, you can install from the source by:

1. Cloning the GitHub repository.
::

    $ git clone https://www.github.com/socialcopsdev/camelot

2. Then simply using pip again.
::

    $ cd camelot
    $ pip install .