.. _intro:

Introduction
============

The Camelot Project
-------------------

The Portable Document Format (PDF) was born out of `The Camelot Project`_ when a need was felt for "a universal to communicate documents across a wide variety of machine configurations, operating systems and communication networks". The goal was to make these documents viewable on any display and printable on any modern printers. The invention of the `PostScript`_ page description language, which enabled the creation of *fixed-layout* flat documents (with text, fonts, graphics, images encapsulated), solved the problem.

At a very high level, PostScript defines instructions, such as, "place this character at this x,y coordinate on a plane". Spaces can be *simulated* by placing characters relatively far apart. Extending from that, tables can be *simulated* by placing characters (which constitute words) in two-dimensional grids. A PDF viewer just takes these instructions and draws everything for the user to view. Since it's just characters on a plane, there is no table data structure which can be extracted and used for analysis!

Sadly, a lot of open data is given out as tables which are trapped inside PDF files.

.. _PostScript: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf

Why another PDF Table Extraction library?
-----------------------------------------

There are both open (`Tabula`_, `pdf-table-extract`_) and closed-source (`smallpdf`_, `PDFTables`_) tools that are widely used, to extract tables from PDF files. They either give a nice output, or fail miserably. There is no in-between. This is not helpful, since everything in the real world, including PDF table extraction, is fuzzy, leading to creation of adhoc table extraction scripts for each different type of PDF that the user wants to parse.

Camelot was created with the goal of offering its users complete control over table extraction. If the users are not able to get the desired output with the default configuration, they should be able to tweak it and get the job done!

Here is a `comparison`_ of Camelot's output with outputs from other open-source PDF parsing libraries and tools.

.. _Tabula: http://tabula.technology/
.. _pdf-table-extract: https://github.com/ashima/pdf-table-extract
.. _PDFTables: https://pdftables.com/
.. _Smallpdf: https://smallpdf.com
.. _comparison: https://github.com/socialcopsdev/camelot/wiki/Comparison-with-other-PDF-Table-Extraction-libraries-and-tools

What's in a name?
-----------------

As you can already guess, this library is named after `The Camelot Project`_.

Fun fact: "Camelot" is the name of the castle in the British comedy film `Monty Python and the Holy Grail`_ (and in the `Arthurian legend`_, which the film depicts), where Arthur leads his men, the Knights of the Round Table, and then sets off elsewhere after deciding that it is "a silly place". Interestingly, the language in which this library is written (Python) was named after Monty Python.

.. _The Camelot Project: http://www.planetpdf.com/planetpdf/pdfs/warnock_camelot.pdf
.. _Monty Python and the Holy Grail: https://en.wikipedia.org/wiki/Monty_Python_and_the_Holy_Grail
.. _Arthurian legend: https://en.wikipedia.org/wiki/King_Arthur

Camelot License
---------------

    .. include:: ../../LICENSE