import os
import csv
import numpy as np

from pdf import get_pdf_info

def overlap(l):
	merged = []
	for higher in l:
		if not merged:
			merged.append(higher)
		else:
			lower = merged[-1]
			if higher[0] >= lower[0] and higher[1] <= lower[1]:
				upper_bound = max(lower[1], higher[1])
				lower_bound = min(lower[0], higher[0])
				merged[-1] = (lower_bound, upper_bound)
			else:
				merged.append(higher)
	return merged

def get_row_idx(t, rows):
	for r in range(len(rows)):
		if t.y1 <= rows[r][0] and t.y0 >= rows[r][1]:
			return r

def get_column_idx(t, columns):
	for c in range(len(columns)):
		if t.x0 >= columns[c][0] and t.x1 <= columns[c][1]:
			return c

def basic(pdf_dir, filename):
	print "working on", filename
	text, _, _ = get_pdf_info(os.path.join(pdf_dir, filename), 'basic')
	rows, columns = [], []
	for t in text:
		rows.append((t.y1, t.y0))
		columns.append((t.x0, t.x1))
	rows = list(set(rows))
	rows = sorted(rows, reverse=True)
	columns = list(set(columns))
	columns = sorted(columns)
	columns = overlap(columns)
	table = [['' for c in columns] for r in rows]
	for t in text:
		r_idx = get_row_idx(t, rows)
		c_idx = get_column_idx(t, columns)
		if None in [r_idx, c_idx]:
			print t
		else:
			table[r_idx][c_idx] = t.get_text().strip('\n')

	csvname = filename.split('.')[0] + '.csv'
	csvpath = os.path.join(pdf_dir, csvname)
	with open(csvpath, 'w') as outfile:
		writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
	 	for cell in table:
			writer.writerow([ce for ce in cell])