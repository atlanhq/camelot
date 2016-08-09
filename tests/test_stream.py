# coding: utf8
import os

from nose.tools import assert_equal

from camelot.pdf import Pdf
from camelot.stream import Stream


testdir = os.path.dirname(os.path.abspath(__file__))


def test_stream_basic():

    data = [
        ["Clave","Nombre Entidad","Clave","Nombre Municipio","Clave","Nombre Localidad"],
        ["Entidad","","Municipio","","Localidad",""],
        ["01","Aguascalientes","001","Aguascalientes","0094","Granja Adelita"],
        ["01","Aguascalientes","001","Aguascalientes","0096","Agua Azul"],
        ["01","Aguascalientes","001","Aguascalientes","0100","Rancho Alegre"],
        ["01","Aguascalientes","001","Aguascalientes","0102","Los Arbolitos [Rancho]"],
        ["01","Aguascalientes","001","Aguascalientes","0104","Ardillas de Abajo (Las Ardillas)"],
        ["01","Aguascalientes","001","Aguascalientes","0106","Arellano"],
        ["01","Aguascalientes","001","Aguascalientes","0112","Bajío los Vázquez"],
        ["01","Aguascalientes","001","Aguascalientes","0113","Bajío de Montoro"],
        ["01","Aguascalientes","001","Aguascalientes","0114","Residencial San Nicolás [Baños la Cantera]"],
        ["01","Aguascalientes","001","Aguascalientes","0120","Buenavista de Peñuelas"],
        ["01","Aguascalientes","001","Aguascalientes","0121","Cabecita 3 Marías (Rancho Nuevo)"],
        ["01","Aguascalientes","001","Aguascalientes","0125","Cañada Grande de Cotorina"],
        ["01","Aguascalientes","001","Aguascalientes","0126","Cañada Honda [Estación]"],
        ["01","Aguascalientes","001","Aguascalientes","0127","Los Caños"],
        ["01","Aguascalientes","001","Aguascalientes","0128","El Cariñán"],
        ["01","Aguascalientes","001","Aguascalientes","0129","El Carmen [Granja]"],
        ["01","Aguascalientes","001","Aguascalientes","0135","El Cedazo (Cedazo de San Antonio)"],
        ["01","Aguascalientes","001","Aguascalientes","0138","Centro de Arriba (El Taray)"],
        ["01","Aguascalientes","001","Aguascalientes","0139","Cieneguilla (La Lumbrera)"],
        ["01","Aguascalientes","001","Aguascalientes","0141","Cobos"],
        ["01","Aguascalientes","001","Aguascalientes","0144","El Colorado (El Soyatal)"],
        ["01","Aguascalientes","001","Aguascalientes","0146","El Conejal"],
        ["01","Aguascalientes","001","Aguascalientes","0157","Cotorina de Abajo"],
        ["01","Aguascalientes","001","Aguascalientes","0162","Coyotes"],
        ["01","Aguascalientes","001","Aguascalientes","0166","La Huerta (La Cruz)"],
        ["01","Aguascalientes","001","Aguascalientes","0170","Cuauhtémoc (Las Palomas)"],
        ["01","Aguascalientes","001","Aguascalientes","0171","Los Cuervos (Los Ojos de Agua)"],
        ["01","Aguascalientes","001","Aguascalientes","0172","San José [Granja]"],
        ["01","Aguascalientes","001","Aguascalientes","0176","La Chiripa"],
        ["01","Aguascalientes","001","Aguascalientes","0182","Dolores"],
        ["01","Aguascalientes","001","Aguascalientes","0183","Los Dolores"],
        ["01","Aguascalientes","001","Aguascalientes","0190","El Duraznillo"],
        ["01","Aguascalientes","001","Aguascalientes","0191","Los Durón"],
        ["01","Aguascalientes","001","Aguascalientes","0197","La Escondida"],
        ["01","Aguascalientes","001","Aguascalientes","0201","Brande Vin [Bodegas]"],
        ["01","Aguascalientes","001","Aguascalientes","0207","Valle Redondo"],
        ["01","Aguascalientes","001","Aguascalientes","0209","La Fortuna"],
        ["01","Aguascalientes","001","Aguascalientes","0212","Lomas del Gachupín"],
        ["01","Aguascalientes","001","Aguascalientes","0213","El Carmen (Gallinas Güeras) [Rancho]"],
        ["01","Aguascalientes","001","Aguascalientes","0216","La Gloria"],
        ["01","Aguascalientes","001","Aguascalientes","0226","Hacienda Nueva"],
    ]

    pdfname = os.path.join(testdir, 'mexican_towns.pdf')
    extractor = Stream(Pdf(pdfname, pagenos=[{'start': 1, 'end': 1}],
                           clean=True))
    tables = extractor.get_tables()
    assert_equal(tables['page-1'][0], data)


