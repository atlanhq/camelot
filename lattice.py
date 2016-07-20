import os
import cv2
import glob
import numpy as np
from wand.image import Image

from table import Table
from pdf import get_pdf_info
from utils import (translate, scale, merge_close_values, get_row_idx,
                   get_column_idx, reduce_index, outline, fill, remove_empty)


def morph_transform(img, s=15, invert=False):
    """Morphological Transformation

    Applies a series of morphological operations on the image
    to find table contours and line segments.
    http://answers.opencv.org/question/63847/how-to-extract-tables-from-an-image/
    
    Empirical result for adaptiveThreshold's blockSize=5 and C=-0.2
    taken from http://pequan.lip6.fr/~bereziat/pima/2012/seuillage/sezgin04.pdf

    Parameters
    ----------
    img : ndarray

    s : int, default: 15, optional
        Scaling factor. Large scaling factor leads to smaller lines
        being detected.

    invert : bool, default: False, optional
        Invert pdf image to make sure that lines are in foreground.

    Returns
    -------
    tables : dict
        Dictionary with table bounding box as key and list of
        joints found in the table as value.

    v_segments : list
        List of vertical line segments found in the image.

    h_segments : list
        List of horizontal line segments found in the image.
    """
    img_x, img_y = img.shape[1], img.shape[0]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if invert:
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -0.2)
    else:
        threshold = cv2.adaptiveThreshold(np.invert(
            gray), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -0.2)
    vertical = threshold
    horizontal = threshold

    scale = s
    verticalsize = vertical.shape[0] / scale
    horizontalsize = horizontal.shape[1] / scale

    ver = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    hor = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalsize, 1))

    vertical = cv2.erode(vertical, ver, (-1, -1))
    vertical = cv2.dilate(vertical, ver, (-1, -1))

    horizontal = cv2.erode(horizontal, hor, (-1, -1))
    horizontal = cv2.dilate(horizontal, hor, (-1, -1))

    mask = vertical + horizontal
    joints = np.bitwise_and(vertical, horizontal)
    __, contours, __ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    tables = {}
    for c in contours:
        c_poly = cv2.approxPolyDP(c, 3, True)
        x, y, w, h = cv2.boundingRect(c_poly)
        # find number of non-zero values in joints using what boundingRect
        # returns
        roi = joints[y : y + h, x : x + w]
        __, jc, __ = cv2.findContours(
            roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if len(jc) <= 4:  # remove contours with less than <=4 joints
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2 * jx + jw) / 2, y + (2 * jy + jh) / 2
            joint_coords.append((c1, c2))
        tables[(x, y + h, x + w, y)] = joint_coords

    v_segments, h_segments = [], []
    _, vcontours, _ = cv2.findContours(
        vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for vc in vcontours:
        x, y, w, h = cv2.boundingRect(vc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        v_segments.append(((x1 + x2) / 2, y2, (x1 + x2) / 2, y1))

    _, hcontours, _ = cv2.findContours(
        horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for hc in hcontours:
        x, y, w, h = cv2.boundingRect(hc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        h_segments.append((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2))

    return tables, v_segments, h_segments


def lattice(filepath, f=None, s=15, jtol=2, mtol=2, invert=False, debug=None):
    """Lattice algorithm

    Makes table using pdf geometry information returned by
    morph_transform and fills data returned by PDFMiner in table cells.

    Parameters
    ----------
    filepath : string

    f : string, default: None, optional
        Fill data in horizontal and/or vertical spanning
        cells. ('h', 'v', 'hv')

    s : int, default: 15, optional
        Scaling factor. Large scaling factor leads to smaller lines
        being detected.

    jtol : int, default: 2, optional
        Tolerance to account for when comparing joint and line
        coordinates.

    mtol : int, default: 2, optional
        Tolerance to account for when merging lines which are
        very close.

    invert : bool, default: False, optional
        Invert pdf image to make sure that lines are in foreground.

    debug : string
        Debug by visualizing pdf geometry.
        ('contour', 'line', 'joint', 'table')
    Returns
    -------
    output : dict
        Dictionary with table number as key and list of data as value.
    """
    if debug:
        import matplotlib.pyplot as plt
    fileroot, __ = os.path.splitext(filepath)
    imagename = fileroot + '.png'
    with Image(filename=filepath, depth=8, resolution=300) as png:
        png.save(filename=imagename)
    img = cv2.imread(imagename)
    img_x, img_y = img.shape[1], img.shape[0]
    text, pdf_x, pdf_y = get_pdf_info(filepath, method='lattice')
    scaling_factor_x = pdf_x / float(img_x)
    scaling_factor_y = pdf_y / float(img_y)
    tables, v_segments, h_segments = morph_transform(img, s=s, invert=invert)

    if debug == "contour":
        for t in tables.keys():
            cv2.rectangle(img, (t[0], t[1]), (t[2], t[3]), (255, 0, 0), 3)
        plt.imshow(img)
        plt.show()
        return None
    if debug == "joint":
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
        plt.show()
        return None

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

    num_tables = 1
    output = {}
    # sort tables based on y-coord
    for k in sorted(tables_new.keys(), key=lambda x: x[1], reverse=True):
        # find rows and columns that lie in table
        lb = (k[0], k[1])
        rt = (k[2], k[3])
        v_s = [v for v in v_segments_new if v[1] > lb[1] - 2 and v[3]
               < rt[1] + 2 and lb[0] - 2 <= v[0] <= rt[0] + 2]
        h_s = [h for h in h_segments_new if h[0] > lb[0] - 2 and h[2]
               < rt[0] + 2 and lb[1] - 2 <= h[1] <= rt[1] + 2]

        if debug == "line":
            for v in v_s:
                plt.plot([v[0], v[2]], [v[1], v[3]])
            for h in h_s:
                plt.plot([h[0], h[2]], [h[1], h[3]])

        columns, rows = zip(*tables_new[k])
        columns, rows = list(columns), list(rows)
        columns.extend([lb[0], rt[0]])
        rows.extend([lb[1], rt[1]])
        # sort horizontal and vertical segments
        columns = merge_close_values(sorted(columns), mtol=mtol)
        rows = merge_close_values(sorted(rows, reverse=True), mtol=mtol)
        # make grid using x and y coord of shortlisted rows and columns
        columns = [(columns[i], columns[i + 1])
                   for i in range(0, len(columns) - 1)]
        rows = [(rows[i], rows[i + 1]) for i in range(0, len(rows) - 1)]

        table = Table(columns, rows)
        # light up cell edges
        table = table.set_edges(v_s, h_s, jtol=jtol)
        # table set span method
        table = table.set_spanning()
        # light up table border
        table = outline(table)

        if debug == "table":
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

        if f is not None:
            table = fill(table, f=f)

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
        output['table_%d' % num_tables] = data
        num_tables += 1

    if debug in ['line', 'table']:
        plt.show()
        return None

    return output