.. _install:

Installation of Camelot
=======================

This part of the documentation covers how to install Camelot.

Using conda
-----------

The easiest way to install Camelot is to install it with `conda`_, which is the package manager that the `Anaconda`_ distribution is built upon.
::

    $ conda install -c camelot-dev camelot-py

.. note:: Camelot is available for Python 2.7, 3.5 and 3.6 on Linux, macOS and Windows. For Windows, you will need to install ghostscript which you can get from their `downloads page`_.

.. _conda: https://conda.io/docs/
.. _Anaconda: http://docs.continuum.io/anaconda/
.. _downloads page: https://www.ghostscript.com/download/gsdnld.html

Using pip
---------

First, you'll need to install the dependencies, which include `Tkinter`_ and `ghostscript`_.

.. _Tkinter: https://wiki.python.org/moin/TkInter
.. _ghostscript: https://www.ghostscript.com

These can be installed using your system's package manager. You can run one of the following, based on your OS.

For Ubuntu
^^^^^^^^^^
::

    $ apt install python-tk ghostscript

Or for Python 3::

    $ apt install python3-tk ghostscript

For macOS
^^^^^^^^^
::

    $ brew install tcl-tk ghostscript

For Windows
^^^^^^^^^^^

For Tkinter, you can download the `ActiveTcl Community Edition`_ from ActiveState. For ghostscript, you can get the installer at the `ghostscript downloads page`_.

After installing ghostscript, you'll need to reboot your system to make sure that the ghostscript executable's path is in the windows PATH environment variable. In case you don't want to reboot, you can manually add the ghostscript executable's path to the PATH variable, `as shown here`_.

.. _ActiveTcl Community Edition: https://www.activestate.com/activetcl/downloads
.. _ghostscript downloads page: https://www.ghostscript.com/download/gsdnld.html
.. _as shown here: https://java.com/en/download/help/path.xml

----

You can do the following checks to see if the dependencies were installed correctly.

For Tkinter
^^^^^^^^^^^

Launch Python, and then at the prompt, type::

    >>> import Tkinter

Or in Python 3::

    >>> import tkinter

If you have Tkinter, Python will not print an error message, and if not, you will see an ``ImportError``.

For ghostscript
^^^^^^^^^^^^^^^

Run the following to check the ghostscript version.

For Ubuntu/macOS::

    $ gs -version

For Windows::

    C:\> gswin64c.exe -version

Or for Windows 32-bit::

    C:\> gswin32c.exe -version

If you have ghostscript, you should see the ghostscript version and copyright information.

Finally, you can use pip to install Camelot::

    $ pip install camelot-py[all]

From the source code
--------------------

After `installing the dependencies`_, you can install from the source by:

1. Cloning the GitHub repository.
::

    $ git clone https://www.github.com/socialcopsdev/camelot

2. Then simply using pip again.
::

    $ cd camelot
    $ pip install ".[all]"

.. _installing the dependencies: https://camelot-py.readthedocs.io/en/latest/user/install.html#using-pip