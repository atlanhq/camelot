.. camelot documentation master file, created by
   sphinx-quickstart on Tue Jul 19 13:44:18 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================
Camelot: PDF parsing made simpler!
==================================

Camelot is a Python 2.7 library and command-line tool for getting tables out of PDF files.

Why another PDF table parsing library?
--------------------------------------

We tried a lot of tools available online to get tables out of PDFs, but each one had its limitations. `PDFTables`_ stopped its development in 2013 and became commercial. `SolidConverter`_ which powers `Smallpdf`_ is closed source. `Tabula`_, though being open source, doesn't always give correct output. Recently, `Docparser`_ was launched, but it too is closed source. In most cases, we had to resort to writing custom scripts for each type of PDF.

.. _PDFTables: https://pdftables.com/
.. _SolidConverter: http://www.soliddocuments.com/pdf/-to-word-converter/304/1
.. _Smallpdf: smallpdf.com
.. _Tabula: http://tabula.technology/
.. _Docparser: https://docparser.com/

PDFs have feelings too
----------------------

PDF started as `The Camelot Project`_ when people wanted a cross-platform way to share documents, since documents looked different on each system. A PDF contains characters placed at a specific x,y-coordinate. Spaces are simulated by placing characters far apart.

Camelot uses two methods to parse tables from PDFs, :doc:`lattice <lattice>` and :doc:`stream <stream>`. The names were taken from Tabula but the implementation is somewhat different, though it follows the same philosophy. Lattice looks for lines between text elements while stream looks for whitespace between text elements.

.. _The Camelot Project: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf

Usage
-----

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

Camelot comes with a command-line tool in which you can specify the output format (we currently support csv, tsv, html, json, and xlsx), page numbers you want to parse and the output directory in which you want the output files to be placed. By default, the output files are placed in the same directory as the PDF.

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
------------

The required dependencies include `numpy`_, `OpenCV`_ and `ImageMagick`_.

.. _numpy: http://www.numpy.org/
.. _OpenCV: http://opencv.org/
.. _ImageMagick: http://www.imagemagick.org/script/index.php

We strongly recommend that you use a virtual environment to install Camelot.

Linux
^^^^^

* Arch Linux ::

    pacman -S opencv imagemagick

* Ubuntu ::

    sudo apt-get install libopencv-dev python-opencv imagemagick

OS X
^^^^

::

    brew install homebrew/science/opencv imagemagick

If you're working in a virtual environment... ::

    sudo ln -s /path/to/system/site-packages/cv2.so ~/.virtualenvs/site-packages/cv2.so

Finally, ``cd`` into the project directory and execute this. ::

    python setup.py install

API Reference
-------------

See :doc:`API docs <api>`.

Development
-----------

Code
^^^^

You can check the latest sources with the command::

    git clone https://github.com/socialcopsdev/camelot.git

Contributing
^^^^^^^^^^^^

The preferred way to contribute to Camelot is to fork this repository, and then submit a "pull request" (PR):

1. Create an account on GitHub if you don't already have one.

2. Fork the project repository: click on the ‘Fork’ button near the top of the page. This creates a copy of the code under your account on the GitHub server.

3. Clone this copy to your local disk.
4. Create a branch to hold your changes::

    git checkout -b my-feature

  and start making changes. Never work in the `master` branch!

5. Work on this copy, on your computer, using Git to do the version control. When you’re done editing, do::

    $ git add modified_files
    $ git commit

  to record your changes in Git, then push them to GitHub with::

    $ git push -u origin my-feature

Finally, go to the web page of the your fork of the camelot repo, and click ‘Pull request’ to send your changes to the maintainers for review.

Testing
^^^^^^^

License
-------

BSD License