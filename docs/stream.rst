.. _stream:

======
Stream
======

Stream method is the complete opposite of Lattice and works on pdf files which have text placed uniformly apart across rows to simulate a table. It looks for spaces between text to form a table representation.

Stream builds on top of PDFMiner's functionality of grouping characters on a page into words and sentences. After getting these words, it groups them into rows based on their y-coordinates and tries to guess the number of columns a pdf table might have by calculating the mode of the number of words in each row. Additionally, the user can specify the number of columns or column x-coordinates.

Let's run it on this pdf.

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.stream import Stream

    >>> manager = Pdf(Stream(), 'eu-027.pdf')
    >>> tables = manager.extract()
    >>> print tables['page-1']['table-1']['data']

.. .. _this: insert link for eu-027.pdf

.. csv-table::

   "C","Appendix C:...","","",""
   "","Table C1:...","","",""
   "","This table...","","",""
   "Variable","Mean","Std. Dev.","Min","Max"
   "Age","50.8","15.9","21","90"
   "Men","0.47","0.50","0","1"
   "East","0.28","0.45","0","1"
   "Rural","0.15","0.36","0","1"
   "Married","0.57","0.50","0","1"
   "Single","0.21","0.40","0","1"
   "Divorced","0.13","0.33","0","1"
   "Widowed","0.08","0.26","0","1"
   "Separated","0.03","0.16","0","1"
   "Partner","0.65","0.48","0","1"
   "Employed","0.55","0.50","0","1"
   "Fulltime","0.34","0.47","0","1"
   "Parttime","0.20","0.40","0","1"
   "Unemployed","0.08","0.28","0","1"
   "Homemaker","0.19","0.40","0","1"
   "Retired","0.28","0.45","0","1"
   "Household size","2.43","1.22","1","9"
   "Households...","0.37","0.48","0","1"
   "Number of...","1.67","1.38","0","8"
   "Lower...","0.08","0.27","0","1"
   "Upper...","0.60","0.49","0","1"
   "Post...","0.12","0.33","0","1"
   "First...","0.17","0.38","0","1"
   "Other...","0.03","0.17","0","1"
   "Household...","2,127","1,389","22","22,500"
   "Gross...","187,281","384,198","0","7,720,000"
   "Gross...","38,855","114,128","0","2,870,000"
   "","Source:...","","",""
   "","","","","ECB"
   "","","","","Working..."
   "","","","","Febuary..."

We can also specify the column x-coordinates. We need to call Stream with debug=True and use matplotlib's interface to note down the column x-coordinates we need. Let's try it on this pdf file.

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.stream import Stream

    >>> manager = Pdf(Stream(debug=True), 'mexican_towns.pdf'), debug=True
    >>> manager.debug_plot()

.. image:: assets/columns.png
   :height: 674
   :width: 1366
   :scale: 50%
   :align: left

After getting the x-coordinates, we just need to pass them to Stream, like this.

::

    >>> from camelot.pdf import Pdf
    >>> from camelot.stream import Stream

    >>> manager = Pdf(Stream(columns=['28,67,180,230,425,475,700']), 'mexican_towns.pdf')
    >>> tables = manager.extract()
    >>> print tables['page-1']['table-1']['data']

.. csv-table::

   "Clave","","Clave","","Clave",""
   "","Nombre Entidad","","Nombre Municipio","","Nombre Localidad"
   "Entidad","","Municipio","","Localidad",""
   "01","Aguascalientes","001","Aguascalientes","0094","Granja Adelita"
   "01","Aguascalientes","001","Aguascalientes","0096","Agua Azul"
   "01","Aguascalientes","001","Aguascalientes","0100","Rancho Alegre"
   "01","Aguascalientes","001","Aguascalientes","0102","Los Arbolitos [Rancho]"
   "01","Aguascalientes","001","Aguascalientes","0104","Ardillas de Abajo (Las Ardillas)"
   "01","Aguascalientes","001","Aguascalientes","0106","Arellano"
   "01","Aguascalientes","001","Aguascalientes","0112","Bajío los Vázquez"
   "01","Aguascalientes","001","Aguascalientes","0113","Bajío de Montoro"
   "01","Aguascalientes","001","Aguascalientes","0114","Residencial San Nicolás [Baños la Cantera]"
   "01","Aguascalientes","001","Aguascalientes","0120","Buenavista de Peñuelas"
   "01","Aguascalientes","001","Aguascalientes","0121","Cabecita 3 Marías (Rancho Nuevo)"
   "01","Aguascalientes","001","Aguascalientes","0125","Cañada Grande de Cotorina"
   "01","Aguascalientes","001","Aguascalientes","0126","Cañada Honda [Estación]"
   "01","Aguascalientes","001","Aguascalientes","0127","Los Caños"
   "01","Aguascalientes","001","Aguascalientes","0128","El Cariñán"
   "01","Aguascalientes","001","Aguascalientes","0129","El Carmen [Granja]"
   "01","Aguascalientes","001","Aguascalientes","0135","El Cedazo (Cedazo de San Antonio)"
   "01","Aguascalientes","001","Aguascalientes","0138","Centro de Arriba (El Taray)"
   "01","Aguascalientes","001","Aguascalientes","0139","Cieneguilla (La Lumbrera)"
   "01","Aguascalientes","001","Aguascalientes","0141","Cobos"
   "01","Aguascalientes","001","Aguascalientes","0144","El Colorado (El Soyatal)"
   "01","Aguascalientes","001","Aguascalientes","0146","El Conejal"
   "01","Aguascalientes","001","Aguascalientes","0157","Cotorina de Abajo"
   "01","Aguascalientes","001","Aguascalientes","0162","Coyotes"
   "01","Aguascalientes","001","Aguascalientes","0166","La Huerta (La Cruz)"
   "01","Aguascalientes","001","Aguascalientes","0170","Cuauhtémoc (Las Palomas)"
   "01","Aguascalientes","001","Aguascalientes","0171","Los Cuervos (Los Ojos de Agua)"
   "01","Aguascalientes","001","Aguascalientes","0172","San José [Granja]"
   "01","Aguascalientes","001","Aguascalientes","0176","La Chiripa"
   "01","Aguascalientes","001","Aguascalientes","0182","Dolores"
   "01","Aguascalientes","001","Aguascalientes","0183","Los Dolores"
   "01","Aguascalientes","001","Aguascalientes","0190","El Duraznillo"
   "01","Aguascalientes","001","Aguascalientes","0191","Los Durón"
   "01","Aguascalientes","001","Aguascalientes","0197","La Escondida"
   "01","Aguascalientes","001","Aguascalientes","0201","Brande Vin [Bodegas]"
   "01","Aguascalientes","001","Aguascalientes","0207","Valle Redondo"
   "01","Aguascalientes","001","Aguascalientes","0209","La Fortuna"
   "01","Aguascalientes","001","Aguascalientes","0212","Lomas del Gachupín"
   "01","Aguascalientes","001","Aguascalientes","0213","El Carmen (Gallinas Güeras) [Rancho]"
   "01","Aguascalientes","001","Aguascalientes","0216","La Gloria"
