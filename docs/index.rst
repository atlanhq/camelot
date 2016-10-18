.. camelot documentation master file, created by
   sphinx-quickstart on Tue Jul 19 13:44:18 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================
Camelot: pdf parsing made simpler!
==================================

Camelot is a Python 2.7 library and command-line tool for getting tables out of pdf files.

Why another pdf table parsing library?
======================================

We tried a lot of tools available online to parse tables from pdf files. `PDFTables`_, `SolidConverter`_ are closed source, commercial products and a free trial doesn't last forever. `Tabula`_, which is open source, isn't very scalable. We found nothing that gave us complete control over the parsing process. In most cases, we didn't get the correct output and had to resort to writing custom scripts for each type of pdf.

.. _PDFTables: https://pdftables.com/
.. _SolidConverter: http://www.soliddocuments.com/pdf/-to-word-converter/304/1
.. _Tabula: http://tabula.technology/

Some background
===============

PDF started as `The Camelot Project`_ when people wanted a cross-platform way for sending and viewing documents. A pdf file contains characters placed at specific x,y-coordinates. Spaces are simulated by placing characters relatively far apart.

Camelot uses two methods to parse tables from PDFs, :doc:`lattice <lattice>` and :doc:`stream <stream>`. The names were taken from Tabula but the implementation is somewhat different, though it follows the same philosophy. Lattice looks for lines between text elements while stream looks for whitespace between text elements.

.. _The Camelot Project: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf

Usage
=====

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.lattice import Lattice

    >>> manager = Pdf(Lattice(), 'us-030.pdf')
    >>> tables = manager.extract()
    >>> print tables['page-1']['table-1']['data']

.. csv-table::
   :header: "Cycle Name","KI (1/km)","Distance (mi)","Percent Fuel Savings","","",""

   "","","","Improved Speed","Decreased Accel","Eliminate Stops","Decreased Idle"
   "2012_2","3.30","1.3","5.9%","9.5%","29.2%","17.4%"
   "2145_1","0.68","11.2","2.4%","0.1%","9.5%","2.7%"
   "4234_1","0.59","58.7","8.5%","1.3%","8.5%","3.3%"
   "2032_2","0.17","57.8","21.7%","0.3%","2.7%","1.2%"
   "4171_1","0.07","173.9","58.1%","1.6%","2.1%","0.5%"

Camelot comes with a CLI where you can specify page numbers, output format, output directory etc. By default, the output files are placed in the same directory as the PDF.

::

    Camelot: PDF parsing made simpler!

    usage:
     camelot [options] <method> [<args>...]

    options:
     -h, --help                Show this screen.
     -v, --version             Show version.
     -V, --verbose             Verbose.
     -p, --pages <pageno>      Comma-separated list of page numbers.
                               Example: -p 1,3-6,10  [default: 1]
     -P, --parallel            Parallelize the parsing process.
     -f, --format <format>     Output format. (csv,tsv,html,json,xlsx) [default: csv]
     -l, --log                 Log to file.
     -o, --output <directory>  Output directory.
     -M, --cmargin <cmargin>   Char margin. Chars closer than cmargin are
                               grouped together to form a word. [default: 1.0]
     -L, --lmargin <lmargin>   Line margin. Lines closer than lmargin are
                               grouped together to form a textbox. [default: 0.5]
     -W, --wmargin <wmargin>   Word margin. Insert blank spaces between chars
                               if distance between words is greater than word
                               margin. [default: 0.1]
     -J, --split_text          Split text lines if they span across multiple cells.
     -K, --flag_size           Flag substring if its size differs from the whole string.
                               Useful for super and subscripts.
     -X, --print-stats         List stats on the parsing process.
     -Y, --save-stats          Save stats to a file.
     -Z, --plot <dist>         Plot distributions. (page,all,rc)

    camelot methods:
     lattice  Looks for lines between data.
     stream   Looks for spaces between data.

    See 'camelot <method> -h' for more information on a specific method.

Installation
============

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them by::

    pip install -U pip setuptools

The required dependencies include `numpy`_, `OpenCV`_ and `ImageMagick`_.

.. _numpy: http://www.numpy.org/
.. _OpenCV: http://opencv.org/
.. _ImageMagick: http://www.imagemagick.org/script/index.php

Installing dependencies
-----------------------

numpy can be install using `pip`. OpenCV and imagemagick can be installed using your system's default package manager.

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

Finally, `cd` into the project directory and install by::

    make install

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