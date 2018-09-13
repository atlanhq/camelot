.. _advanced:

Advanced Usage
==============

This page covers some of the more advanced configurations for :ref:`Stream <stream>` and :ref:`Lattice <lattice>`.

Process background lines
------------------------

To detect line segments, Lattice needs the lines that make the table, to be in foreground. Here's an example of a table in which lines are in the background.

.. figure:: ../_static/png/background_lines.png
   :scale: 50%
   :alt: A table with lines in background
   :align: left

Source: `PDF`_

To do it, do this.

.. _PDF: ../_static/pdf/background_lines.pdf

::

    >>> tables = camelot.read_pdf('background_lines.pdf', mesh=True, process_background=True)
    >>> tables[1].df

.. csv-table::
  :file: ../_static/csv/background_lines.csv

Plot geometry
-------------

_static/pdf/foo.pdf

::

    >>> camelot.plot_geometry('foo.pdf', geometry_type='text')

.. figure:: ../_static/png/geometry_text.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

::

    >>> camelot.plot_geometry('foo.pdf', geometry_type='line')

.. figure:: ../_static/png/geometry_line.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

::

    >>> camelot.plot_geometry('foo.pdf', mesh=True, geometry_type='joint')

.. figure:: ../_static/png/geometry_joint.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

::

    >>> camelot.plot_geometry('foo.pdf', mesh=True, geometry_type='contour')

.. figure:: ../_static/png/geometry_contour.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

::

    >>> camelot.plot_geometry('foo.pdf', mesh=True, geometry_type='table')

.. figure:: ../_static/png/geometry_table.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

You can call Lattice with debug={'line', 'intersection', 'contour', 'table'}, and call `debug_plot()` which will generate an image like the ones on this page, with the help of which you can modify various parameters. See :doc:`API doc <api>` for more information.

Specify table areas
-------------------

_static/pdf/table_areas.pdf

::

    >>> tables = camelot.read_pdf('table_areas.pdf', table_areas=['316,499,566,337'])
    >>> tables[0].df

.. csv-table::
  :file: ../_static/csv/table_areas.csv

Specify column separators
-------------------------

_static/pdf/column_separators.pdf

::

    >>> tables = camelot.read_pdf('column_separators.pdf', columns=['72,95,209,327,442,529,566,606,683'])
    >>> tables[0].df

.. csv-table::

    "...","...","...","...","...","...","...","...","...","..."
    "LICENSE","","","","PREMISE","","","","",""
    "NUMBER TYPE DBA NAME","","","LICENSEE NAME","ADDRESS","CITY","ST","ZIP","PHONE NUMBER","EXPIRES"
    "...","...","...","...","...","...","...","...","...","..."

Split text along separators
---------------------------

_static/pdf/column_separators.pdf

::

    >>> tables = camelot.read_pdf('column_separators.pdf', columns=['72,95,209,327,442,529,566,606,683'], split_text=True)
    >>> tables[0].df

.. csv-table::

    "...","...","...","...","...","...","...","...","...","..."
    "LICENSE","","","","PREMISE","","","","",""
    "NUMBER","TYPE","DBA NAME","LICENSEE NAME","ADDRESS","CITY","ST","ZIP","PHONE NUMBER","EXPIRES"
    "...","...","...","...","...","...","...","...","...","..."

Flag subscripts and superscripts
--------------------------------

_static/pdf/superscript.pdf

.. figure:: ../_static/png/superscript.png
   :align: left

::

    >>> tables = camelot.read_pdf('superscript.pdf', flag_size=True)
    >>> tables[0].df

.. csv-table::

    "...","...","...","...","...","...","...","...","...","...","..."
    "Karnataka","22.44","19.59","-","-","2.86","1.22","-","0.89","-","0.69"
    "Kerala","29.03","24.91<s>2</s>","-","-","4.11","1.77","-","0.48","-","1.45"
    "Madhya Pradesh","27.13","23.57","-","-","3.56","0.38","-","1.86","-","1.28"
    "...","...","...","...","...","...","...","...","...","...","..."

