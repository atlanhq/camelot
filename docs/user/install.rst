.. _install:

Installation
============

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them by::

    pip install -U pip setuptools

The dependencies include `tk`_ and `ghostscript`_.

.. _tk: https://wiki.tcl.tk/3743
.. _ghostscript: https://www.ghostscript.com/

Installing dependencies
-----------------------

tk and ghostscript can be installed using your system's default package manager.

Linux
^^^^^

* Ubuntu

::

    sudo apt-get install python-opencv python-tk ghostscript

* Arch Linux

::

    sudo pacman -S opencv tk ghostscript

OS X
^^^^

::

    brew install homebrew/science/opencv ghostscript

Finally, `cd` into the project directory and install by::

    python setup.py install