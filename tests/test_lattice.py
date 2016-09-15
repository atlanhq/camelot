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
    manager = Pdf(Lattice(), pdfname, pagenos=[{'start': 2, 'end': 2}],
        clean=True)
    tables = manager.extract()
    assert_equal(tables['page-2']['table-1']['data'], data)


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
    manager = Pdf(Lattice(fill='v', scale=40), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables['page-1']['table-1']['data'], data)


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
    manager = Pdf(Lattice(invert=True), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables['page-1']['table-2']['data'], data)


def test_lattice_table_rotation():

    data = [
        ["State","Nutritional Assessment  (No. of individuals)","","","","IYCF Practices  (No. of mothers: 2011-12)","Blood Pressure  (No. of adults: 2011-12)","","Fasting  Blood Sugar (No. of adults:2011-12)",""],
        ["","1975-79","1988-90","1996-97","2011-12","","Men","Women","Men","Women"],
        ["Kerala","5738","6633","8864","8297","245","2161","3195","1645","2391"],
        ["Tamil Nadu","7387","10217","5813","7851","413","2134","2858","1119","1739"],
        ["Karnataka","6453","8138","12606","8958","428","2467","2894","1628","2028"],
        ["Andhra Pradesh","5844","9920","9545","8300","557","1899","2493","1111","1529"],
        ["Maharashtra","5161","7796","6883","9525","467","2368","2648","1417","1599"],
        ["Gujarat","4403","5374","4866","9645","477","2687","3021","2122","2503"],
        ["Madhya Pradesh","*","*","*","7942","470","1965","2150","1579","1709"],
        ["Orissa","3756","5540","12024","8473","398","2040","2624","1093","1628"],
        ["West Bengal","*","*","*","8047","423","2058","2743","1413","2027"],
        ["Uttar Pradesh","*","*","*","9860","581","2139","2415","1185","1366"],
        ["Pooled","38742","53618","60601","86898","4459","21918","27041","14312","18519"]
    ]
    pdfname = os.path.join(testdir, 'left_rotated_table.pdf')
    manager = Pdf(Lattice(), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables['page-1']['table-1']['data'], data)

    pdfname = os.path.join(testdir, 'right_rotated_table.pdf')
    manager = Pdf(Lattice(), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables['page-1']['table-1']['data'], data)

def test_lattice_cell_rotation():

    data = [
        ["Sl.No.","District","Projected Population for 2012-13(In lakhs)","Adult Equivalent  to 88%(In lakhs)","Total Consumptionrequirement(@ 400gms/adult/day)(In Lakh tonnes)","Total Requirement(Including seeds, feeds & wastage)(In Lakh tonnes)","Production (Rice)(In Lakh tonnes)","","","Surplus/Deﬁ cit(In Lakh tonnes)",""],
        ["","","","","","","Kharif","Rabi","Total","Rice","Paddy"],
        ["1","Balasore","23.65","20.81","3.04","3.47","2.78","0.86","3.64","0.17","0.25"],
        ["2","Bhadrak","15.34","13.50","1.97","2.25","3.50","0.05","3.55","1.30","1.94"],
        ["3","Balangir","17.01","14.97","2.19","2.50","6.23","0.10","6.33","3.83","5.72"],
        ["4","Subarnapur","6.70","5.90","0.86","0.98","4.48","1.13","5.61","4.63","6.91"],
        ["5","Cuttack","26.63","23.43","3.42","3.91","3.75","0.06","3.81","-0.10","-0.15"],
        ["6","Jagatsingpur","11.49","10.11","1.48","1.69","2.10","0.02","2.12","0.43","0.64"],
        ["7","Jajpur","18.59","16.36","2.39","2.73","2.13","0.04","2.17","-0.56","-0.84"],
        ["8","Kendrapara","14.62","12.87","1.88","2.15","2.60","0.07","2.67","0.52","0.78"],
        ["9","Dhenkanal","12.13","10.67","1.56","1.78","2.26","0.02","2.28","0.50","0.75"],
        ["10","Angul","12.93","11.38","1.66","1.90","1.73","0.02","1.75","-0.15","-0.22"],
        ["11","Ganjam","35.77","31.48","4.60","5.26","4.57","0.00","4.57","-0.69","-1.03"],
        ["12","Gajapati","5.85","5.15","0.75","0.86","0.68","0.01","0.69","-0.17","-0.25"],
        ["13","Kalahandi","16.12","14.19","2.07","2.37","5.42","1.13","6.55","4.18","6.24"],
        ["14","Nuapada","6.18","5.44","0.79","0.90","1.98","0.08","2.06","1.16","1.73"],
        ["15","Keonjhar","18.42","16.21","2.37","2.71","2.76","0.08","2.84","0.13","0.19"],
        ["16","Koraput","14.09","12.40","1.81","2.07","2.08","0.34","2.42","0.35","0.52"],
        ["17","Malkangiri","6.31","5.55","0.81","0.93","1.78","0.04","1.82","0.89","1.33"],
        ["18","Nabarangpur","12.50","11.00","1.61","1.84","3.26","0.02","3.28","1.44","2.15"],
        ["19","Rayagada","9.83","8.65","1.26","1.44","1.15","0.03","1.18","-0.26","-0.39"],
        ["20","Mayurbhanj","25.61","22.54","3.29","3.76","4.90","0.06","4.96","1.20","1.79"],
        ["21","Kandhamal","7.45","6.56","0.96","1.10","0.70","0.01","0.71","-0.39","-0.58"],
        ["22","Boudh","4.51","3.97","0.58","0.66","1.73","0.03","1.76","1.10","1.64"],
        ["23","Puri","17.29","15.22","2.22","2.54","2.45","0.99","3.44","0.90","1.34"],
        ["24","Khordha","23.08","20.31","2.97","3.39","2.02","0.03","2.05","-1.34","-2.00"],
        ["25","Nayagarh","9.78","8.61","1.26","1.44","2.10","0.00","2.10","0.66","0.99"],
        ["26","Sambalpur","10.62","9.35","1.37","1.57","3.45","0.71","4.16","2.59","3.87"],
        ["27","Bargarh","15.00","13.20","1.93","2.21","6.87","2.65","9.52","7.31","10.91"],
        ["28","Deogarh","3.18","2.80","0.41","0.47","1.12","0.07","1.19","0.72","1.07"],
        ["29","Jharsuguda","5.91","5.20","0.76","0.87","0.99","0.01","1.00","0.13","0.19"],
        ["30","Sundargarh","21.21","18.66","2.72","3.11","4.72","0.02","4.74","1.63","2.43"],
        ["ODISHA","","427.80","376.49","54.99","62.86","86.29","8.68","94.97","32.11","47.92"]
    ]
    pdfname = os.path.join(testdir, 'agstat.pdf')
    manager = Pdf(Lattice(), pdfname, clean=True)
    tables = manager.extract()
    assert_equal(tables['page-1']['table-1']['data'], data)