Control how text is grouped into rows
-------------------------------------

_static/pdf/group_rows.pdf

::

    >>> tables = camelot.read_pdf('group_rows.pdf')
    >>> tables[0].df

.. csv-table::

    "Clave","","Clave","","","Clave",""
    "","Nombre Entidad","","","Nombre Municipio","","Nombre Localidad"
    "Entidad","","Municipio","","","Localidad",""
    "01","Aguascalientes","001","Aguascalientes","","0094","Granja Adelita"
    "01","Aguascalientes","001","Aguascalientes","","0096","Agua Azul"
    "01","Aguascalientes","001","Aguascalientes","","0100","Rancho Alegre"

::

    >>> tables = camelot.read_pdf('group_rows.pdf', row_close_tol=10)
    >>> tables[0].df

.. csv-table::

    "Clave","Nombre Entidad","Clave","","Nombre Municipio","Clave","Nombre Localidad"
    "Entidad","","Municipio","","","Localidad",""
    "01","Aguascalientes","001","Aguascalientes","","0094","Granja Adelita"
    "01","Aguascalientes","001","Aguascalientes","","0096","Agua Azul"
    "01","Aguascalientes","001","Aguascalientes","","0100","Rancho Alegre"

Detect short lines
------------------

_static/pdf/short_lines.pdf

The scale parameter is used to determine the length of the structuring element used for morphological transformations. The length of vertical and horizontal structuring elements are found by dividing the image's height and width respectively, by `scale`. Large `scale` will lead to a smaller structuring element, which means that smaller lines will be detected. The default value for scale is 15.

.. figure:: ../_static/png/short_lines.png
   :align: left

::

    >>> camelot.plot_geometry('short_lines.pdf', mesh=True, geometry_type='table')

.. figure:: ../_static/png/short_lines_1.png
   :align: left

Clearly, it couldn't detected those small lines in the lower left part. Therefore, we need to increase the value of scale. Let's try a value of 40.

::

    >>> camelot.plot_geometry('short_lines.pdf', mesh=True, geometry_type='table', line_size_scaling=40)

.. figure:: ../_static/png/short_lines_2.png
   :align: left

::

    >>> tables = camelot.read_pdf('short_lines.pdf', mesh=True, line_size_scaling=40)
    >>> tables[0].df

.. csv-table::

    "Investigations","No. ofHHs","Age/Sex/Physiological  Group","Preva-lence","C.I*","RelativePrecision","Sample sizeper State"
    "Anthropometry","2400","All ...","","","",""
    "Clinical Examination","","","","","",""
    "History of morbidity","","","","","",""
    "Diet survey","1200","All ...","","","",""
    "Blood Pressure #","2400","Men (≥ 18yrs)","10%","95%","20%","1728"
    "","","Women (≥ 18 yrs)","","","","1728"
    "Fasting blood glucose","2400","Men (≥ 18 yrs)","5%","95%","20%","1825"
    "","","Women (≥ 18 yrs)","","","","1825"
    "Knowledge &Practices on HTN &DM","2400","Men (≥ 18 yrs)","-","-","-","1728"
    "","2400","Women (≥ 18 yrs)","-","-","-","1728"

beware

Voila! It detected the smaller lines.

Shift text in spanning cells
----------------------------

in order

_static/pdf/short_lines.pdf

.. figure:: ../_static/png/short_lines.png
   :align: left

::

    >>> tables = camelot.read_pdf('short_lines.pdf', mesh=True, line_size_scaling=40, shift_text=[''])
    >>> tables[0].df

