import os
import re
import glob
import time
import shutil
import logging
import subprocess
import argparse

from basic import basic
from spreadsheet import spreadsheet

pno = re.compile(r'\d+')


def mkdir(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)


def filesort(filename):
    filename = filename.split('/')[-1]
    num = pno.findall(filename)
    if len(num) == 2:
        return (int(num[0]), int(num[1]))
    else:
        return (int(num[0]), 0)

start_time = time.time()
CAMELOT_DIR = '.camelot/'
mkdir(CAMELOT_DIR)

parser = argparse.ArgumentParser(
    description='Parse tables from pdfs!', usage='python2 camelot.py [options] file')
parser.add_argument('-p', '--pages', nargs='+', action='store', dest='pages',
                    help='Specify the page numbers and/or page ranges to be parsed. Example: -p="1 3-5 9", -p="all" (default: 1)')
parser.add_argument('-f', '--format', nargs=1, action='store', dest='format',
                    help='Output format (csv/xlsx). Example: -f="xlsx" (default: csv)', default=["csv"])
parser.add_argument('-s', '--spreadsheet', action='store_true', dest='spreadsheet',
                    help='Extract tables with ruling lines. (default: False)')
parser.add_argument('-i', '--fill', action='store', dest='fill',
                    help='Fill the values in empty cells horizontally(h) and/or vertically(v). Example: -F="h", -F="v", -F="hv" (default: None)', default=None)
parser.add_argument('-c', '--scale', nargs='?', action='store', dest='scale',
                    help='Scaling factor. Large scaling factor leads to smaller lines being detected. (default: 15)', default=15, type=int)
parser.add_argument('-j', '--jtol', nargs='?', action='store',
                    dest='jtol', help='Tolerance to account for when comparing joint and line coordinates. (default: 2)', default=2, type=int)
parser.add_argument('-t', '--mtol', nargs='?', action='store',
                    dest='mtol', help='Tolerance to account for when merging lines which are very close. (default: 2)', default=2, type=int)
parser.add_argument('-n', '--invert', action='store_true', dest='invert',
                    help='Make sure lines are in foreground. (default: False)')
parser.add_argument('-d', '--debug', nargs=1, action='store', dest='debug',
                    help='Debug by visualizing contours, lines, joints, tables. Example: --debug="contours"')
parser.add_argument('-M', '--char-margin', nargs='?', action='store', dest='char_margin',
                    help='(default: 2.0)', default=2.0, type=float)
parser.add_argument('-L', '--line-margin', nargs='?', action='store', dest='line_margin',
                    help='(default: 0.5)', default=0.5, type=float)
parser.add_argument('-W', '--word-margin', nargs='?', action='store', dest='word_margin',
                    help='(default: 0.1)', default=0.1, type=float)
parser.add_argument('-o', '--output', nargs=1, action='store', dest='output',
                    help='Specify output directory.')
parser.add_argument('file', nargs=1)

result = parser.parse_args()

if result.pages:
    if result.pages == ['all']:
        p = result.pages
    else:
        p = []
        for r in result.pages[0].split(' '):
            if '-' in r:
                a, b = r.split('-')
                a, b = int(a), int(b)
                p.extend([str(i) for i in range(a, b + 1)])
            else:
                p.extend([str(r)])
else:
    p = ['1']
p = sorted(set(p))

filename = result.file[0].split('/')[-1]
# pdf_dir = os.path.join(CAMELOT_DIR, os.urandom(16).encode('hex'))
pdf_dir = os.path.join(CAMELOT_DIR, filename.split('.')[0])
mkdir(pdf_dir)
logging.basicConfig(filename=os.path.join(pdf_dir, filename.split('.')[
                    0] + '.log'), filemode='w', level=logging.DEBUG)

shutil.copy(result.file[0], os.path.join(pdf_dir, filename))
print "separating pdf into pages"
print
if p == ['all']:
    subprocess.call(['pdfseparate', os.path.join(
        pdf_dir, filename), os.path.join(pdf_dir, 'pg-%d.pdf')])
else:
    for page in p:
        subprocess.call(['pdfseparate', '-f', page, '-l', page, os.path.join(
            pdf_dir, filename), os.path.join(pdf_dir, 'pg-' + page + '.pdf')])

if result.spreadsheet:
    print "using the spreadsheet method"
    for g in sorted(glob.glob(os.path.join(pdf_dir, 'pg-*.pdf'))):
        print "converting", g.split('/')[-1], "to image"
        os.system(' '.join(['convert', '-density', '300',
                            g, '-depth', '8', g[:-4] + '.png']))
        try:
            spreadsheet(pdf_dir, g.split('/')[-1], result.fill, result.scale,
                        result.jtol, result.mtol, result.invert, result.debug,
                        result.char_margin, result.line_margin, result.word_margin)
        except:
          logging.error("Couldn't parse " + g.split('/')[-1])
          print "Couldn't parse", g.split('/')[-1]
else:
    print "using the basic method"
    for g in sorted(glob.glob(os.path.join(pdf_dir, 'pg-*.pdf'))):
        basic(pdf_dir, g.split('/')[-1], result.char_margin, result.line_margin, result.word_margin)

if result.format == ['xlsx']:
    import csv
    from pyexcel_xlsx import save_data
    from collections import OrderedDict
    data = OrderedDict()
    for c in sorted(glob.glob(os.path.join(pdf_dir, '*.csv')), key=filesort):
        print "adding", c.split('/')[-1], "to excel file"
        with open(c, 'r') as csvfile:
            reader = csv.reader(csvfile)
            data.update({c.split('/')[-1].split('.')
                         [0]: [row for row in reader]})
    xlsxname = filename.split('.')[0] + '.xlsx'
    xlsxpath = os.path.join(pdf_dir, xlsxname)
    save_data(xlsxpath, data)
    print
    print "saved as", xlsxname

print "finished in", time.time() - start_time, "seconds"
logging.info("Time taken for " + filename + ": " +
             str(time.time() - start_time) + " seconds")
