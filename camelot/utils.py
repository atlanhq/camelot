from __future__ import division
import os
import logging
from itertools import groupby
from operator import itemgetter

import numpy as np

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (LAParams, LTAnno, LTChar, LTTextLineHorizontal,
                             LTTextLineVertical)


def translate(x1, x2):
    """Translates x2 by x1.

    Parameters
    ----------
    x1 : float

    x2 : float

    Returns
    -------
    x2 : float
    """
    x2 += x1
    return x2


def scale(x, s):
    """Scales x by scaling factor s.

    Parameters
    ----------
    x : float

    s : float

    Returns
    -------
    x : float
    """
    x *= s
    return x


def rotate(x1, y1, x2, y2, angle):
    """Rotates point x2, y2 about point x1, y1 by angle.

    Parameters
    ----------
    x1 : float

    y1 : float

    x2 : float

    y2 : float

    angle : float
        Angle in radians.

    Returns
    -------
    xnew : float

    ynew : float
    """
    s = np.sin(angle)
    c = np.cos(angle)
    x2 = translate(-x1, x2)
    y2 = translate(-y1, y2)
    xnew = c * x2 - s * y2
    ynew = s * x2 + c * y2
    xnew = translate(x1, xnew)
    ynew = translate(y1, ynew)
    return xnew, ynew


def scale_to_image(k, factors):
    """Translates and scales PDFMiner coordinates to OpenCV's coordinate
    space.

    Parameters
    ----------
    k : tuple
        Tuple (x1, y1, x2, y2) representing table bounding box where
        (x1, y1) -> lt and (x2, y2) -> rb in PDFMiner's coordinate
        space.

    factors : tuple
        Tuple (scaling_factor_x, scaling_factor_y, pdf_y) where the
        first two elements are scaling factors and pdf_y is height of
        pdf.

    Returns
    -------
    knew : tuple
        Tuple (x1, y1, x2, y2) representing table bounding box where
        (x1, y1) -> lt and (x2, y2) -> rb in OpenCV's coordinate
        space.
    """
    x1, y1, x2, y2 = k
    scaling_factor_x, scaling_factor_y, pdf_y = factors
    x1 = scale(x1, scaling_factor_x)
    y1 = scale(abs(translate(-pdf_y, y1)), scaling_factor_y)
    x2 = scale(x2, scaling_factor_x)
    y2 = scale(abs(translate(-pdf_y, y2)), scaling_factor_y)
    knew = (int(x1), int(y1), int(x2), int(y2))
    return knew


def scale_to_pdf(tables, v_segments, h_segments, factors):
    """Translates and scales OpenCV coordinates to PDFMiner's coordinate
    space.

    Parameters
    ----------
    tables : dict
        Dict with table boundaries as keys and list of intersections
        in that boundary as their value.

    v_segments : list
        List of vertical line segments.

    h_segments : list
        List of horizontal line segments.

    factors : tuple
        Tuple (scaling_factor_x, scaling_factor_y, img_y) where the
        first two elements are scaling factors and img_y is height of
        image.

    Returns
    -------
    tables_new : dict

    v_segments_new : dict

    h_segments_new : dict
    """
    scaling_factor_x, scaling_factor_y, img_y = factors
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

    return tables_new, v_segments_new, h_segments_new


def get_rotation(lttextlh, lttextlv, ltchar):
    """Detects if text in table is vertical or not using the current
    transformation matrix (CTM) and returns its orientation.

    Parameters
    ----------
    lttextlh : list
        List of PDFMiner LTTextLineHorizontal objects.

    lttextlv : list
        List of PDFMiner LTTextLineVertical objects.

    ltchar : list
        List of PDFMiner LTChar objects.

    Returns
    -------
    rotation : string
        {'', 'left', 'right'}
        '' if text in table is upright, 'left' if rotated 90 degree
        anti-clockwise and 'right' if rotated 90 degree clockwise.
    """
    rotation = ''
    hlen = len([t for t in lttextlh if t.get_text().strip()])
    vlen = len([t for t in lttextlv if t.get_text().strip()])
    if hlen < vlen:
        clockwise = sum(t.matrix[1] < 0 and t.matrix[2] > 0 for t in ltchar)
        anticlockwise = sum(t.matrix[1] > 0 and t.matrix[2] < 0 for t in ltchar)
        rotation = 'left' if clockwise < anticlockwise else 'right'
    return rotation


