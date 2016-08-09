# coding: utf8
import os

from nose.tools import assert_equal

from camelot.pdf import Pdf
from camelot.lattice import Lattice


testdir = os.path.dirname(os.path.abspath(__file__))


def test_lattice_basic():

    data = [
        ["Cycle Name","KI (1/km)","Distance (mi)","Percent Fuel Savings","","",""],
        ["","","","Improved Speed","Decreased Accel","Eliminate Stops","Decreased Idle"],
        ["2012_2","3.30","1.3","5.9%","9.5%","29.2%","17.4%"],
        ["2145_1","0.68","11.2","2.4%","0.1%","9.5%","2.7%"],
        ["4234_1","0.59","58.7","8.5%","1.3%","8.5%","3.3%"],
        ["2032_2","0.17","57.8","21.7%","0.3%","2.7%","1.2%"],
        ["4171_1","0.07","173.9","58.1%","1.6%","2.1%","0.5%"]
    ]
    pdfname = os.path.join(testdir,
        "tabula_test_pdfs/icdar2013-dataset/competition-dataset-us/us-030.pdf")
    extractor = Lattice(Pdf(pdfname,
                            pagenos=[{'start': 2, 'end': 2}], clean=True))
    tables = extractor.get_tables()
    assert_equal(tables['page-2'][0], data)


def test_lattice_fill():

    data = [
        ["Plan Type","County","Plan  Name","Totals"],
        ["GMC","Sacramento","Anthem Blue Cross","164,380"],
        ["GMC","Sacramento","Health Net","126,547"],
        ["GMC","Sacramento","Kaiser Foundation","74,620"],
        ["GMC","Sacramento","Molina Healthcare","59,989"],
        ["GMC","San Diego","Care 1st Health Plan","71,831"],
        ["GMC","San Diego","Community Health Group","264,639"],
        ["GMC","San Diego","Health Net","72,404"],
        ["GMC","San Diego","Kaiser","50,415"],
        ["GMC","San Diego","Molina Healthcare","206,430"],
        ["GMC","Total GMC Enrollment","","1,091,255"],
        ["COHS","Marin","Partnership Health Plan of CA","36,006"],
        ["COHS","Mendocino","Partnership Health Plan of CA","37,243"],
        ["COHS","Napa","Partnership Health Plan of CA","28,398"],
        ["COHS","Solano","Partnership Health Plan of CA","113,220"],
        ["COHS","Sonoma","Partnership Health Plan of CA","112,271"],
        ["COHS","Yolo","Partnership Health Plan of CA","52,674"],
        ["COHS","Del Norte","Partnership Health Plan of CA","11,242"],
        ["COHS","Humboldt","Partnership Health Plan of CA","49,911"],
        ["COHS","Lake","Partnership Health Plan of CA","29,149"],
        ["COHS","Lassen","Partnership Health Plan of CA","7,360"],
        ["COHS","Modoc","Partnership Health Plan of CA","2,940"],
        ["COHS","Shasta","Partnership Health Plan of CA","61,763"],
        ["COHS","Siskiyou","Partnership Health Plan of CA","16,715"],
        ["COHS","Trinity","Partnership Health Plan of CA","4,542"],
        ["COHS","Merced","Central California Alliance for Health","123,907"],
        ["COHS","Monterey","Central California Alliance for Health","147,397"],
        ["COHS","Santa Cruz","Central California Alliance for Health","69,458"],
        ["COHS","Santa Barbara","CenCal","117,609"],
        ["COHS","San Luis Obispo","CenCal","55,761"],
        ["COHS","Orange","CalOptima","783,079"],
        ["COHS","San Mateo","Health Plan of San Mateo","113,202"],
        ["COHS","Ventura","Gold Coast Health Plan","202,217"],
        ["COHS","Total COHS Enrollment","","2,176,064"],
        ["Subtotal for Two-Plan, Regional Model, GMC and COHS","","","10,132,022"],
        ["PCCM","Los Angeles","AIDS Healthcare Foundation","828"],
        ["PCCM","San Francisco","Family Mosaic","25"],
        ["PCCM","Total PHP Enrollment","","853"],
        ["All Models Total Enrollments","","","10,132,875"],
        ["Source:   Data Warehouse 12/14/15","","",""]
    ]
    pdfname = os.path.join(testdir, 'row_span_1.pdf')
    extractor = Lattice(Pdf(pdfname, clean=True), fill='v', scale=40)
    tables = extractor.get_tables()
    assert_equal(tables['pagea-1'][0], data)


def test_lattice_invert():

    data = [
        ["State","Date","Halt stations","Halt days","Persons directly reached(in lakh)","Persons trained","Persons counseled","Persons testedfor HIV"],
        ["Delhi","1.12.2009","8","17","1.29","3,665","2,409","1,000"],
        ["Rajasthan","2.12.2009 to 19.12.2009","","","","","",""],
        ["Gujarat","20.12.2009 to 3.1.2010","6","13","6.03","3,810","2,317","1,453"],
        ["Maharashtra","4.01.2010 to 1.2.2010","13","26","1.27","5,680","9,027","4,153"],
        ["Karnataka","2.2.2010 to 22.2.2010","11","19","1.80","5,741","3,658","3,183"],
        ["Kerala","23.2.2010 to 11.3.2010","9","17","1.42","3,559","2,173","855"],
        ["Total","","47","92","11.81","22,455","19,584","10,644"]
    ]
    pdfname = os.path.join(testdir, 'lines_in_background_1.pdf')
    extractor = Lattice(Pdf(pdfname, clean=True), invert=True)
    tables = extractor.get_tables()
    assert_equal(tables['page-1'][1], data)