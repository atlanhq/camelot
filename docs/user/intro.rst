.. _intro:

Introduction
============

The Camelot Project
-------------------

The Portable Document Format (PDF) was born out of `The Camelot Project`_ when a need was felt for "a universal to communicate documents across a wide variety of machine configurations, operating systems and communication networks". The goal was to make these documents viewable on any display and printable on any modern printers. The invention of the `PostScript`_ page description language, which enabled the creation of fixed-layout flat documents (with text, fonts, graphics, images encapsulated), solved the problem.

At a very high level, PostScript defines instructions, such as, "place this character at this x,y coordinate on a plane". Spaces can be *simulated* by placing characters relatively far apart. Similarly, tables can be *simulated* by placing characters (and words) in two-dimensional grids. A PDF viewer just takes these instructions and draws everything for the user to view. Since it's just characters on a plane, there is no table data structure which can be directly extracted and used for analysis!

Sadly, a lot of open data is given out as tables which are trapped inside PDF files.

.. _The Camelot Project: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf
.. _PostScript: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf

Why another PDF Table Parsing library?
--------------------------------------

There are both open (`Tabula`_) and closed-source (`PDFTables`_, `smallpdf`_) tools that are used widely to extract tables from PDF files. They either give nice output, or fail miserably. There is no in-between. This does not help most users, since everything in the real world, including PDF table extraction, is fuzzy. Which leads to creation adhoc table extraction scripts for each different type of PDF that the user wants to parse.

Camelot was created with the goal of offering its users complete control over table extraction. If the users are not able to the desired output with the default configuration, they should be able to tweak the parameters and get the tables out!

Here is a `comparison`_ of Camelot's output with outputs from other libraries and tools.

.. _Tabula: http://tabula.technology/
.. _PDFTables: https://pdftables.com/
.. _Smallpdf: https://smallpdf.com
.. _comparison: https://github.com/socialcopsdev/camelot/wiki/Comparison-with-other-PDF-Table-Parsing-libraries-and-tools

Camelot License
---------------

    .. include:: ../../LICENSE