def segments_bbox(bbox, v_segments, h_segments):
    """Returns all line segments present inside a
    table's bounding box.

    Parameters
    ----------
    bbox : tuple
        Tuple (x1, y1, x2, y2) representing table bounding box where
        (x1, y1) -> lb and (x2, y2) -> rt in PDFMiner's coordinate space.

    v_segments : list
        List of vertical line segments.

    h_segments : list
        List of vertical horizontal segments.

    Returns
    -------
    v_s : list
        List of vertical line segments that lie inside table.

    h_s : list
        List of horizontal line segments that lie inside table.
    """
    lb = (bbox[0], bbox[1])
    rt = (bbox[2], bbox[3])
    v_s = [v for v in v_segments if v[1] > lb[1] - 2 and
           v[3] < rt[1] + 2 and lb[0] - 2 <= v[0] <= rt[0] + 2]
    h_s = [h for h in h_segments if h[0] > lb[0] - 2 and
           h[2] < rt[0] + 2 and lb[1] - 2 <= h[1] <= rt[1] + 2]
    return v_s, h_s


def rotate_segments(v_s, h_s, table_rotation):
    """Rotates line segments if the table is rotated.

    Parameters
    ----------
    v : list
        List of vertical line segments.

    h : list
        List of horizontal line segments.

    table_rotation : string
        {'', 'left', 'right'}


    Returns
    -------
    vertical : list
        List of rotated vertical line segments.

    horizontal : list
        List of rotated horizontal line segments.
    """
    vertical, horizontal = [], []
    if table_rotation != '':
        if table_rotation == 'left':
            for v in v_s:
                x0, y0 = rotate(0, 0, v[0], v[1], -np.pi / 2)
                x1, y1 = rotate(0, 0, v[2], v[3], -np.pi / 2)
                horizontal.append((x0, y0, x1, y1))
            for h in h_s:
                x0, y0 = rotate(0, 0, h[0], h[1], -np.pi / 2)
                x1, y1 = rotate(0, 0, h[2], h[3], -np.pi / 2)
                vertical.append((x1, y1, x0, y0))
        elif table_rotation == 'right':
            for v in v_s:
                x0, y0 = rotate(0, 0, v[0], v[1], np.pi / 2)
                x1, y1 = rotate(0, 0, v[2], v[3], np.pi / 2)
                horizontal.append((x1, y1, x0, y0))
            for h in h_s:
                x0, y0 = rotate(0, 0, h[0], h[1], np.pi / 2)
                x1, y1 = rotate(0, 0, h[2], h[3], np.pi / 2)
                vertical.append((x0, y0, x1, y1))
    else:
        vertical = v_s
        horizontal = h_s
    return vertical, horizontal


