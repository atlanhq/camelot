.. Camelot documentation master file, created by
   sphinx-quickstart on Tue Jul 19 13:44:18 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Camelot: PDF Table Parsing for Humans
=====================================

Release v\ |version|. (:ref:`Installation <install>`)

.. image:: https://img.shields.io/badge/license-MIT-lightgrey.svg
    :target: https://pypi.org/project/camelot-py/

.. image:: https://img.shields.io/badge/python-2.7-blue.svg
    :target: https://pypi.org/project/camelot-py/

**Camelot** is a Python library which makes it easy for *anyone* to extract tables from PDF files!

.. note:: Camelot only works with:

          - Python 2, with **Python 3** support `on the way`_.
          - Text-based PDFs and not scanned documents. If you can click-and-drag to select text in your table in a PDF viewer, then your PDF is text-based. Support for image-based PDFs using **OCR** is `planned`_.

.. _on the way: https://github.com/socialcopsdev/camelot/issues/81
.. _planned: https://github.com/socialcopsdev/camelot/issues/101

------------------------

**Here's how you can extract tables from PDF files.** Check out the PDF used in this example, `here`_.

.. _here: _static/pdf/foo.pdf

::

    >>> import camelot
    >>> tables = camelot.read_pdf('foo.pdf', mesh=True)
    >>> tables
    <TableList tables=1>
    >>> tables.export('foo.csv', f='csv', compress=True) # json, excel, html
    >>> tables[0]
    <Table shape=(7, 7)>
    >>> tables[0].parsing_report
    {
        'accuracy': 99.02,
        'whitespace': 12.24,
        'order': 1,
        'page': 1
    }
    >>> tables[0].to_csv('foo.csv') # to_json, to_excel, to_html
    >>> tables[0].df # get a pandas DataFrame!

.. csv-table::
  :file: _static/csv/foo.csv

There's a :ref:`command-line interface <cli>` too!

Why Camelot?
------------
- **You are in control**: Unlike other libraries and tools which either give a nice output or fail miserably (with no in-between), Camelot gives you the power to tweak table extraction. (Since everything in the real world, including PDF table extraction, is fuzzy.)
- **Metrics**: *Bad* tables can be discarded based on metrics like accuracy and whitespace, without ever having to manually look at each table.
- Each table is a **pandas DataFrame**, which enables seamless integration into data analysis workflows.
- **Export** to multiple formats, including json, excel and html.
- Simple and Elegant API, written in **Python**!

The User Guide
--------------

This part of the documentation, begins with some background information about why Camelot was created, takes a small dip into the implementation details and then focuses on step-by-step instructions for getting the most out of Camelot.

.. toctree::
   :maxdepth: 2

   user/intro
   user/install
   user/how-it-works
   user/quickstart
   user/advanced
   user/cli

The API Documentation / Guide
-----------------------------

If you are looking for information on a specific function, class, or method,
this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api

The Contributor Guide
---------------------

If you want to contribute to the project, this part of the documentation is for
you.

.. toctree::
   :maxdepth: 2

   dev/contributing