.. csv-table::

    "Investigations","No. ofHHs","Age/Sex/Physiological  Group","Preva-lence","C.I*","RelativePrecision","Sample sizeper State"
    "Anthropometry","","","","","",""
    "Clinical Examination","2400","","All ...","","",""
    "History of morbidity","","","","","",""
    "Diet survey","1200","","All ...","","",""
    "","","Men (≥ 18yrs)","","","","1728"
    "Blood Pressure #","2400","Women (≥ 18 yrs)","10%","95%","20%","1728"
    "","","Men (≥ 18 yrs)","","","","1825"
    "Fasting blood glucose","2400","Women (≥ 18 yrs)","5%","95%","20%","1825"
    "Knowledge &Practices on HTN &","2400","Men (≥ 18 yrs)","-","-","-","1728"
    "DM","2400","Women (≥ 18 yrs)","-","-","-","1728"

::

    >>> tables = camelot.read_pdf('short_lines.pdf', mesh=True, line_size_scaling=40, shift_text=['r', 'b'])
    >>> tables[0].df

.. csv-table::

    "Investigations","No. ofHHs","Age/Sex/Physiological  Group","Preva-lence","C.I*","RelativePrecision","Sample sizeper State"
    "Anthropometry","","","","","",""
    "Clinical Examination","","","","","",""
    "History of morbidity","2400","","","","","All ..."
    "Diet survey","1200","","","","","All ..."
    "","","Men (≥ 18yrs)","","","","1728"
    "Blood Pressure #","2400","Women (≥ 18 yrs)","10%","95%","20%","1728"
    "","","Men (≥ 18 yrs)","","","","1825"
    "Fasting blood glucose","2400","Women (≥ 18 yrs)","5%","95%","20%","1825"
    "","2400","Men (≥ 18 yrs)","-","-","-","1728"
    "Knowledge &Practices on HTN &DM","2400","Women (≥ 18 yrs)","-","-","-","1728"

Copy text in spanning cells
---------------------------

in order

_static/pdf/copy_text.pdf

In the file used above, you can see that some cells spanned a lot of rows, `fill` just copies the same value to all rows/columns of a spanning cell. You can apply fill horizontally, vertically or both. Let us fill the output for the file we used above, vertically.

::

    >>> camelot.read_pdf('copy_text.pdf', mesh=True)

.. csv-table::

    "Sl. No.","Name of State/UT","Name of District","Disease/ Illness","No. of Cases","No. of Deaths","Date of start of outbreak","Date of reporting","Current Status","..."
    "1","Kerala","Kollam","i.  Food Poisoning","19","0","31/12/13","03/01/14","Under control","..."
    "2","Maharashtra","Beed","i.  Dengue & Chikungunya   i","11","0","03/01/14","04/01/14","Under control","..."
    "3","Odisha","Kalahandi","iii. Food Poisoning","42","0","02/01/14","03/01/14","Under control","..."
    "4","West Bengal","West Medinipur","iv. Acute Diarrhoeal Disease","145","0","04/01/14","05/01/14","Under control","..."
    "","","Birbhum","v.  Food Poisoning","199","0","31/12/13","31/12/13","Under control","..."
    "","","Howrah","vi. Viral Hepatitis A &E","85","0","26/12/13","27/12/13","Under surveillance","..."

::

    >>> camelot.read_pdf('copy_text.pdf', mesh=True, copy_text=['v'])

.. csv-table::

    "Sl. No.","Name of State/UT","Name of District","Disease/ Illness","No. of Cases","No. of Deaths","Date of start of outbreak","Date of reporting","Current Status","..."
    "1","Kerala","Kollam","i.  Food Poisoning","19","0","31/12/13","03/01/14","Under control","..."
    "2","Maharashtra","Beed","i.  Dengue & Chikungunya   i","11","0","03/01/14","04/01/14","Under control","..."
    "3","Odisha","Kalahandi","iii. Food Poisoning","42","0","02/01/14","03/01/14","Under control","..."
    "4","West Bengal","West Medinipur","iv. Acute Diarrhoeal Disease","145","0","04/01/14","05/01/14","Under control","..."
    "4","West Bengal","Birbhum","v.  Food Poisoning","199","0","31/12/13","31/12/13","Under control","..."
    "4","West Bengal","Howrah","vi. Viral Hepatitis A &E","85","0","26/12/13","27/12/13","Under surveillance","..."