def rotate_textlines(lh_bbox, lv_bbox, table_rotation):
    """Rotates bounding boxes of LTTextLineHorizontals and
    LTTextLineVerticals if the table is rotated.

    Parameters
    ----------
    lh_bbox : list
        List of PDFMiner LTTextLineHorizontal objects.

    lv_bbox : list
        List of PDFMiner LTTextLineVertical objects.

    table_rotation : string
        {'', 'left', 'right'}

    Returns
    -------
    t_bbox : dict
        Dict with two keys 'horizontal' and 'vertical' with lists of
        LTTextLineHorizontals and LTTextLineVerticals respectively.
    """
    t_bbox = {}
    if table_rotation != '':
        if table_rotation == 'left':
            for t in lh_bbox:
                x0, y0, x1, y1 = t.bbox
                x0, y0 = rotate(0, 0, x0, y0, -np.pi / 2)
                x1, y1 = rotate(0, 0, x1, y1, -np.pi / 2)
                t.set_bbox((x1, y0, x0, y1))
                for obj in t._objs:
                    if isinstance(obj, LTChar):
                        x0, y0, x1, y1 = obj.bbox
                        x0, y0 = rotate(0, 0, x0, y0, -np.pi / 2)
                        x1, y1 = rotate(0, 0, x1, y1, -np.pi / 2)
                        obj.set_bbox((x1, y0, x0, y1))
            for t in lv_bbox:
                x0, y0, x1, y1 = t.bbox
                x0, y0 = rotate(0, 0, x0, y0, -np.pi / 2)
                x1, y1 = rotate(0, 0, x1, y1, -np.pi / 2)
                t.set_bbox((x0, y1, x1, y0))
                for obj in t._objs:
                    if isinstance(obj, LTChar):
                        x0, y0, x1, y1 = obj.bbox
                        x0, y0 = rotate(0, 0, x0, y0, -np.pi / 2)
                        x1, y1 = rotate(0, 0, x1, y1, -np.pi / 2)
                        obj.set_bbox((x0, y1, x1, y0))
        elif table_rotation == 'right':
            for t in lh_bbox:
                x0, y0, x1, y1 = t.bbox
                x0, y0 = rotate(0, 0, x0, y0, np.pi / 2)
                x1, y1 = rotate(0, 0, x1, y1, np.pi / 2)
                t.set_bbox((x0, y1, x1, y0))
                for obj in t._objs:
                    if isinstance(obj, LTChar):
                        x0, y0, x1, y1 = obj.bbox
                        x0, y0 = rotate(0, 0, x0, y0, np.pi / 2)
                        x1, y1 = rotate(0, 0, x1, y1, np.pi / 2)
                        obj.set_bbox((x0, y1, x1, y0))
            for t in lv_bbox:
                x0, y0, x1, y1 = t.bbox
                x0, y0 = rotate(0, 0, x0, y0, np.pi / 2)
                x1, y1 = rotate(0, 0, x1, y1, np.pi / 2)
                t.set_bbox((x1, y0, x0, y1))
                for obj in t._objs:
                    if isinstance(obj, LTChar):
                        x0, y0, x1, y1 = obj.bbox
                        x0, y0 = rotate(0, 0, x0, y0, np.pi / 2)
                        x1, y1 = rotate(0, 0, x1, y1, np.pi / 2)
                        obj.set_bbox((x1, y0, x0, y1))
        t_bbox['horizontal'] = lv_bbox
        t_bbox['vertical'] = lh_bbox
    else:
        t_bbox['horizontal'] = lh_bbox
        t_bbox['vertical'] = lv_bbox
    return t_bbox


def rotate_table(R, C, table_rotation):
    """Rotates coordinates of table rows and columns.

    Parameters
    ----------
    R : list
        List of row x-coordinates.

    C : list
        List of column y-coordinates.

    table_rotation : string
        {'', 'left', 'right'}

    Returns
    -------
    rows : list
        List of rotated row x-coordinates.

    cols : list
        List of rotated column y-coordinates.
    """
    rows, cols = [], []
    if table_rotation != '':
        if table_rotation == 'left':
            for r in R:
                r0, r1 = rotate(0, 0, 0, r[0], -np.pi / 2)
                r2, r3 = rotate(0, 0, 0, r[1], -np.pi / 2)
                cols.append((r2, r0))
            cols = sorted(cols)
            for c in C:
                c0, c1 = rotate(0, 0, c[0], 0, -np.pi / 2)
                c2, c3 = rotate(0, 0, c[1], 0, -np.pi / 2)
                rows.append((c1, c3))
        elif table_rotation == 'right':
            for r in R:
                r0, r1 = rotate(0, 0, 0, r[0], np.pi / 2)
                r2, r3 = rotate(0, 0, 0, r[1], np.pi / 2)
                cols.append((r0, r2))
            for c in C:
                c0, c1 = rotate(0, 0, c[0], 0, np.pi / 2)
                c2, c3 = rotate(0, 0, c[1], 0, np.pi / 2)
                rows.append((c3, c1))
            rows = sorted(rows, reverse=True)
    else:
        rows = R
        cols = C
    return rows, cols


