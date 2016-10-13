# coding: utf8
import os

from nose.tools import assert_equal

from camelot.pdf import Pdf
from camelot.stream import Stream


testdir = os.path.dirname(os.path.abspath(__file__))


def test_stream_basic():

    data = [
        ["", "Table 6.", ""],
        ["", "U.S. Production, Imports, Exports, and Net Supply of Conventional Pesticides", ""],
        ["", "at Producer Level, 1994/95 Estimates.", ""],
        ["", "Active Ingredient", "Sales Value"],
        ["", "(in billions of lbs.)", "(in billions of dollars)"],
        ["Category", "1994/95", "1994/95"],
        ["U.S. Production", "1.3", "7.0"],
        ["U.S. Imports", "0.2", "2.2"],
        ["Total Supply", "1.5", "9.2"],
        ["U.S. Exports", "0.5", "2.6"],
        ["Net Supply/Usage", "1.0", "6.6"],
        ["SOURCE:", "EPA  estimates  based  on  ACPA  Surveys,  Department  of  Commerce  Publications,  tabulations  and  other", ""],
        ["sources.", "", ""],
        ["16\xe2\x80\x9494/95 Pesticides Industry Sales And Usage", "", ""]
    ]

    pdfname = os.path.join(testdir, "tabula_test_pdfs/us-024.pdf")
    manager = Pdf(Stream(), pdfname, pagenos=[{"start": 1, "end": 1}],
        clean=True)
    tables = manager.extract()
    assert_equal(tables["page-1"]["table-1"]["data"], data)


def test_stream_missing_value():

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
        ["4","","","",""]
    ]
    pdfname = os.path.join(testdir, "missing_values.pdf")
    manager = Pdf(Stream(flag_size=False), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables["page-1"]["table-1"]["data"], data)


def test_stream_single_table_area():

    data = [
        ["","One Withholding"],
        ["Payroll Period","Allowance"],
        ["Weekly","$71.15"],
        ["Biweekly","142.31"],
        ["Semimonthly","154.17"],
        ["Monthly","308.33"],
        ["Quarterly","925.00"],
        ["Semiannually","1,850.00"],
        ["Annually","3,700.00"],
        ["Daily or Miscellaneous","14.23"],
        ["(each day of the payroll period)",""]
    ]
    pdfname = os.path.join(testdir, "tabula_test_pdfs/us-007.pdf")
    manager = Pdf(Stream(table_area=["320,500,573,335"]),
                  pdfname, pagenos=[{"start": 1, "end": 1}], clean=True)
    tables = manager.extract()
    assert_equal(tables["page-1"]["table-1"]["data"], data)


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
    pdfname = os.path.join(testdir, "mexican_towns.pdf")
    manager = Pdf(Stream(columns=["67,180,230,425,475"], ytol=[10]), pdfname,
        clean=True)
    tables = manager.extract()
    assert_equal(tables["page-1"]["table-1"]["data"], data)


