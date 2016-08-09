.. camelot documentation master file, created by
   sphinx-quickstart on Tue Jul 19 13:44:18 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================
Camelot: PDF parsing made simpler!
==================================

Camelot is a Python 2.7 library and command-line tool for getting tables out of PDF files.

Why another PDF table parsing library?
======================================

We tried a lot of tools available online to get tables out of PDFs, but each one had its limitations. `PDFTables`_ stopped its open source development in 2013. `SolidConverter`_ which powers `Smallpdf`_ is closed source. Recently, `Docparser`_ was launched, which again is closed source. `Tabula`_, though being open source, doesn't always give correct output. In most cases, we had to resort to writing custom scripts for each type of PDF.

.. _PDFTables: https://pdftables.com/
.. _SolidConverter: http://www.soliddocuments.com/pdf/-to-word-converter/304/1
.. _Smallpdf: smallpdf.com
.. _Docparser: https://docparser.com/
.. _Tabula: http://tabula.technology/

PDFs have feelings too
======================

PDF started as `The Camelot Project`_ when people wanted a cross-platform way to share documents, since a document looked different on each system. A PDF contains characters placed at specific x,y-coordinates. Spaces are simulated by placing characters relatively far apart.

Camelot uses two methods to parse tables from PDFs, :doc:`lattice <lattice>` and :doc:`stream <stream>`. The names were taken from Tabula but the implementation is somewhat different, though it follows the same philosophy. Lattice looks for lines between text elements while stream looks for whitespace between text elements.

.. _The Camelot Project: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf

Usage
=====

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.lattice import Lattice

    >>> extractor = Lattice(Pdf('us-030.pdf'))
    >>> tables = extractor.get_tables()
    >>> print tables['pg-1']

.. csv-table::
   :header: "Cycle Name","KI (1/km)","Distance (mi)","Percent Fuel Savings","","",""

   "","","","Improved Speed","Decreased Accel","Eliminate Stops","Decreased Idle"
   "2012_2","3.30","1.3","5.9%","9.5%","29.2%","17.4%"
   "2145_1","0.68","11.2","2.4%","0.1%","9.5%","2.7%"
   "4234_1","0.59","58.7","8.5%","1.3%","8.5%","3.3%"
   "2032_2","0.17","57.8","21.7%","0.3%","2.7%","1.2%"
   "4171_1","0.07","173.9","58.1%","1.6%","2.1%","0.5%"

Camelot comes with a command-line tool in which you can specify the output format (csv, tsv, html, json, and xlsx), page numbers you want to parse and the output directory in which you want the output files to be placed. By default, the output files are placed in the same directory as the PDF.

::

    Camelot: PDF parsing made simpler!

    usage:
     camelot [options] <method> [<args>...]

    options:
     -h, --help                Show this screen.
     -v, --version             Show version.
     -p, --pages <pageno>      Comma-separated list of page numbers.
                               Example: -p 1,3-6,10  [default: 1]
     -f, --format <format>     Output format. (csv,tsv,html,json,xlsx) [default: csv]
     -l, --log                 Print log to file.
     -o, --output <directory>  Output directory.

    camelot methods:
     lattice  Looks for lines between data.
     stream   Looks for spaces between data.

    See 'camelot <method> -h' for more information on a specific method.

Installation
============

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them by::

    pip install -U pip, setuptools

The required dependencies include `numpy`_, `OpenCV`_ and `ImageMagick`_.

.. _numpy: http://www.numpy.org/
.. _OpenCV: http://opencv.org/
.. _ImageMagick: http://www.imagemagick.org/script/index.php

We strongly recommend that you use a `virtual environment`_ to install Camelot. If you don't want to use a virtual environment, then skip the next section.

Installation & Setup (virtualenv)
---------------------------------

You'll need to install `virtualenvwrapper`_.

::

    pip install virtualenvwrapper

or

::

    sudo pip install virtualenvwrapper

Add the following lines to your `.bashrc` and source it.

::

    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/bin/virtualenvwrapper.sh

.. note:: The path to `virtualenvwrapper.sh` could be different on your system.

Finally make a virtual environment using::

    mkvirtualenv camelot

Installation (dependencies)
---------------------------

`numpy` can be install using `pip` itself.

::

    pip install numpy

`OpenCV` and `imagemagick` can be installed using your system's default package manager.

Linux
^^^^^

* Arch Linux

::

    sudo pacman -S opencv imagemagick

* Ubuntu

::

    sudo apt-get install libopencv-dev python-opencv imagemagick

OS X
^^^^

::

    brew install homebrew/science/opencv imagemagick

If you're working in a virtualenv, you'll need to create a symbolic link for the OpenCV shared object file::

    sudo ln -s /path/to/system/site-packages/cv2.so ~/path/to/virtualenv/site-packages/cv2.so

Finally, ``cd`` into the project directory and install by doing::

    make install

.. _virtual environment: http://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/

API Reference
=============

See :doc:`API doc <api>`.

Development
===========

Code
----

You can check the latest sources with the command::

    git clone https://github.com/socialcopsdev/camelot.git

Contributing
------------

See :doc:`Contributing doc <contributing>`.

Testing
-------

::

    make test

License
=======

BSD License