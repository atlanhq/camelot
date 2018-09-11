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
  >>> tables = camelot.read_pdf("foo.pdf")
  >>> tables
  <TableList n=2>
  >>> tables.export("foo.csv", f="csv", compress=True) # json, excel, html
  >>> tables[0]
  <Table shape=(3,4)>
  >>> tables[0].parsing_report
  {
      "accuracy": 96,
      "whitespace": 80,
      "order": 1,
      "page": 1
  }
  >>> tables[0].to_csv("foo.csv") # to_json, to_excel, to_html
  >>> tables[0].df

.. csv-table::
   :header: "Cycle Name","KI (1/km)","Distance (mi)","Percent Fuel Savings","","",""

   "","","","Improved Speed","Decreased Accel","Eliminate Stops","Decreased Idle"
   "2012_2","3.30","1.3","5.9%","9.5%","29.2%","17.4%"
   "2145_1","0.68","11.2","2.4%","0.1%","9.5%","2.7%"
   "4234_1","0.59","58.7","8.5%","1.3%","8.5%","3.3%"
   "2032_2","0.17","57.8","21.7%","0.3%","2.7%","1.2%"
   "4171_1","0.07","173.9","58.1%","1.6%","2.1%","0.5%"

::

  Usage: camelot [OPTIONS] FILEPATH

  Options:
    -p, --pages TEXT                Comma-separated page numbers to parse.
                                    Example: 1,3,4 or 1,4-end
    -o, --output TEXT               Output filepath.
    -f, --format [csv|json|excel|html]
                                    Output file format.
    -z, --zip                       Whether or not to create a ZIP archive.
    -m, --mesh                      Whether or not to use Lattice method of
                                    parsing. Stream is used by default.
    -T, --table_area TEXT           Table areas (x1,y1,x2,y2) to process.
                                    x1, y1
                                    -> left-top and x2, y2 -> right-bottom
    -split, --split_text            Whether or not to split text if it spans
                                    across multiple cells.
    -flag, --flag_size              (inactive) Whether or not to flag text which
                                    has uncommon size. (Useful to detect
                                    super/subscripts)
    -M, --margins <FLOAT FLOAT FLOAT>...
                                    char_margin, line_margin, word_margin for
                                    PDFMiner.
    -C, --columns TEXT              x-coordinates of column separators.
    -r, --row_close_tol INTEGER     Rows will be formed by combining text
                                    vertically within this tolerance.
    -c, --col_close_tol INTEGER     Columns will be formed by combining text
                                    horizontally within this tolerance.
    -back, --process_background     (with --mesh) Whether or not to process
                                    lines that are in background.
    -scale, --line_size_scaling INTEGER
                                    (with --mesh) Factor by which the page
                                    dimensions will be divided to get smallest
                                    length of detected lines.
    -copy, --copy_text [h|v]        (with --mesh) Specify direction in which
                                    text will be copied over in a spanning cell.
    -shift, --shift_text [l|r|t|b]  (with --mesh) Specify direction in which
                                    text in a spanning cell should flow.
    -l, --line_close_tol INTEGER    (with --mesh) Tolerance parameter used to
                                    merge close vertical lines and close
                                    horizontal lines.
    -j, --joint_close_tol INTEGER   (with --mesh) Tolerance parameter used to
                                    decide whether the detected lines and points
                                    lie close to each other.
    -block, --threshold_blocksize INTEGER
                                    (with --mesh) For adaptive thresholding,
                                    size of a pixel neighborhood that is used to
                                    calculate a threshold value for the pixel:
                                    3, 5, 7, and so on.
    -const, --threshold_constant INTEGER
                                    (with --mesh) For adaptive thresholding,
                                    constant subtracted from the mean or
                                    weighted mean.
                                    Normally, it is positive but
                                    may be zero or negative as well.
    -I, --iterations INTEGER        (with --mesh) Number of times for
                                    erosion/dilation is applied.
    -G, --geometry_type [text|table|contour|joint|line]
                                    Plot geometry found on pdf page for
                                    debugging.
                                    text: Plot text objects. (Useful to get
                                          table_area and columns coordinates)
                                    table: Plot parsed table.
                                    contour (with --mesh): Plot detected rectangles.
                                    joint (with --mesh): Plot detected line intersections.
                                    line (with --mesh): Plot detected lines.
    --help                          Show this message and exit.

The User Guide
--------------

This part of the documentation, which is mostly prose, begins with some
background information about Requests, then focuses on step-by-step
instructions for getting the most out of Requests.

.. toctree::
   :maxdepth: 2

   user/intro
   user/install
   user/quickstart

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