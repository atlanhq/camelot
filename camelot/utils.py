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


def affine_transform(factors, x1, y1, x2, y2):
    scaling_factor_x, scaling_factor_y, img_y = factors
    x1 = scale(x1, scaling_factor_x)
    x2 = scale(x2, scaling_factor_x)
    y1 = scale(abs(translate(-img_y, y1)), scaling_factor_y)
    y2 = scale(abs(translate(-img_y, y2)), scaling_factor_y)
    return int(x1), int(y1), int(x2), int(y2)


def scale_to_pdf(tables, hierarchy, v_segments, h_segments, factors):
    """Translates and scales OpenCV coordinates to PDFMiner's coordinate
    space.

    Parameters
    ----------
    tables : dict
        Dict with table boundaries as keys and list of intersections
        in that boundary as their value.

    hierarchy : dict

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

    hierarchy_new : dict

    v_segments_new : dict

    h_segments_new : dict
    """
    scaling_factor_x, scaling_factor_y, img_y = factors

    tables_new = {}
    for k in tables.keys():
        x1, y1, x2, y2 = affine_transform(factors, *k)
        if tables[k]:
            j_x, j_y = zip(*tables[k])
            j_x = [scale(j, scaling_factor_x) for j in j_x]
            j_y = [scale(abs(translate(-img_y, j)), scaling_factor_y) for j in j_y]
            joints = zip(j_x, j_y)
            tables_new[(x1, y1, x2, y2)] = joints

    hierarchy_new = {}
    for k in hierarchy.keys():
        x1, y1, x2, y2 = affine_transform(factors, *k)
        hierarchy_new[(x1, y1, x2, y2)] = []
        for v in hierarchy[k]:
            vx1, vy1, vx2, vy2 = affine_transform(factors, *v)
            hierarchy_new[(x1, y1, x2, y2)].append((vx1, vy1, vx2, vy2))

    v_segments_new = []
    for v in v_segments:
        x1, y1, x2, y2 = affine_transform(factors, *v)
        v_segments_new.append((x1, y1, x2, y2))

    h_segments_new = []
    for h in h_segments:
        x1, y1, x2, y2 = affine_transform(factors, *h)
        h_segments_new.append((x1, y1, x2, y2))

    return tables_new, hierarchy_new, v_segments_new, h_segments_new


def setup_logging(log_filepath):
    """Setup logging
    Args:
        log_filepath (string): Path to log file
    Returns:
        logging.Logger: Logger object
    """
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.DEBUG)
    # Log File Handler (Associating one log file per webservice run)
    log_file_handler = logging.FileHandler(log_filepath,
                                           mode='a',
                                           encoding='utf-8')
    log_file_handler.setLevel(logging.DEBUG)
    format_string = '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    formatter = logging.Formatter(format_string, datefmt='%Y-%m-%dT%H:%M:%S')
    log_file_handler.setFormatter(formatter)
    logger.addHandler(log_file_handler)
    # Stream Log Handler (For console)
    stream_log_handler = logging.StreamHandler()
    stream_log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(format_string, datefmt='%Y-%m-%dT%H:%M:%S')
    stream_log_handler.setFormatter(formatter)
    logger.addHandler(stream_log_handler)
    return logger


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


def to_wh(tup):
    return tup[0], tup[1], tup[2] - tup[0], tup[3] - tup[1]


def find_parent(hierarchy, contour):
    if contour in hierarchy.keys():
        children = hierarchy[contour] if hierarchy[contour] else ()
        return contour, children
    for key, value in hierarchy.iteritems():
        if contour in value:
            return contour, ()
    return contour, None


