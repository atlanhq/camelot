import os
import csv
import cv2
import glob
import numpy as np

from table import Table
from pdf import get_pdf_info
from morph_transform import morph_transform
from utils import (translate, scale, merge_close_values, get_row_idx,
                   get_column_idx, reduce_index, outline, fill, remove_empty)


def spreadsheet(pdf_dir, filename, fill, s, jtol, mtol, invert, debug,
                char_margin, line_margin, word_margin):
    if debug:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
    print "working on", filename
    imagename = os.path.join(pdf_dir, filename.split('.')[0] + '.png')
    img = cv2.imread(imagename)
    img_x, img_y = img.shape[1], img.shape[0]
    text, pdf_x, pdf_y = get_pdf_info(
        os.path.join(pdf_dir, filename), 'spreadsheet',
        char_margin, line_margin, word_margin)
    scaling_factor_x = pdf_x / float(img_x)
    scaling_factor_y = pdf_y / float(img_y)
    tables, v_segments, h_segments = morph_transform(imagename, s, invert)

    if debug == ["contours"]:
        for t in tables.keys():
            cv2.rectangle(img, (t[0], t[1]), (t[2], t[3]), (255, 0, 0), 3)
        plt.imshow(img)
    if debug == ["joints"]:
        x_coord = []
        y_coord = []
        for k in tables.keys():
            for coord in tables[k]:
                x_coord.append(coord[0])
                y_coord.append(coord[1])
        max_x, max_y = max(x_coord), max(y_coord)
        plt.plot(x_coord, y_coord, 'ro')
        plt.axis([0, max_x + 100, max_y + 100, 0])
        plt.imshow(img)

    # detect if vertical
    num_v = [t for t in text if (not t.upright) and t.get_text().strip()]
    num_h = [t for t in text if t.upright and t.get_text().strip()]
    vger = len(num_v) / float(len(num_v) + len(num_h))
    rotated = ''
    if vger > 0.8:
        clockwise = sum(t.matrix[1] < 0 and t.matrix[2] > 0 for t in text)
        anticlockwise = sum(t.matrix[1] > 0 and t.matrix[2] < 0 for t in text)
        rotated = 'left' if clockwise < anticlockwise else 'right'

    tables_new = {}
    for k in tables.keys():
        x1, y1, x2, y2 = k
        x1 = scale(x1, scaling_factor_x)
        y1 = scale(abs(translate(-img_y, y1)), scaling_factor_y)
        x2 = scale(x2, scaling_factor_x)
        y2 = scale(abs(translate(-img_y, y2)), scaling_factor_y)
        j_x, j_y = zip(*tables[k])
        j_x = [scale(j, scaling_factor_x) for j in j_x]
        j_y = [scale(abs(translate(-img_y, j)), scaling_factor_y) for j in j_y]
        joints = zip(j_x, j_y)
        tables_new[(x1, y1, x2, y2)] = joints

    v_segments_new = []
    for v in v_segments:
        x1, x2 = scale(v[0], scaling_factor_x), scale(v[2], scaling_factor_x)
        y1, y2 = scale(abs(translate(-img_y, v[1])), scaling_factor_y), scale(
            abs(translate(-img_y, v[3])), scaling_factor_y)
        v_segments_new.append((x1, y1, x2, y2))

    h_segments_new = []
    for h in h_segments:
        x1, x2 = scale(h[0], scaling_factor_x), scale(h[2], scaling_factor_x)
        y1, y2 = scale(abs(translate(-img_y, h[1])), scaling_factor_y), scale(
            abs(translate(-img_y, h[3])), scaling_factor_y)
        h_segments_new.append((x1, y1, x2, y2))

    num_tables = 0
    # sort tables based on y-coord
    for k in sorted(tables_new.keys(), key=lambda x: x[1], reverse=True):
        # find rows and columns that lie in table
        lb = (k[0], k[1])
        rt = (k[2], k[3])
        v_s = [v for v in v_segments_new if v[1] > lb[1] - 2 and v[3]
               < rt[1] + 2 and lb[0] - 2 <= v[0] <= rt[0] + 2]
        h_s = [h for h in h_segments_new if h[0] > lb[0] - 2 and h[2]
               < rt[0] + 2 and lb[1] - 2 <= h[1] <= rt[1] + 2]

        if debug == ["lines"]:
            for v in v_s:
                plt.plot([v[0], v[2]], [v[1], v[3]])
            for h in h_s:
                plt.plot([h[0], h[2]], [h[1], h[3]])

        columns, rows = zip(*tables_new[k])
        columns, rows = list(columns), list(rows)
        columns.extend([lb[0], rt[0]])
        rows.extend([lb[1], rt[1]])
        # sort horizontal and vertical segments
        columns = merge_close_values(sorted(columns), mtol)
        rows = merge_close_values(sorted(rows, reverse=True), mtol)
        # make grid using x and y coord of shortlisted rows and columns
        columns = [(columns[i], columns[i + 1])
                   for i in range(0, len(columns) - 1)]
        rows = [(rows[i], rows[i + 1]) for i in range(0, len(rows) - 1)]

        table = Table(columns, rows)
        # light up cell edges
        table = table.set_edges(v_s, h_s, jtol)
        # table set span method
        table = table.set_spanning()
        # TODO
        table = outline(table)

        if debug == ["tables"]:
            for i in range(len(table.cells)):
                for j in range(len(table.cells[i])):
                    if table.cells[i][j].left:
                        plt.plot([table.cells[i][j].lb[0], table.cells[i][j].lt[0]],
                                 [table.cells[i][j].lb[1], table.cells[i][j].lt[1]])
                    if table.cells[i][j].right:
                        plt.plot([table.cells[i][j].rb[0], table.cells[i][j].rt[0]],
                                 [table.cells[i][j].rb[1], table.cells[i][j].rt[1]])
                    if table.cells[i][j].top:
                        plt.plot([table.cells[i][j].lt[0], table.cells[i][j].rt[0]],
                                 [table.cells[i][j].lt[1], table.cells[i][j].rt[1]])
                    if table.cells[i][j].bottom:
                        plt.plot([table.cells[i][j].lb[0], table.cells[i][j].rb[0]],
                                 [table.cells[i][j].lb[1], table.cells[i][j].rb[1]])
        if debug:
            plt.show()

        # fill text after sorting it
        if not rotated:
            text.sort(key=lambda x: (-x.y0, x.x0))
        elif rotated == 'left':
            text.sort(key=lambda x: (x.x0, x.y0))
        elif rotated == 'right':
            text.sort(key=lambda x: (-x.x0, -x.y0))

        for t in text:
            r_idx = get_row_idx(t, rows)
            c_idx = get_column_idx(t, columns)
            if None in [r_idx, c_idx]:
                pass
            else:
                r_idx, c_idx = reduce_index(table, rotated, r_idx, c_idx)
                table.cells[r_idx][c_idx].add_text(t.get_text().strip('\n'))

        if fill:
            table = fill(table, fill)

        data = []
        for i in range(len(table.cells)):
            data.append([table.cells[i][j].get_text().strip().encode('utf-8')
                         for j in range(len(table.cells[i]))])
        if rotated == 'left':
            data = zip(*data[::-1])
        elif rotated == 'right':
            data = zip(*data[::1])
            data.reverse()
        data = remove_empty(data)
        csvname = filename.split(
            '.')[0] + ('_table_%d' % (num_tables + 1)) + '.csv'
        csvpath = os.path.join(pdf_dir, csvname)
        with open(csvpath, 'w') as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            for d in data:
                writer.writerow(d)
            print "saved as", csvname
            print
        num_tables += 1