def test_stream_ncolumns():

    data = [
        ["Bhandara - Key Indicators","","","",""],
        ["","DLHS-4 (2012-13)","","DLHS-3 (2007-08)",""],
        ["Indicators","TOTAL","RURAL","TOTAL","RURAL"],
        ["Reported Prevalence of Morbidity","","","",""],
        ["Any Injury .....................................................................................................................................","1.9","2.1","",""],
        ["Acute Illness .................................................................................................................................","4.5","5.6","",""],
        ["Chronic Illness ..............................................................................................................................","5.1","4.1","",""],
        ["Reported Prevalence of Chronic Illness during last one year (%)","","","",""],
        ["Disease of respiratory system ......................................................................................................","11.7","15.0","",""],
        ["Disease of cardiovascular system ................................................................................................","8.9","9.3","",""],
        ["Persons suffering from tuberculosis .............................................................................................","2.2","1.5","",""],
        ["Anaemia Status by Haemoglobin Level14 (%)","","","",""],
        ["Children (6-59 months) having anaemia ......................................................................................","68.5","71.9","",""],
        ["Children (6-59 months) having severe anaemia ..........................................................................","6.7","9.4","",""],
        ["Children (6-9 Years) having anaemia - Male ................................................................................","67.1","71.4","",""],
        ["Children (6-9 Years) having severe anaemia - Male ....................................................................","4.4","2.4","",""],
        ["Children (6-9 Years) having anaemia - Female ...........................................................................","52.4","48.8","",""],
        ["Children (6-9 Years) having severe anaemia - Female ................................................................","1.2","0.0","",""],
        ["Children (6-14 years) having  anaemia - Male .............................................................................","50.8","62.5","",""],
        ["Children (6-14 years) having severe anaemia - Male ..................................................................","3.7","3.6","",""],
        ["Children (6-14 years) having  anaemia - Female .........................................................................","48.3","50.0","",""],
        ["Children (6-14 years) having severe anaemia - Female ..............................................................","4.3","6.1","",""],
        ["Children (10-19 Years15) having anaemia - Male .........................................................................","37.9","51.2","",""],
        ["Children (10-19 Years15) having severe anaemia - Male .............................................................","3.5","4.0","",""],
        ["Children (10-19 Years15) having anaemia - Female .....................................................................","46.6","52.1","",""],
        ["Children (10-19 Years15) having severe anaemia - Female .........................................................","6.4","6.5","",""],
        ["Adolescents (15-19 years) having  anaemia ................................................................................","39.4","46.5","",""],
        ["Adolescents (15-19 years) having severe anaemia .....................................................................","5.4","5.1","",""],
        ["Pregnant women (15-49 aged) having anaemia ..........................................................................","48.8","51.5","",""],
        ["Pregnant women (15-49 aged) having severe anaemia ..............................................................","7.1","8.8","",""],
        ["Women (15-49 aged) having anaemia .........................................................................................","45.2","51.7","",""],
        ["Women (15-49 aged) having severe anaemia .............................................................................","4.8","5.9","",""],
        ["Persons (20 years and above) having anaemia ...........................................................................","37.8","42.1","",""],
        ["Persons (20 years and above) having Severe anaemia ..............................................................","4.6","4.8","",""],
        ["Blood Sugar Level (age 18 years and above) (%)","","","",""],
        ["Blood Sugar Level >140 mg/dl (high) ...........................................................................................","12.9","11.1","",""],
        ["Blood Sugar Level >160 mg/dl (very high) ...................................................................................","7.0","5.1","",""],
        ["Hypertension (age 18 years and above) (%)","","","",""],
        ["Above Normal Range (Systolic >140 mm of Hg & Diastolic >90 mm of Hg )  ..............................","23.8","22.8","",""],
        ["Moderately High (Systolic >160 mm of Hg & Diastolic >100 mm of Hg ) .....................................","8.2","7.1","",""],
        ["Very High (Systolic >180 mm of Hg & Diastolic >110 mm of Hg ) ...............................................","3.7","3.1","",""],
        ["14 Any anaemia below 11g/dl, severe anaemia below 7g/dl. 15 Excluding age group 19 years","","","",""],
        ["Chronic Illness :Any person with symptoms persisting for longer than one month is defined as suffering from chronic illness","","","",""],
        ["","4","","",""]
    ]
    pdfname = os.path.join(testdir, 'missing_values.pdf')
    extractor = Stream(Pdf(pdfname, char_margin=1.0, clean=True),
                       ncolumns=5)
    tables = extractor.get_tables()
    assert_equal(tables['page-1'][0], data)