def segments_bbox(v_segments, h_segments, bbox, hierarchy=None):
    """Returns all line segments present inside a
    table's bounding box.

    Parameters
    ----------
    bbox : tuple
        Tuple (x1, y1, x2, y2) representing table bounding box where
        (x1, y1) -> lb and (x2, y2) -> rt in PDFMiner's coordinate space.

    hierarchy : dict

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
    def filter_segments(v_segments, h_segments, bbox):
        px1, py1, px2, py2 = bbox
        v_s = [v for v in v_segments if v[1] > py1 - 2 and v[3] < py2 + 2 and \
               px1 - 2 <= v[0] <= px2 + 2]
        h_s = [h for h in h_segments if h[0] > px1 - 2 and h[2] < px2 + 2 and \
               py1 - 2 <= h[1] <= py2 + 2]
        return v_s, h_s

    v_s, h_s = ([] for i in range(2))
    if hierarchy is not None:
        parent, children = find_parent(hierarchy, bbox)
        if children is not None:
            v_s, h_s = filter_segments(v_segments, h_segments, parent)
            if isinstance(children, list):
                v_s_child, h_s_child = ([] for i in range(2))
                for child in children:
                    vtemp, htemp = filter_segments(v_s, h_s, child)
                    v_s_child.extend(vtemp)
                    h_s_child.extend(htemp)
                v_s = list(set(v_s).difference(set(v_s_child)))
                h_s = list(set(h_s).difference(set(h_s_child)))
    else:
        v_s, h_s = filter_segments(v_segments, h_segments, bbox)
    return v_s, h_s


def text_bbox(text, bbox, hierarchy=None):
    """Returns all text objects present inside a
    table's bounding box.

    Parameters
    ----------
    bbox : tuple
        Tuple (x1, y1, x2, y2) representing table bounding box where
        (x1, y1) -> lb and (x2, y2) -> rt in PDFMiner's coordinate space.

    hierarchy : dict

    text : list
        List of PDFMiner text objects.

    Returns
    -------
    t_bbox : list
        List of PDFMiner text objects that lie inside table.
    """
    def filter_text(text, bbox):
        px1, py1, px2, py2 = bbox
        t_bbox = [t for t in text if px1 - 2 <= (t.x0 + t.x1) / 2.0 <= px2 + 2 and \
                  py1 - 2 <= (t.y0 + t.y1) / 2.0 <= py2 + 2]
        return t_bbox

    t_bbox = []
    if hierarchy is not None:
        parent, children = find_parent(hierarchy, bbox)
        if children is not None:
            t_bbox = filter_text(text, parent)
            if isinstance(children, list):
                t_bbox_child = []
                for child in children:
                    temp = filter_text(t_bbox, child)
                    t_bbox_child.extend(temp)
                t_bbox = list(set(t_bbox).difference(set(t_bbox_child)))
    else:
        t_bbox = filter_text(text, bbox)
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


def flag_on_size(textline, direction):
    """Flags a super/subscript by enclosing it with <s></s>. May give
    false positives.

    Parameters
    ----------
    textline : list
        List of PDFMiner LTChar objects.

    direction : string
        {'horizontal', 'vertical'}
        Direction of the PDFMiner LTTextLine object.

    Returns
    -------
    fstring : string
    """
    if direction == 'horizontal':
        d = [(t.get_text(), np.round(t.height, decimals=6)) for t in textline if not isinstance(t, LTAnno)]
    elif direction == 'vertical':
        d = [(t.get_text(), np.round(t.width, decimals=6)) for t in textline if not isinstance(t, LTAnno)]
    l = [np.round(size, decimals=6) for text, size in d]
    if len(set(l)) > 1:
        flist = []
        min_size = min(l)
        for key, chars in groupby(d, itemgetter(1)):
            if key == min_size:
                fchars = [t[0] for t in chars]
                if ''.join(fchars).strip():
                    fchars.insert(0, '<s>')
                    fchars.append('</s>')
                    flist.append(''.join(fchars))
            else:
                fchars = [t[0] for t in chars]
                if ''.join(fchars).strip():
                    flist.append(''.join(fchars))
        fstring = ''.join(flist).strip('\n')
    else:
        fstring = ''.join([t.get_text() for t in textline]).strip('\n')
    return fstring


def split_textline(table, textline, direction, flag_size=True):
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

    flag_size : bool
        Whether or not to highlight a substring using <s></s>
        if its size is different from rest of the string, useful for
        super and subscripts.
        (optional, default: True)

    Returns
    -------
    grouped_chars : list
        List of tuples of the form (idx, text) where idx is the index
        of row/column and text is the an lttextline substring.
    """
    idx = 0
    cut_text = []
    bbox = textline.bbox
    try:
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
                            cut_text.append((cut[0], c, obj))
                            break
                    elif isinstance(obj, LTAnno):
                        cut_text.append((cut[0], c, obj))
    except IndexError:
        return [(-1, -1, textline.get_text())]
    grouped_chars = []
    for key, chars in groupby(cut_text, itemgetter(0, 1)):
        if flag_size:
            grouped_chars.append((key[0], key[1], flag_on_size([t[2] for t in chars], direction)))
        else:
            gchars = [t[2].get_text() for t in chars]
            grouped_chars.append((key[0], key[1], ''.join(gchars).strip('\n')))
    return grouped_chars


def get_table_index(table, t, direction, split_text=False, flag_size=True):
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

    flag_size : bool
        Whether or not to highlight a substring using <s></s>
        if its size is different from rest of the string, useful for
        super and subscripts.
        (optional, default: True)

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
                logging.warning("Text did not fit any column.")
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
        return split_textline(table, t, direction, flag_size=flag_size), error
    else:
        if flag_size:
            return [(r_idx, c_idx, flag_on_size(t._objs, direction))], error
        else:
            return [(r_idx, c_idx, t.get_text().strip('\n'))], error


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
    try:
        score = 0
        if sum([ew[0] for ew in error_weights]) != SCORE_VAL:
            raise ValueError("Sum of weights should be equal to 100.")
        for ew in error_weights:
            weight = ew[0] / len(ew[1])
            for error_percentage in ew[1]:
                score += weight * (1 - error_percentage)
    except ZeroDivisionError:
        score = 0
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


def get_page_layout(pname, char_margin=1.0, line_margin=0.5, word_margin=0.1,
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


def merge_tuples(tuples):
    """Merges a list of overlapping tuples.

    Parameters
    ----------
    tuples : list

    Returns
    -------
    merged : list
    """
    merged = list(tuples[0])
    for s, e in tuples:
        if s <= merged[1]:
            merged[1] = max(merged[1], e)
        else:
            yield tuple(merged)
            merged[0] = s
            merged[1] = e
    yield tuple(merged)