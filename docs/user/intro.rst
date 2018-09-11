PDF started as `The Camelot Project`_ when people wanted a cross-platform way for sending and viewing documents. A pdf file contains characters placed at specific x,y-coordinates. Spaces are simulated by placing characters relatively far apart.

Camelot uses two methods to parse tables from PDFs, :doc:`lattice <lattice>` and :doc:`stream <stream>`. The names were taken from Tabula but the implementation is somewhat different, though it follows the same philosophy. Lattice looks for lines between text elements while stream looks for whitespace between text elements.

.. _The Camelot Project: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf

Why another pdf table parsing library?
======================================

We tried a lot of tools available online to parse tables from pdf files. `PDFTables`_, `SolidConverter`_ are closed source, commercial products and a free trial doesn't last forever. `Tabula`_, which is open source, isn't very scalable. We found nothing that gave us complete control over the parsing process. In most cases, we didn't get the correct output and had to resort to writing custom scripts for each type of pdf.

.. _PDFTables: https://pdftables.com/
.. _SolidConverter: http://www.soliddocuments.com/pdf/-to-word-converter/304/1
.. _Tabula: http://tabula.technology/

License
=======

MIT License