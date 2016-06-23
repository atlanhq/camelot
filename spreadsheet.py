import os
import csv
import glob
import numpy as np
import matplotlib.pyplot as plt

from table import Table
from pdf import get_pdf_info
from morph_transform import morph

def remove_close_values(ar):
	ret = []
	for a in ar:
		if not ret:
			ret.append(a)
		else:
			temp = ret[-1]
			if np.isclose(temp, a, atol=2):
				pass
			else:
				ret.append(a)
	return ret

def merge_close_values(ar):
	ret = []
	for a in ar:
		if not ret:
			ret.append(a)
		else:
			temp = ret[-1]
			if np.isclose(temp, a, atol=2):
				temp = (temp + a) / 2.0
				ret[-1] = temp
			else:
				ret.append(a)
	return ret

def get_row_idx(t, rows):
	for r in range(len(rows)):
		if abs(t.y0 + t.y1) / 2.0 < rows[r][0] and abs(t.y0 + t.y1) / 2.0 > rows[r][1]:
			return r

def get_column_idx(t, columns):
	for c in range(len(columns)):
		if abs(t.x0 + t.x1) / 2.0 > columns[c][0] and abs(t.x0 + t.x1) / 2.0 < columns[c][1]:
			return c

def reduce_index(t, r_idx, c_idx):
	if t.cells[r_idx][c_idx].spanning_h:
		while not t.cells[r_idx][c_idx].left:
			c_idx -= 1
	if t.cells[r_idx][c_idx].spanning_v:
		while not t.cells[r_idx][c_idx].top:
			r_idx -= 1
	return r_idx, c_idx

def fill(t, orientation):
	if orientation == "h":
		for i in range(len(t.cells)):
			for j in range(len(t.cells[i])):
				if t.cells[i][j].get_text().strip() == '':
					if t.cells[i][j].spanning_h:
						t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
	elif orientation == "v":
		for i in range(len(t.cells)):
			for j in range(len(t.cells[i])):
				if t.cells[i][j].get_text().strip() == '':
					if t.cells[i][j].spanning_v:
						t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
	elif orientation == "hv":
		for i in range(len(t.cells)):
			for j in range(len(t.cells[i])):
				if t.cells[i][j].get_text().strip() == '':
					if t.cells[i][j].spanning_h:
						t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
					elif t.cells[i][j].spanning_v:
						t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
	return t

def spreadsheet(pdf_dir, filename, orientation, scale):
	print "working on", filename
	imagename = os.path.join(pdf_dir, filename.split('.')[0] + '.png')
	text, pdf_x, pdf_y = get_pdf_info(os.path.join(pdf_dir, filename), 'spreadsheet')
	tables, v_segments, h_segments = morph(imagename, pdf_x, pdf_y, scale)

	num_tables = 0
	for k in sorted(tables.keys(), key=lambda x: x[1], reverse=True): # sort tables based on y-coord
		# find rows and columns that lie in table
		lb = (k[0], k[1])
		rt = (k[2], k[3])
		v_s = [v for v in v_segments if v[1] > lb[1] - 2 and v[3] < rt[1] + 2 and lb[0] - 2 <= v[0] <= rt[0] + 2]
		h_s = [h for h in h_segments if h[0] > lb[0] - 2 and h[2] < rt[0] + 2 and lb[1] - 2 <= h[1] <= rt[1] + 2]
		columns, rows = zip(*tables[k])
		# sort horizontal and vertical segments
		columns = merge_close_values(sorted(list(columns)))
		rows = merge_close_values(sorted(list(rows), reverse=True))
		# make grid using x and y coord of shortlisted rows and columns
		columns = [(columns[i], columns[i + 1]) for i in range(0, len(columns) - 1)]
		rows = [(rows[i], rows[i + 1]) for i in range(0, len(rows) - 1)]

		table = Table(columns, rows)
		# pass row and column line segments to table method and light up cell edges
		table = table.set_edges(v_s, h_s)
		# table set span method
		table = table.set_spanning()
		# fill text after sorting it
		text.sort(key=lambda x: (-x.y0, x.x0))

		for t in text:
			r_idx = get_row_idx(t, rows)
			c_idx = get_column_idx(t, columns)
			if None in [r_idx, c_idx]:
				pass
			else:
				r_idx, c_idx = reduce_index(table, r_idx, c_idx)
				table.cells[r_idx][c_idx].add_text(t.get_text().strip('\n'))

		if orientation:
			table = fill(table, orientation)

		csvname = filename.split('.')[0] + ('_table_%d' % (num_tables + 1)) + '.csv'
		csvpath = os.path.join(pdf_dir, csvname)
		with open(csvpath, 'w') as outfile:
			writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
		 	for i in range(len(table.cells)):
				writer.writerow([table.cells[i][j].get_text().strip().encode('utf-8') for j in range(len(table.cells[i]))])
			print "saved as", csvname
			print
		num_tables += 1