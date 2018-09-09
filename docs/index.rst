.. camelot documentation master file, created by
   sphinx-quickstart on Tue Jul 19 13:44:18 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================================
Camelot: PDF Table Parsing for Humans
=====================================

Camelot is a Python 2.7 library and command-line tool for extracting tabular data from PDF files.

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

    >>> import camelot
    >>> tables = camelot.read_pdf("foo.pdf")
    >>> tables
    <TableList n=2>
    >>> tables.export("foo.csv", f="csv", compress=True) # json, excel, html
    >>> tables[0]
    <Table shape=(3,4)>
    >>> tables[0].to_csv("foo.csv") # to_json, to_excel, to_html
    >>> tables[0].parsing_report
    {
        "accuracy": 96,
        "whitespace": 80,
        "order": 1,
        "page": 1
    }
    >>> df = tables[0].df

.. csv-table::
   :header: "Cycle Name","KI (1/km)","Distance (mi)","Percent Fuel Savings","","",""

   "","","","Improved Speed","Decreased Accel","Eliminate Stops","Decreased Idle"
   "2012_2","3.30","1.3","5.9%","9.5%","29.2%","17.4%"
   "2145_1","0.68","11.2","2.4%","0.1%","9.5%","2.7%"
   "4234_1","0.59","58.7","8.5%","1.3%","8.5%","3.3%"
   "2032_2","0.17","57.8","21.7%","0.3%","2.7%","1.2%"
   "4171_1","0.07","173.9","58.1%","1.6%","2.1%","0.5%"

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

See :doc:`Contributing guidelines <contributing>`.

Testing
-------

::

    python setup.py test

License
=======

BSD License