def text_in_bbox(bbox, text):
    """Returns all text objects present inside a
    table's bounding box.

    Parameters
    ----------
    bbox : tuple
        Tuple (x1, y1, x2, y2) representing table bounding box where
        (x1, y1) -> lb and (x2, y2) -> rt in PDFMiner's coordinate space.

    text : list
        List of PDFMiner text objects.

    Returns
    -------
    t_bbox : list
        List of PDFMiner text objects that lie inside table.
    """
    lb = (bbox[0], bbox[1])
    rt = (bbox[2], bbox[3])
    t_bbox = [t for t in text if lb[0] - 2 <= (t.x0 + t.x1) / 2.0
                 <= rt[0] + 2 and lb[1] - 2 <= (t.y0 + t.y1) / 2.0
                 <= rt[1] + 2]
    return t_bbox


def remove_close_values(ar, mtol=2):
    """Removes values which are within a tolerance of mtol of another value
    present in list.

    Parameters
    ----------
    ar : list

    mtol : int
        (optional, default: 2)

    Returns
    -------
    ret : list
    """
    ret = []
    for a in ar:
        if not ret:
            ret.append(a)
        else:
            temp = ret[-1]
            if np.isclose(temp, a, atol=mtol):
                pass
            else:
                ret.append(a)
    return ret


def merge_close_values(ar, mtol=2):
    """Merges values which are within a tolerance of mtol by calculating
    a moving mean.

    Parameters
    ----------
    ar : list

    mtol : int
        (optional, default: 2)

    Returns
    -------
    ret : list
    """
    ret = []
    for a in ar:
        if not ret:
            ret.append(a)
        else:
            temp = ret[-1]
            if np.isclose(temp, a, atol=mtol):
                temp = (temp + a) / 2.0
                ret[-1] = temp
            else:
                ret.append(a)
    return ret


def flag_on_size(textline):
    """Flags a super/subscript by enclosing it with <s></s>. May give
    false positives.

    Parameters
    ----------
    textline : list
        List of PDFMiner LTChar objects.

    Returns
    -------
    fstring : string
    """
    l = []
    for t in textline:
        if not isinstance(t, LTAnno):
            l.append(t.size)
    if len(set(l)) > 1:
        flist = []
        max_size = max(l)
        d = [(t.get_text(), t.size) for t in textline if not isinstance(t, LTAnno)]
        for key, chars in groupby(d, itemgetter(1)):
            if key == max_size:
                flist.append(''.join([t[0] for t in chars]))
            else:
                fchars = [t[0] for t in chars]
                fchars.insert(0, '<s>')
                fchars.append('</s>')
                flist.append(''.join(fchars))
        fstring = ''.join(flist).strip('\n')
    else:
        fstring = ''.join([t.get_text() for t in textline]).strip('\n')
    return fstring


def split_textline(table, textline, direction):
    """Splits PDFMiner LTTextLine into substrings if it spans across
    multiple rows/columns.

    Parameters
    ----------
    table : object
        camelot.pdf.Pdf

    textline : object
        PDFMiner LTTextLine object.

    direction : string
        {'horizontal', 'vertical'}
        Direction of the PDFMiner LTTextLine object.

    Returns
    -------
    grouped_chars : list
        List of tuples of the form (idx, text) where idx is the index
        of row/column and text is the an lttextline substring.
    """
    idx = 0
    cut_text = []
    bbox = textline.bbox
    if direction == 'horizontal' and not textline.is_empty():
        x_overlap = [i for i, x in enumerate(table.cols) if x[0] <= bbox[2] and bbox[0] <= x[1]]
        r_idx = [j for j, r in enumerate(table.rows) if r[1] <= (bbox[1] + bbox[3]) / 2 <= r[0]]
        r = r_idx[0]
        x_cuts = [(c, table.cells[r][c].x2) for c in x_overlap if table.cells[r][c].right]
        if not x_cuts:
            x_cuts = [(x_overlap[0], table.cells[r][-1].x2)]
        for obj in textline._objs:
            row = table.rows[r]
            for cut in x_cuts:
                if isinstance(obj, LTChar):
                    if (row[1] <= (obj.y0 + obj.y1) / 2 <= row[0] and
                            (obj.x0 + obj.x1) / 2 <= cut[1]):
                        cut_text.append((r, cut[0], obj))
                        break
                elif isinstance(obj, LTAnno):
                    cut_text.append((r, cut[0], obj))
    elif direction == 'vertical' and not textline.is_empty():
        y_overlap = [j for j, y in enumerate(table.rows) if y[1] <= bbox[3] and bbox[1] <= y[0]]
        c_idx = [i for i, c in enumerate(table.cols) if c[0] <= (bbox[0] + bbox[2]) / 2 <= c[1]]
        c = c_idx[0]
        y_cuts = [(r, table.cells[r][c].y1) for r in y_overlap if table.cells[r][c].bottom]
        if not y_cuts:
            y_cuts = [(y_overlap[0], table.cells[-1][c].y1)]
        for obj in textline._objs:
            col = table.cols[c]
            for cut in y_cuts:
                if isinstance(obj, LTChar):
                    if (col[0] <= (obj.x0 + obj.x1) / 2 <= col[1] and
                            (obj.y0 + obj.y1) / 2 >= cut[1]):
                        cut_text.append((cut[0], c, obj.get_text()))
                        break
                elif isinstance(obj, LTAnno):
                    cut_text.append((cut[0], c, obj))
    grouped_chars = []
    for key, chars in groupby(cut_text, itemgetter(0, 1)):
        grouped_chars.append((key[0], key[1], flag_on_size([t[2] for t in chars])))
    return grouped_chars


