from __future__ import division
import os

import numpy as np

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal


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


def transform(tables, v_segments, h_segments, factors):
    """Translates and scales OpenCV coordinates to PDFMiner coordinate
    space.

    Parameters
    ----------
    tables : dict

    v_segments : list

    h_segments : list

    factors : tuple

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


def detect_vertical(text):
    """Detects if text in table is vertical or not and returns
    its orientation.

    Parameters
    ----------
    text : list

    Returns
    -------
    rotated : string
    """
    num_v = [t for t in text if (not t.upright) and t.get_text().strip()]
    num_h = [t for t in text if t.upright and t.get_text().strip()]
    vger = len(num_v) / float(len(num_v) + len(num_h))
    rotated = ''
    if vger > 0.8:
        clockwise = sum(t.matrix[1] < 0 and t.matrix[2] > 0 for t in text)
        anticlockwise = sum(t.matrix[1] > 0 and t.matrix[2] < 0 for t in text)
        rotated = 'left' if clockwise < anticlockwise else 'right'
    return rotated


def elements_bbox(bbox, text, v_segments, h_segments):
    """Returns all text objects and line segments present inside a
    table's bounding box.

    Parameters
    ----------
    bbox : tuple

    text : list

    v_segments : list

    h_segments : list

    Returns
    -------
    text_bbox : list

    v_s : list

    h_s : list
    """
    lb = (bbox[0], bbox[1])
    rt = (bbox[2], bbox[3])
    text_bbox = [t for t in text if lb[0] - 2 <= (t.x0 + t.x1) / 2.0
                 <= rt[0] + 2 and lb[1] - 2 <= (t.y0 + t.y1) / 2.0
                 <= rt[1] + 2]
    v_s = [v for v in v_segments if v[1] > lb[1] - 2 and
           v[3] < rt[1] + 2 and lb[0] - 2 <= v[0] <= rt[0] + 2]
    h_s = [h for h in h_segments if h[0] > lb[0] - 2 and
           h[2] < rt[0] + 2 and lb[1] - 2 <= h[1] <= rt[1] + 2]
    return text_bbox, v_s, h_s


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


def get_row_index(t, rows):
    """Gets index of the row in which the given object falls by
    comparing their co-ordinates.

    Parameters
    ----------
    t : object

    rows : list, sorted in decreasing order

    Returns
    -------
    r : int
    """
    offset1, offset2 = 0, 0
    for r in range(len(rows)):
        if (t.y0 + t.y1) / 2.0 < rows[r][0] and (t.y0 + t.y1) / 2.0 > rows[r][1]:
            if t.y0 > rows[r][0]:
                offset1 = abs(t.y0 - rows[r][0])
            if t.y1 < rows[r][1]:
                offset2 = abs(t.y1 - rows[r][1])
            X = abs(t.x0 - t.x1)
            charea = abs(t.x0 - t.x1) * abs(t.y0 - t.y1)
            error = (X * (offset1 + offset2)) / charea
            return r, error


def get_column_index(t, columns):
    """Gets index of the column in which the given object falls by
    comparing their co-ordinates.

    Parameters
    ----------
    t : object

    columns : list

    Returns
    -------
    c : int
    """
    offset1, offset2 = 0, 0
    for c in range(len(columns)):
        if (t.x0 + t.x1) / 2.0 > columns[c][0] and (t.x0 + t.x1) / 2.0 < columns[c][1]:
            if t.x0 < columns[c][0]:
                offset1 = abs(t.x0 - columns[c][0])
            if t.x1 > columns[c][1]:
                offset2 = abs(t.x1 - columns[c][1])
            Y = abs(t.y0 - t.y1)
            charea = abs(t.x0 - t.x1) * abs(t.y0 - t.y1)
            error = (Y * (offset1 + offset2)) / charea
            return c, error


def get_score(error_weights):
    """Calculates score based on weights assigned to various parameters,
    and their error percentages.

    Parameters
    ----------
    error_weights : dict
        Dict with a tuple of error percentages as key and weightage
        assigned to them as value. Sum of all values should be equal
        to 100.

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


def reduce_index(t, rotated, r_idx, c_idx):
    """Reduces index of a text object if it lies within a spanning
    cell taking in account table rotation.

    Parameters
    ----------
    t : object

    rotated : string

    r_idx : int

    c_idx : int

    Returns
    -------
    r_idx : int

    c_idx : int
    """
    if not rotated:
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].left:
                c_idx -= 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].top:
                r_idx -= 1
    elif rotated == 'left':
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].left:
                c_idx -= 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].bottom:
                r_idx += 1
    elif rotated == 'right':
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].right:
                c_idx += 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].top:
                r_idx -= 1
    return r_idx, c_idx


def outline(t):
    """Sets table border edges to True.

    Parameters
    ----------
    t : object

    Returns
    -------
    t : object
    """
    for i in range(len(t.cells)):
        t.cells[i][0].left = True
        t.cells[i][len(t.cells[i]) - 1].right = True
    for i in range(len(t.cells[0])):
        t.cells[0][i].top = True
        t.cells[len(t.cells) - 1][i].bottom = True
    return t


def fill_spanning(t, fill=None):
    """Fills spanning cells.

    Parameters
    ----------
    t : object

    f : string
        (optional, default: None)

    Returns
    -------
    t : object
    """
    if fill == "h":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_h:
                        t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
    elif fill == "v":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_v:
                        t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    elif fill == "hv":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_h:
                        t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
                    elif t.cells[i][j].spanning_v:
                        t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    return t


def remove_empty(d):
    """Removes empty rows and columns from list of lists.

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
    """Counts empty rows and columns from list of lists.

    Parameters
    ----------
    d : list

    Returns
    -------
    n_blank_rows : number of blank rows
    n_blank_cols : number of blank columns
    blank_p : percentage of blank cells
    """
    n_blank_rows, n_blank_cols, blank_p = 0, 0, 0
    for i in d:
        for j in i:
            if j == '':
                blank_p += 1
    blank_p = 100 * (blank_p / float(len(d) * len(d[0])))
    for i, row in enumerate(d):
        if row == [''] * len(row):
            n_blank_rows += 1
    d = zip(*d)
    d = [list(col) for col in d]
    for i, col in enumerate(d):
        if col == [''] * len(col):
            n_blank_cols += 1
    return n_blank_rows, n_blank_cols, blank_p


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


def extract_text_objects(layout, LTObject, t=None):
    """Recursively parses pdf layout to get a list of
    text objects.

    Parameters
    ----------
    layout : object
        Layout object.

    LTObject : object
        Text object, either LTChar or LTTextLineHorizontal.

    t : list (optional, default: None)

    Returns
    -------
    t : list
        List of text objects.
    """
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTObject):
                t.append(obj)
            else:
                t += extract_text_objects(obj, LTObject)
    except AttributeError:
        pass
    return t


def pdf_to_text(pname, char_margin, line_margin, word_margin):
    # pkey = 'page-{0}'.format(p)
    # pname = os.path.join(self.temp, '{}.pdf'.format(pkey))
    with open(pname, 'r') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        laparams = LAParams(char_margin=char_margin,
                            line_margin=line_margin,
                            word_margin=word_margin)
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            lattice_objects = extract_text_objects(layout, LTChar)
            stream_objects = extract_text_objects(
                layout, LTTextLineHorizontal)
            width = layout.bbox[2]
            height = layout.bbox[3]
        return lattice_objects, stream_objects, width, height