def test_stream_table_rotation():

    data = [
        ["","","Table 21  Current use of contraception by background characteristics—Continued","","","","","","","","","","","","","","",""],
        ["","","","","","","Modern method","","","","","","","Traditional method","","","",""],
        ["","","","Any","","","","","","","Other","Any","","","","Not","","Number"],
        ["","","Any","modern","Female","Male","","","","Condom/","modern","traditional","","With-","Folk","currently","","of"],
        ["","Background characteristic","method","method","sterilization","sterilization","Pill","IUD","Injectables","Nirodh","method","method","Rhythm","drawal","method","using","Total","women"],
        ["","Caste/tribe","","","","","","","","","","","","","","","",""],
        ["","Scheduled caste","74.8","55.8","42.9","0.9","9.7","0.0","0.2","2.2","0.0","19.0","11.2","7.4","0.4","25.2","100.0","1,363"],
        ["","Scheduled tribe","59.3","39.0","26.8","0.6","6.4","0.6","1.2","3.5","0.0","20.3","10.4","5.8","4.1","40.7","100.0","256"],
        ["","Other backward class","71.4","51.1","34.9","0.0","8.6","1.4","0.0","6.2","0.0","20.4","12.6","7.8","0.0","28.6","100.0","211"],
        ["","Other","71.1","48.8","28.2","0.8","13.3","0.9","0.3","5.2","0.1","22.3","12.9","9.1","0.3","28.9","100.0","3,319"],
        ["","Wealth index","","","","","","","","","","","","","","","",""],
        ["","Lowest","64.5","48.6","34.3","0.5","10.5","0.6","0.7","2.0","0.0","15.9","9.9","4.6","1.4","35.5","100.0","1,258"],
        ["","Second","68.5","50.4","36.2","1.1","11.4","0.5","0.1","1.1","0.0","18.1","11.2","6.7","0.2","31.5","100.0","1,317"],
        ["","Middle","75.5","52.8","33.6","0.6","14.2","0.4","0.5","3.4","0.1","22.7","13.4","8.9","0.4","24.5","100.0","1,018"],
        ["","Fourth","73.9","52.3","32.0","0.5","12.5","0.6","0.2","6.3","0.2","21.6","11.5","9.9","0.2","26.1","100.0","908"],
        ["","Highest","78.3","44.4","19.5","1.0","9.7","1.4","0.0","12.7","0.0","33.8","18.2","15.6","0.0","21.7","100.0","733"],
        ["","Number of living children","","","","","","","","","","","","","","","",""],
        ["","No children","25.1","7.6","0.3","0.5","2.0","0.0","0.0","4.8","0.0","17.5","9.0","8.5","0.0","74.9","100.0","563"],
        ["","1 child","66.5","32.1","3.7","0.7","20.1","0.7","0.1","6.9","0.0","34.3","18.9","15.2","0.3","33.5","100.0","1,190"],
        ["","1 son","66.8","33.2","4.1","0.7","21.1","0.5","0.3","6.6","0.0","33.5","21.2","12.3","0.0","33.2","100.0","672"],
        ["","No sons","66.1","30.7","3.1","0.6","18.8","0.8","0.0","7.3","0.0","35.4","15.8","19.0","0.6","33.9","100.0","517"],
        ["","2 children","81.6","60.5","41.8","0.9","11.6","0.8","0.3","4.8","0.2","21.1","12.2","8.3","0.6","18.4","100.0","1,576"],
        ["","1 or more sons","83.7","64.2","46.4","0.9","10.8","0.8","0.4","4.8","0.1","19.5","11.1","7.6","0.7","16.3","100.0","1,268"],
        ["","No sons","73.2","45.5","23.2","1.0","15.1","0.9","0.0","4.8","0.5","27.7","16.8","11.0","0.0","26.8","100.0","308"],
        ["","3 children","83.9","71.2","57.7","0.8","9.8","0.6","0.5","1.8","0.0","12.7","8.7","3.3","0.8","16.1","100.0","961"],
        ["","1 or more sons","85.0","73.2","60.3","0.9","9.4","0.5","0.5","1.6","0.0","11.8","8.1","3.0","0.7","15.0","100.0","860"],
        ["","No sons","74.7","53.8","35.3","0.0","13.7","1.6","0.0","3.2","0.0","20.9","13.4","6.1","1.5","25.3","100.0","101"],
        ["","4+ children","74.3","58.1","45.1","0.6","8.7","0.6","0.7","2.4","0.0","16.1","9.9","5.4","0.8","25.7","100.0","944"],
        ["","1 or more sons","73.9","58.2","46.0","0.7","8.3","0.7","0.7","1.9","0.0","15.7","9.4","5.5","0.8","26.1","100.0","901"],
        ["","No sons","(82.1)","(57.3)","(25.6)","(0.0)","(17.8)","(0.0)","(0.0)","(13.9)","(0.0)","(24.8)","(21.3)","(3.5)","(0.0)","(17.9)","100.0","43"],
        ["","Total","71.2","49.9","32.2","0.7","11.7","0.6","0.3","4.3","0.1","21.3","12.3","8.4","0.5","28.8","100.0","5,234"],
        ["","NFHS-2 (1998-99)","66.6","47.3","32.0","1.8","9.2","1.4","na","2.9","na","na","8.7","9.8","na","33.4","100.0","4,116"],
        ["","NFHS-1 (1992-93)","57.7","37.6","26.5","4.3","3.6","1.3","0.1","1.9","na","na","11.3","8.3","na","42.3","100.0","3,970"],
        ["","","Note: If more than one method is used, only the most effective method is considered in this tabulation. Total includes women for whom caste/tribe was not known or is missing, who are","","","","","","","","","","","","","","",""],
        ["","not shown separately.","","","","","","","","","","","","","","","",""],
        ["","na = Not available","","","","","","","","","","","","","","","",""],
        ["","","ns = Not shown; see table 2b, footnote 1","","","","","","","","","","","","","","",""],
        ["","( ) Based on 25-49 unweighted cases.","","","","","","","","","","","","","","","",""],
        ["","","","","","","","","54","","","","","","","","",""]
    ]
    pdfname = os.path.join(testdir, "left_rotated_table_2.pdf")
    manager = Pdf(Stream(flag_size=False), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables["page-1"]["table-1"]["data"], data)

    pdfname = os.path.join(testdir, "right_rotated_table_2.pdf")
    manager = Pdf(Stream(flag_size=False), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables["page-1"]["table-1"]["data"], data)