def get_table_index(table, t, direction, split_text=False):
    """Gets indices of the cell where given text object lies by
    comparing their y and x-coordinates.

    Parameters
    ----------
    table : object
        camelot.table.Table

    t : object
        PDFMiner LTTextLine object.

    direction : string
        {'horizontal', 'vertical'}
        Direction of the PDFMiner LTTextLine object.

    split_text : bool
        Whether or not to split a text line if it spans across
        multiple cells.
        (optional, default: False)

    Returns
    -------
    indices : list
        List of tuples of the form (idx, text) where idx is the index
        of row/column and text is the an lttextline substring.

    error : float
        Assignment error, percentage of text area that lies outside
        a cell.
        +-------+
        |       |
        |   [Text bounding box]
        |       |
        +-------+
    """
    r_idx, c_idx = [-1] * 2
    for r in range(len(table.rows)):
        if ((t.y0 + t.y1) / 2.0 < table.rows[r][0] and
                (t.y0 + t.y1) / 2.0 > table.rows[r][1]):
            lt_col_overlap = []
            for c in table.cols:
                if c[0] <= t.x1 and c[1] >= t.x0:
                    left = t.x0 if c[0] <= t.x0 else c[0]
                    right = t.x1 if c[1] >= t.x1 else c[1]
                    lt_col_overlap.append(abs(left - right) / abs(c[0] - c[1]))
                else:
                    lt_col_overlap.append(-1)
            if len(filter(lambda x: x != -1, lt_col_overlap)) == 0:
                logging.warning("Text doesn't fit any column.")
            r_idx = r
            c_idx = lt_col_overlap.index(max(lt_col_overlap))
            break

    # error calculation
    y0_offset, y1_offset, x0_offset, x1_offset = [0] * 4
    if t.y0 > table.rows[r_idx][0]:
        y0_offset = abs(t.y0 - table.rows[r_idx][0])
    if t.y1 < table.rows[r_idx][1]:
        y1_offset = abs(t.y1 - table.rows[r_idx][1])
    if t.x0 < table.cols[c_idx][0]:
        x0_offset = abs(t.x0 - table.cols[c_idx][0])
    if t.x1 > table.cols[c_idx][1]:
        x1_offset = abs(t.x1 - table.cols[c_idx][1])
    X = 1.0 if abs(t.x0 - t.x1) == 0.0 else abs(t.x0 - t.x1)
    Y = 1.0 if abs(t.y0 - t.y1) == 0.0 else abs(t.y0 - t.y1)
    charea = X * Y
    error = ((X * (y0_offset + y1_offset)) + (Y * (x0_offset + x1_offset))) / charea

    if split_text:
        return split_textline(table, t, direction), error
    else:
        return [(r_idx, c_idx, flag_on_size(t._objs))], error


