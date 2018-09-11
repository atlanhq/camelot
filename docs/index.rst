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

**Camelot** is a Python library and command-line tool for extracting tables from PDF files.

.. note:: Camelot only works with:

          - Python 2, with **Python 3** support `on the way`_.
          - Text-based PDFs and not scanned documents. If you can click-and-drag to select text in your table in a PDF viewer, then your PDF is text-based. Support for image-based PDFs using **OCR** is `planned`_.

.. _on the way: https://github.com/socialcopsdev/camelot/issues/81
.. _planned: https://github.com/socialcopsdev/camelot/issues/101

Usage
-----

::

  >>> import camelot
  >>> tables = camelot.read_pdf('foo.pdf')
  >>> tables
  <TableList n=2>
  >>> tables.export('foo.csv', f='csv', compress=True) # json, excel, html
  >>> tables[0]
  <Table shape=(3,4)>
  >>> tables[0].parsing_report
  {
      'accuracy': 96,
      'whitespace': 80,
      'order': 1,
      'page': 1
  }
  >>> tables[0].to_csv('foo.csv') # to_json, to_excel, to_html
  >>> tables[0].df

.. csv-table::
  :file: _static/csv/foo.csv

The User Guide
--------------

.. toctree::
   :maxdepth: 2

   user/intro
   user/install
   user/quickstart
   user/cli

The API Documentation / Guide
-----------------------------

.. toctree::
   :maxdepth: 2

   api

The Contributor Guide
---------------------

.. toctree::
   :maxdepth: 2

   dev/contributing