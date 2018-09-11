.. _lattice:

Lattice
=======

Lattice method is designed to work on pdf files which have tables with well-defined grids. It looks for lines on a page to form a table.

Lattice uses OpenCV to apply a set of morphological transformations (erosion and dilation) to find horizontal and vertical line segments in a pdf page after converting it to an image using imagemagick.

.. note:: Currently, Lattice only works on pdf files that contain text. However, we plan to add `OCR support`_ in the future.

.. _OCR support: https://github.com/socialcopsdev/camelot/issues/14

Let's see how Lattice processes this pdf, step by step.

Line segments are detected in the first step.

.. .. _this: insert link for us-030.pdf

.. image:: ../_static/user/line.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

The detected line segments are overlapped by `and` ing their pixel intensities to find intersections.

.. image:: ../_static/user/intersection.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

The detected line segments are overlapped again, this time by `or` ing their pixel intensities and outermost contours are computed to identify potential table boundaries. This helps Lattice in detecting more than one table on a single page.

.. image:: ../_static/user/contour.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

Since dimensions of a pdf and its image vary; table contours, intersections and segments are scaled and translated to the pdf's coordinate space. A representation of the table is then created using these scaled coordinates.

.. image:: ../_static/user/table.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

Spanning cells are then detected using the line segments and intersections.

.. image:: ../_static/user/table_span.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

Finally, the characters found on the page are assigned to cells based on their x,y coordinates.

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

Scale
-----

The scale parameter is used to determine the length of the structuring element used for morphological transformations. The length of vertical and horizontal structuring elements are found by dividing the image's height and width respectively, by `scale`. Large `scale` will lead to a smaller structuring element, which means that smaller lines will be detected. The default value for scale is 15.

Let's consider this pdf file.

.. .. _this: insert link for row_span_1.pdf

.. image:: ../_static/user/scale_1.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

Clearly, it couldn't detected those small lines in the lower left part. Therefore, we need to increase the value of scale. Let's try a value of 40.

.. image:: ../_static/user/scale_2.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

Voila! It detected the smaller lines.

Fill
----

In the file used above, you can see that some cells spanned a lot of rows, `fill` just copies the same value to all rows/columns of a spanning cell. You can apply fill horizontally, vertically or both. Let us fill the output for the file we used above, vertically.

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.lattice import Lattice

    >>> manager = Pdf(Lattice(fill=['v'], scale=40), 'row_span_1.pdf')
    >>> tables = manager.extract()
    >>> print tables['page-1']['table-1']['data']

.. csv-table::
   :header: "Plan Type","County","Plan  Name","Totals"

   "GMC","Sacramento","Anthem Blue Cross","164,380"
   "GMC","Sacramento","Health Net","126,547"
   "GMC","Sacramento","Kaiser Foundation","74,620"
   "GMC","Sacramento","Molina Healthcare","59,989"
   "GMC","San Diego","Care 1st Health Plan","71,831"
   "GMC","San Diego","Community...","264,639"
   "GMC","San Diego","Health Net","72,404"
   "GMC","San Diego","Kaiser","50,415"
   "GMC","San Diego","Molina Healthcare","206,430"
   "GMC","Total GMC...","","1,091,255"
   "COHS","Marin","Partnership Health...","36,006"
   "COHS","Mendocino","Partnership Health...","37,243"
   "COHS","Napa","Partnership Health...","28,398"
   "COHS","Solano","Partnership Health...","113,220"
   "COHS","Sonoma","Partnership Health...","112,271"
   "COHS","Yolo","Partnership Health...","52,674"
   "COHS","Del Norte","Partnership Health...","11,242"
   "COHS","Humboldt","Partnership Health...","49,911"
   "COHS","Lake","Partnership Health...","29,149"
   "COHS","Lassen","Partnership Health...","7,360"
   "COHS","Modoc","Partnership Health...","2,940"
   "COHS","Shasta","Partnership Health...","61,763"
   "COHS","Siskiyou","Partnership Health...","16,715"
   "COHS","Trinity","Partnership Health...","4,542"
   "COHS","Merced","Central California...","123,907"
   "COHS","Monterey","Central California...","147,397"
   "COHS","Santa Cruz","Central California...","69,458"
   "COHS","Santa Barbara","CenCal","117,609"
   "COHS","San Luis Obispo","CenCal","55,761"
   "COHS","Orange","CalOptima","783,079"
   "COHS","San Mateo","Health Plan...","113,202"
   "COHS","Ventura","Gold Coast...","202,217"
   "COHS","Total COHS...","","2,176,064"
   "Subtotal for...","","","10,132,022"
   "PCCM","Los Angeles","AIDS Healthcare...","828"
   "PCCM","San Francisco","Family Mosaic","25"
   "PCCM","Total PHP...","","853"
   "All Models...","","","10,132,875"
   "Source: Data...","","",""

Invert
------

To find line segments, Lattice needs the lines of the pdf file to be in foreground. So, if you encounter a file like this, just set invert to True.

.. .. _this: insert link for lines_in_background_1.pdf

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.lattice import Lattice

    >>> manager = Pdf(Lattice(invert=True), 'lines_in_background_1.pdf')
    >>> tables = manager.extract()
    >>> print tables['page-1']['table-1']['data']

.. csv-table::
   :header: "State","Date","Halt stations","Halt days","Persons directly reached(in lakh)","Persons trained","Persons counseled","Persons testedfor HIV"

   "Delhi","1.12.2009","8","17","1.29","3,665","2,409","1,000"
   "Rajasthan","2.12.2009 to 19.12.2009","","","","","",""
   "Gujarat","20.12.2009 to 3.1.2010","6","13","6.03","3,810","2,317","1,453"
   "Maharashtra","4.01.2010 to 1.2.2010","13","26","1.27","5,680","9,027","4,153"
   "Karnataka","2.2.2010 to 22.2.2010","11","19","1.80","5,741","3,658","3,183"
   "Kerala","23.2.2010 to 11.3.2010","9","17","1.42","3,559","2,173","855"
   "Total","","47","92","11.81","22,455","19,584","10,644"

Lattice can also parse pdf files with tables like these that are rotated clockwise/anti-clockwise by 90 degrees.

.. .. _these: insert link for left_rotated_table.pdf

You can call Lattice with debug={'line', 'intersection', 'contour', 'table'}, and call `debug_plot()` which will generate an image like the ones on this page, with the help of which you can modify various parameters. See :doc:`API doc <api>` for more information.
