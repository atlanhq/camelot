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

parser = argparse.ArgumentParser(description='Parse yo pdf!', usage='python2 camelot.py [options] pdf_file')
parser.add_argument('-p', nargs='+', action='store', dest='pages', help='Specify the page numbers and/or page ranges to be parsed. Example: -p="1 3-5 9", -p="all" (default: -p="1")')
parser.add_argument('-f', nargs=1, action='store', dest='format', help='Output format (csv/xlsx). Example: -f="xlsx" (default: -f="csv")', default=["csv"])
parser.add_argument('-spreadsheet', action='store_true', dest='spreadsheet', help='Extract data stored in pdfs with ruling lines. (default: False)')
parser.add_argument('-F', action='store', dest='orientation', help='Fill the values in empty cells. Example: -F="h", -F="v", -F="hv" (default: None)', default=None)
parser.add_argument('-s', nargs='?', action='store', dest='scale', help='Scaling factor. Large scaling factor leads to smaller lines being detected. (default: 15)', default=15, type=int)
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

s = result.spreadsheet

pdf_dir = os.path.join(CAMELOT_DIR, os.urandom(16).encode('hex'))
mkdir(pdf_dir)
filename = result.file[0].split('/')[-1]
logging.basicConfig(filename=os.path.join(pdf_dir, filename.split('.')[0] + '.log'), filemode='w', level=logging.DEBUG)

shutil.copy(result.file[0], os.path.join(pdf_dir, filename))
print "separating pdf into pages"
print
if p == ['all']:
	subprocess.call(['pdfseparate', os.path.join(pdf_dir, filename), os.path.join(pdf_dir, 'pg-%d.pdf')])
else:
	for page in p:
		subprocess.call(['pdfseparate', '-f', page, '-l', page, os.path.join(pdf_dir, filename), os.path.join(pdf_dir, 'pg-' + page + '.pdf')])

if s:
	print "using the spreadsheet method"
	for g in sorted(glob.glob(os.path.join(pdf_dir, 'pg-*.pdf'))):
		print "converting", g.split('/')[-1], "to image"
		os.system(' '.join(['convert', '-density', '300', g, '-depth', '8', g[:-4] + '.png']))
		spreadsheet(pdf_dir, g.split('/')[-1], result.orientation, result.scale)
else:
	print "using the basic method"
	for g in sorted(glob.glob(os.path.join(pdf_dir, 'pg-*.pdf'))):
		basic(pdf_dir, g.split('/')[-1])

if result.format == ['xlsx']:
	import csv
	from pyexcel_xlsx import save_data
	from collections import OrderedDict
	data = OrderedDict()
	for c in sorted(glob.glob(os.path.join(pdf_dir, '*.csv')), key=filesort):
		print "adding", c.split('/')[-1], "to excel file"
		with open(c, 'r') as csvfile:
			reader = csv.reader(csvfile)
			data.update({c.split('/')[-1].split('.')[0]: [row for row in reader]})
	xlsxname = filename.split('.')[0] + '.xlsx'
	xlsxpath = os.path.join(pdf_dir, xlsxname)
	save_data(xlsxpath, data)
	print
	print "saved as", xlsxname

print "finished in", time.time() - start_time, "seconds"
logging.info("Time taken for " + filename + ": " + str(time.time() - start_time) + " seconds")