def test_stream_columns():

    data = [
        ["Clave","Nombre Entidad","Clave","Nombre Municipio","Clave","Nombre Localidad"],
        ["Entidad","","Municipio","","Localidad",""],
        ["01","Aguascalientes","001","Aguascalientes","0094","Granja Adelita"],
        ["01","Aguascalientes","001","Aguascalientes","0096","Agua Azul"],
        ["01","Aguascalientes","001","Aguascalientes","0100","Rancho Alegre"],
        ["01","Aguascalientes","001","Aguascalientes","0102","Los Arbolitos [Rancho]"],
        ["01","Aguascalientes","001","Aguascalientes","0104","Ardillas de Abajo (Las Ardillas)"],
        ["01","Aguascalientes","001","Aguascalientes","0106","Arellano"],
        ["01","Aguascalientes","001","Aguascalientes","0112","Bajío los Vázquez"],
        ["01","Aguascalientes","001","Aguascalientes","0113","Bajío de Montoro"],
        ["01","Aguascalientes","001","Aguascalientes","0114","Residencial San Nicolás [Baños la Cantera]"],
        ["01","Aguascalientes","001","Aguascalientes","0120","Buenavista de Peñuelas"],
        ["01","Aguascalientes","001","Aguascalientes","0121","Cabecita 3 Marías (Rancho Nuevo)"],
        ["01","Aguascalientes","001","Aguascalientes","0125","Cañada Grande de Cotorina"],
        ["01","Aguascalientes","001","Aguascalientes","0126","Cañada Honda [Estación]"],
        ["01","Aguascalientes","001","Aguascalientes","0127","Los Caños"],
        ["01","Aguascalientes","001","Aguascalientes","0128","El Cariñán"],
        ["01","Aguascalientes","001","Aguascalientes","0129","El Carmen [Granja]"],
        ["01","Aguascalientes","001","Aguascalientes","0135","El Cedazo (Cedazo de San Antonio)"],
        ["01","Aguascalientes","001","Aguascalientes","0138","Centro de Arriba (El Taray)"],
        ["01","Aguascalientes","001","Aguascalientes","0139","Cieneguilla (La Lumbrera)"],
        ["01","Aguascalientes","001","Aguascalientes","0141","Cobos"],
        ["01","Aguascalientes","001","Aguascalientes","0144","El Colorado (El Soyatal)"],
        ["01","Aguascalientes","001","Aguascalientes","0146","El Conejal"],
        ["01","Aguascalientes","001","Aguascalientes","0157","Cotorina de Abajo"],
        ["01","Aguascalientes","001","Aguascalientes","0162","Coyotes"],
        ["01","Aguascalientes","001","Aguascalientes","0166","La Huerta (La Cruz)"],
        ["01","Aguascalientes","001","Aguascalientes","0170","Cuauhtémoc (Las Palomas)"],
        ["01","Aguascalientes","001","Aguascalientes","0171","Los Cuervos (Los Ojos de Agua)"],
        ["01","Aguascalientes","001","Aguascalientes","0172","San José [Granja]"],
        ["01","Aguascalientes","001","Aguascalientes","0176","La Chiripa"],
        ["01","Aguascalientes","001","Aguascalientes","0182","Dolores"],
        ["01","Aguascalientes","001","Aguascalientes","0183","Los Dolores"],
        ["01","Aguascalientes","001","Aguascalientes","0190","El Duraznillo"],
        ["01","Aguascalientes","001","Aguascalientes","0191","Los Durón"],
        ["01","Aguascalientes","001","Aguascalientes","0197","La Escondida"],
        ["01","Aguascalientes","001","Aguascalientes","0201","Brande Vin [Bodegas]"],
        ["01","Aguascalientes","001","Aguascalientes","0207","Valle Redondo"],
        ["01","Aguascalientes","001","Aguascalientes","0209","La Fortuna"],
        ["01","Aguascalientes","001","Aguascalientes","0212","Lomas del Gachupín"],
        ["01","Aguascalientes","001","Aguascalientes","0213","El Carmen (Gallinas Güeras) [Rancho]"],
        ["01","Aguascalientes","001","Aguascalientes","0216","La Gloria"],
        ["01","Aguascalientes","001","Aguascalientes","0226","Hacienda Nueva"],
    ]
    pdfname = os.path.join(testdir, 'mexican_towns.pdf')
    extractor = Stream(Pdf(pdfname, clean=True),
                       columns='28,67,180,230,425,475,700')
    tables = extractor.get_tables()
    assert_equal(tables['page-1'][0], data)