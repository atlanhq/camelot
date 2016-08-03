# coding: utf8
import os

from nose.tools import assert_equal

from camelot.pdf import Pdf
from camelot.stream import Stream


testdir = os.path.dirname(os.path.abspath(__file__))


def test_stream_basic():

    data = [
        ["","","","",""],
        ["C Appendix C: Summary Statistics","","","",""],
        ["","Table C1: Summary Statistics","","",""],
        ["","This table contains summary statistics for 2,012 respondents in SAVE 2009.","","",""],
        ["Variable","Mean","Std. Dev. Min","","Max"],
        ["Age","50.8","15.9","21","90"],
        ["Men","0.47","0.50","0","1"],
        ["East","0.28","0.45","0","1"],
        ["Rural","0.15","0.36","0","1"],
        ["Married","0.57","0.50","0","1"],
        ["Single","0.21","0.40","0","1"],
        ["Divorced","0.13","0.33","0","1"],
        ["Widowed","0.08","0.26","0","1"],
        ["Separated","0.03","0.16","0","1"],
        ["Partner","0.65","0.48","0","1"],
        ["Employed","0.55","0.50","0","1"],
        ["Fulltime","0.34","0.47","0","1"],
        ["Parttime","0.20","0.40","0","1"],
        ["Unemployed","0.08","0.28","0","1"],
        ["Homemaker","0.19","0.40","0","1"],
        ["Retired","0.28","0.45","0","1"],
        ["Household size","2.43","1.22","1","9"],
        ["Households with children","0.37","0.48","0","1"],
        ["Number of children","1.67","1.38","0","8"],
        ["Lower secondary education","0.08","0.27","0","1"],
        ["Upper secondary education","0.60","0.49","0","1"],
        ["Post secondary, non tert. education","0.12","0.33","0","1"],
        ["First stage tertiary education","0.17","0.38","0","1"],
        ["Other education","0.03","0.17","0","1"],
        ["Household income (Euro/month)","2,127","1,389","22","22,500"],
        ["Gross wealth - end of 2007 (Euro)","187,281","384,198","0","7,720,000"],
        ["Gross ﬁnancial wealth - end of 2007 (Euro)","38,855","114,128","0","2,870,000"],
        ["","Source: SAVE 2008 and 2009, data is weighted and imputed.","","",""],
        ["","","","","ECB"],
        ["","","","","Working Paper Series No 1299"],
        ["","","","","Febuary 2011"]
    ]

    pdfname = os.path.join(testdir,
        "tabula_test_pdfs/icdar2013-dataset/competition-dataset-eu/eu-027.pdf")
    extractor = Stream(Pdf(pdfname, pagenos=[{'start': 3, 'end': 3}],
                           clean=True))
    tables = extractor.get_tables()
    assert_equal(tables['pg-3'][0], data)


def test_stream_ncolumns():

    data = [
        ["","","","",""],
        ["","Bhandara - Key Indicators","","",""],
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
        ["","Chronic Illness :Any person with symptoms persisting for longer than one month is defined as suffering from chronic illness","","",""]
    ]
    pdfname = os.path.join(testdir, 'missing_values.pdf')
    extractor = Stream(Pdf(pdfname, char_margin=1.0, clean=True),
                       ncolumns=5)
    tables = extractor.get_tables()
    assert_equal(tables['pg-1'][0], data)


def test_stream_columns():

    data = [
        ["","","","","",""],
        ["Clave","","Clave","","Clave",""],
        ["","Nombre Entidad","","Nombre Municipio","","Nombre Localidad"],
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
        ["01","Aguascalientes","001","Aguascalientes","0216","La Gloria"]
    ]
    pdfname = os.path.join(testdir, 'mexican_towns.pdf')
    extractor = Stream(Pdf(pdfname, clean=True),
                       columns='28,67,180,230,425,475,700')
    tables = extractor.get_tables()
    assert_equal(tables['pg-1'][0], data)