def get_score(error_weights):
    """Calculates score based on weights assigned to various parameters,
    and their error percentages.

    Parameters
    ----------
    error_weights : list
        Two-dimensional list of the form [[p1, e1], [p2, e2], ...]
        where pn is the weight assigned to list of errors en.
        Sum of pn should be equal to 100.

    Returns
    -------
    score : float
    """
    SCORE_VAL = 100
    score = 0
    if sum([ew[0] for ew in error_weights]) != SCORE_VAL:
        raise ValueError("Please assign a valid weightage to each parameter"
                         " such that their sum is equal to 100")
    for ew in error_weights:
        weight = ew[0] / len(ew[1])
        for error_percentage in ew[1]:
            score += weight * (1 - error_percentage)
    return score


def remove_empty(d):
    """Removes empty rows and columns from a two-dimensional list.

    Parameters
    ----------
    d : list

    Returns
    -------
    d : list
    """
    for i, row in enumerate(d):
        if row == [''] * len(row):
            d.pop(i)
    d = zip(*d)
    d = [list(row) for row in d if any(row)]
    d = zip(*d)
    return d


def count_empty(d):
    """Counts empty rows and columns in a two-dimensional list.

    Parameters
    ----------
    d : list

    Returns
    -------
    n_empty_rows : list
        Number of empty rows.

    n_empty_cols : list
        Number of empty columns.

    empty_p : float
        Percentage of empty cells.
    """
    empty_p = 0
    r_nempty_cells, c_nempty_cells = [], []
    for i in d:
        for j in i:
            if j.strip() == '':
                empty_p += 1
    empty_p = 100 * (empty_p / float(len(d) * len(d[0])))
    for row in d:
        r_nempty_c = 0
        for r in row:
            if r.strip() != '':
                r_nempty_c += 1
        r_nempty_cells.append(r_nempty_c)
    d = zip(*d)
    d = [list(col) for col in d]
    for col in d:
        c_nempty_c = 0
        for c in col:
            if c.strip() != '':
                c_nempty_c += 1
        c_nempty_cells.append(c_nempty_c)
    return empty_p, r_nempty_cells, c_nempty_cells


def encode_list(ar):
    """Encodes list of text.

    Parameters
    ----------
    ar : list

    Returns
    -------
    ar : list
    """
    ar = [[r.encode('utf-8') for r in row] for row in ar]
    return ar


def get_text_objects(layout, ltype="char", t=None):
    """Recursively parses pdf layout to get a list of
    text objects.

    Parameters
    ----------
    layout : object
        PDFMiner LTPage object.

    ltype : string
        {'char', 'lh', 'lv'}
        Specify 'char', 'lh', 'lv' to get LTChar, LTTextLineHorizontal,
        and LTTextLineVertical objects respectively.

    t : list

    Returns
    -------
    t : list
        List of PDFMiner text objects.
    """
    if ltype == "char":
        LTObject = LTChar
    elif ltype == "lh":
        LTObject = LTTextLineHorizontal
    elif ltype == "lv":
        LTObject = LTTextLineVertical
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTObject):
                t.append(obj)
            else:
                t += get_text_objects(obj, ltype=ltype)
    except AttributeError:
        pass
    return t


def get_page_layout(pname, char_margin=2.0, line_margin=0.5, word_margin=0.1,
               detect_vertical=True, all_texts=True):
    """Returns a PDFMiner LTPage object and page dimension of a single
    page pdf. See https://euske.github.io/pdfminer/ to get definitions
    of kwargs.

    Parameters
    ----------
    pname : string
        Path to pdf file.

    char_margin : float

    line_margin : float

    word_margin : float

    detect_vertical : bool

    all_texts : bool

    Returns
    -------
    layout : object
        PDFMiner LTPage object.

    dim : tuple
        pdf page dimension of the form (width, height).
    """
    with open(pname, 'r') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        laparams = LAParams(char_margin=char_margin,
                            line_margin=line_margin,
                            word_margin=word_margin,
                            detect_vertical=detect_vertical,
                            all_texts=all_texts)
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            width = layout.bbox[2]
            height = layout.bbox[3]
            dim = (width, height)
        return layout, dim