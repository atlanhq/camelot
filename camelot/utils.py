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
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal, LTTextLineVertical


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


def get_rotation(ltchar, lttextlh=None, lttextlv=None):
    """Detects if text in table is vertical or not using the current
    transformation matrix (CTM) and returns its orientation.

    Parameters
    ----------
    ltchar : list
        List of PDFMiner LTChar objects.

    lttextlh : list
        List of PDFMiner LTTextLineHorizontal objects.
        (optional, default: None)

    lttextlv : list
        List of PDFMiner LTTextLineVertical objects.
        (optional, default: None)

    Returns
    -------
    rotation : string
        {'', 'left', 'right'}
        '' if text in table is upright, 'left' if rotated 90 degree
        anti-clockwise and 'right' if rotated 90 degree clockwise.
    """
    rotation = ''
    if lttextlh is not None and lttextlv is not None:
        hlen = len([t for t in lttextlh if t.get_text().strip()])
        vlen = len([t for t in lttextlv if t.get_text().strip()])
        vger = 0.0
    else:
        hlen = len([t for t in ltchar if t.upright and t.get_text().strip()])
        vlen = len([t for t in ltchar if (not t.upright) and t.get_text().strip()])
        vger = vlen / float(hlen+vlen)
    if hlen < vlen or vger > 0.8:
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


def text_bbox(bbox, text):
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


def get_row_index(t, rows):
    """Gets index of the row in which the given text object lies by
    comparing their y-coordinates.

    Parameters
    ----------
    t : object

    rows : list
        List of row coordinate tuples, sorted in decreasing order.

    Returns
    -------
    r : int

    error : float
    """
    offset1, offset2 = 0, 0
    for r in range(len(rows)):
        if (t.y0 + t.y1) / 2.0 < rows[r][0] and (t.y0 + t.y1) / 2.0 > rows[r][1]:
            if t.y0 > rows[r][0]:
                offset1 = abs(t.y0 - rows[r][0])
            if t.y1 < rows[r][1]:
                offset2 = abs(t.y1 - rows[r][1])
            X = 1.0 if abs(t.x0 - t.x1) == 0.0 else abs(t.x0 - t.x1)
            Y = 1.0 if abs(t.y0 - t.y1) == 0.0 else abs(t.y0 - t.y1)
            charea = X * Y
            error = (X * (offset1 + offset2)) / charea
            return r, error


def get_column_index(t, columns):
    """Gets index of the column in which the given text object lies by
    comparing their x-coordinates.

    Parameters
    ----------
    t : object

    columns : list
        List of column coordinate tuples.

    Returns
    -------
    c : int

    error : float
    """
    offset1, offset2 = 0, 0
    for c in range(len(columns)):
        if (t.x0 + t.x1) / 2.0 > columns[c][0] and (t.x0 + t.x1) / 2.0 < columns[c][1]:
            if t.x0 < columns[c][0]:
                offset1 = abs(t.x0 - columns[c][0])
            if t.x1 > columns[c][1]:
                offset2 = abs(t.x1 - columns[c][1])
            X = 1.0 if abs(t.x0 - t.x1) == 0.0 else abs(t.x0 - t.x1)
            Y = 1.0 if abs(t.y0 - t.y1) == 0.0 else abs(t.y0 - t.y1)
            charea = X * Y
            error = (Y * (offset1 + offset2)) / charea
            return c, error


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
    n_empty_rows : number of empty rows
    n_empty_cols : number of empty columns
    empty_p : percentage of empty cells
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


def get_text_objects(layout, LTType="char", t=None):
    """Recursively parses pdf layout to get a list of
    text objects.

    Parameters
    ----------
    layout : object
        PDFMiner LTPage object.

    LTType : string
        {'char', 'lh', 'lv'}
        Specify 'char', 'lh', 'lv' to get LTChar, LTTextLineHorizontal,
        and LTTextLineVertical objects respectively.

    t : list

    Returns
    -------
    t : list
        List of PDFMiner text objects.
    """
    if LTType == "char":
        LTObject = LTChar
    elif LTType == "lh":
        LTObject = LTTextLineHorizontal
    elif LTType == "lv":
        LTObject = LTTextLineVertical
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTObject):
                t.append(obj)
            else:
                t += get_text_objects(obj, LTType=LTType)
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