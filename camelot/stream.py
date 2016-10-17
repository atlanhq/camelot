from __future__ import division
import os
import types
import logging
import copy_reg

import numpy as np

from .table import Table
from .utils import (rotate, get_rotation, rotate_textlines, text_in_bbox,
                    get_table_index, get_score, count_empty, encode_list,
                    get_text_objects, get_page_layout)


__all__ = ['Stream']


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


def _text_bbox(t_bbox):
    """Returns bounding box for the text present on a page.

    Parameters
    ----------
    t_bbox : dict
        Dict with two keys 'horizontal' and 'vertical' with lists of
        LTTextLineHorizontals and LTTextLineVerticals respectively.

    Returns
    -------
    text_bbox : tuple
        Tuple of the form (x0, y0, x1, y1) in PDFMiner's coordinate
        space.
    """
    xmin = min([t.x0 for direction in t_bbox for t in t_bbox[direction]])
    ymin = min([t.y0 for direction in t_bbox for t in t_bbox[direction]])
    xmax = max([t.x1 for direction in t_bbox for t in t_bbox[direction]])
    ymax = max([t.y1 for direction in t_bbox for t in t_bbox[direction]])
    text_bbox = (xmin, ymin, xmax, ymax)
    return text_bbox


def _group_rows(text, ytol=2):
    """Groups PDFMiner text objects into rows using their
    y-coordinates taking into account some tolerance ytol.

    Parameters
    ----------
    text : list
        List of PDFMiner text objects.

    ytol : int
        Tolerance parameter.
        (optional, default: 2)

    Returns
    -------
    rows : list
        Two-dimensional list of text objects grouped into rows.
    """
    row_y = 0
    rows = []
    temp = []
    for t in text:
        # is checking for upright necessary?
        # if t.get_text().strip() and all([obj.upright for obj in t._objs if
        # type(obj) is LTChar]):
        if t.get_text().strip():
            if not np.isclose(row_y, t.y0, atol=ytol):
                rows.append(sorted(temp, key=lambda t: t.x0))
                temp = []
                row_y = t.y0
            temp.append(t)
    rows.append(sorted(temp, key=lambda t: t.x0))
    __ = rows.pop(0) # hacky
    return rows


def _merge_columns(l, mtol=0):
    """Merges column boundaries if they overlap or lie within some
    tolerance mtol.

    Parameters
    ----------
    l : list
        List of column coordinate tuples.

    mtol : int
        TODO
        (optional, default: 0)

    Returns
    -------
    merged : list
        List of merged column coordinate tuples.
    """
    merged = []
    for higher in l:
        if not merged:
            merged.append(higher)
        else:
            lower = merged[-1]
            if mtol >= 0:
                if (higher[0] <= lower[1] or
                        np.isclose(higher[0], lower[1], atol=mtol)):
                    upper_bound = max(lower[1], higher[1])
                    lower_bound = min(lower[0], higher[0])
                    merged[-1] = (lower_bound, upper_bound)
                else:
                    merged.append(higher)
            elif mtol < 0:
                if higher[0] <= lower[1]:
                    if np.isclose(higher[0], lower[1], atol=abs(mtol)):
                        merged.append(higher)
                    else:
                        upper_bound = max(lower[1], higher[1])
                        lower_bound = min(lower[0], higher[0])
                        merged[-1] = (lower_bound, upper_bound)
                else:
                    merged.append(higher)
    return merged


def _join_rows(rows_grouped, text_y_max, text_y_min):
    """Makes row coordinates continuous.

    Parameters
    ----------
    rows_grouped : list
        Two-dimensional list of text objects grouped into rows.

    text_y_max : int

    text_y_min : int

    Returns
    -------
    rows : list
        List of continuous row coordinate tuples.
    """
    row_mids = [sum([(t.y0 + t.y1) / 2 for t in r]) / len(r)
                if len(r) > 0 else 0 for r in rows_grouped]
    rows = [(row_mids[i] + row_mids[i - 1]) / 2 for i in range(1, len(row_mids))]
    rows.insert(0, text_y_max)
    rows.append(text_y_min)
    rows = [(rows[i], rows[i + 1])
            for i in range(0, len(rows) - 1)]
    return rows


def _join_columns(cols, text_x_min, text_x_max):
    """Makes column coordinates continuous.

    Parameters
    ----------
    cols : list
        List of column coordinate tuples.

    text_x_min : int

    text_y_max : int

    Returns
    -------
    cols : list
        Updated list of column coordinate tuples.
    """
    cols = sorted(cols)
    cols = [(cols[i][0] + cols[i - 1][1]) / 2 for i in range(1, len(cols))]
    cols.insert(0, text_x_min)
    cols.append(text_x_max)
    cols = [(cols[i], cols[i + 1])
            for i in range(0, len(cols) - 1)]
    return cols


def _add_columns(cols, text, ytol):
    """Adds columns to existing list by taking into account
    the text that lies outside the current column coordinates.

    Parameters
    ----------
    cols : list
        List of column coordinate tuples.

    text : list
        List of PDFMiner text objects.

    ytol : int
        Tolerance parameter.

    Returns
    -------
    cols : list
        Updated list of column coordinate tuples.
    """
    if text:
        text = _group_rows(text, ytol=ytol)
        elements = [len(r) for r in text]
        new_cols = [(t.x0, t.x1)
            for r in text if len(r) == max(elements) for t in r]
        cols.extend(_merge_columns(sorted(new_cols)))
    return cols


class Stream:
    """Stream looks for spaces between text elements to form a table.

    If you want to give columns, ncolumns, ytol or mtol for each table
    when specifying multiple table areas, make sure that their length
    is equal to the length of table_area. Mapping between them is based
    on index.

    Also, if you want to specify columns for the first table and
    ncolumns for the second table in a pdf having two tables, pass
    columns as ['x1,x2,x3,x4', ''] and ncolumns as [-1, 5].

    Parameters
    ----------
    table_area : list
        List of strings of the form x1,y1,x2,y2 where
        (x1, y1) -> left-top and (x2, y2) -> right-bottom in PDFMiner's
        coordinate space, denoting table areas to analyze.
        (optional, default: None)

    columns : list
        List of strings where each string is comma-separated values of
        x-coordinates in PDFMiner's coordinate space.
        (optional, default: None)

    ncolumns : list
        List of ints specifying the number of columns in each table.
        (optional, default: None)

    headers : list
        List of strings where each string is a csv header for a table.
        (optional, default: None)

    ytol : list
        List of ints specifying the y-tolerance parameters.
        (optional, default: [2])

    mtol : list
        List of ints specifying the m-tolerance parameters.
        (optional, default: [0])

    margins : tuple
        PDFMiner margins. (char_margin, line_margin, word_margin)
        (optional, default: (1.0, 0.5, 0.1))

    split_text : bool
        Whether or not to split a text line if it spans across
        different cells.
        (optional, default: False)

    flag_size : bool
        Whether or not to highlight a substring using <s></s>
        if its size is different from rest of the string, useful for
        super and subscripts.
        (optional, default: True)

    debug : bool
        Set to True to generate a matplotlib plot of
        LTTextLineHorizontals in order to select table_area, columns.
        (optional, default: False)
    """
    def __init__(self, table_area=None, columns=None, ncolumns=None,
                 headers=None, ytol=[2], mtol=[0], margins=(1.0, 0.5, 0.1),
                 split_text=False, flag_size=True, debug=False):

        self.method = 'stream'
        self.table_area = table_area
        self.columns = columns
        self.ncolumns = ncolumns
        self.ytol = ytol
        self.mtol = mtol
        self.headers = headers
        self.char_margin, self.line_margin, self.word_margin = margins
        self.split_text = split_text
        self.flag_size = flag_size
        self.debug = debug

    def get_tables(self, pdfname):
        """get_tables

        Parameters
        ---------
        pdfname : string
            Path to single page pdf file.

        Returns
        -------
        page : dict
        """
        layout, dim = get_page_layout(pdfname, char_margin=self.char_margin,
            line_margin=self.line_margin, word_margin=self.word_margin)
        lttextlh = get_text_objects(layout, ltype="lh")
        lttextlv = get_text_objects(layout, ltype="lv")
        ltchar = get_text_objects(layout, ltype="char")
        width, height = dim
        bname, __ = os.path.splitext(pdfname)
        if not lttextlh:
            logging.warning("{0}: PDF has no text. It may be an image.".format(
                os.path.basename(bname)))
            return None

        if self.debug:
            self.debug_text = []
            self.debug_text.extend([(t.x0, t.y0, t.x1, t.y1) for t in lttextlh])
            self.debug_text.extend([(t.x0, t.y0, t.x1, t.y1) for t in lttextlv])

        if self.table_area is not None:
            if self.columns is not None:
                if len(self.table_area) != len(self.columns):
                    raise ValueError("Length of columns should be equal to table_area.")
            if self.ncolumns is not None:
                if len(self.table_area) != len(self.ncolumns):
                    raise ValueError("Length of ncolumns should be equal to table_area.")
            if self.headers is not None:
                if len(self.table_area) != len(self.headers):
                    raise ValueError("Length of headers should be equal to table_area.")

            table_bbox = {}
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = float(x1)
                y1 = float(y1)
                x2 = float(x2)
                y2 = float(y2)
                table_bbox[(x1, y2, x2, y1)] = None
        else:
            table_bbox = {(0, 0, width, height): None}

        if len(self.ytol) == 1 and self.ytol[0] == 2:
            self.ytol = self.ytol * len(table_bbox)
        if len(self.mtol) == 1 and self.mtol[0] == 0:
            self.mtol = self.mtol * len(table_bbox)

        page = {}
        tables = {}
        table_no = 0
        # sort tables based on y-coord
        for k in sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True):
            # select elements which lie within table_bbox
            table_data = {}
            lh_bbox = text_in_bbox(k, lttextlh)
            lv_bbox = text_in_bbox(k, lttextlv)
            char_bbox = text_in_bbox(k, ltchar)
            table_data['text_p'] = 100 * (1 - (len(char_bbox) / len(ltchar)))
            table_rotation = get_rotation(lh_bbox, lv_bbox, char_bbox)
            t_bbox = rotate_textlines(lh_bbox, lv_bbox, table_rotation)
            for direction in t_bbox:
                t_bbox[direction].sort(key=lambda x: (-x.y0, x.x0))
            text_x_min, text_y_min, text_x_max, text_y_max = _text_bbox(t_bbox)
            rows_grouped = _group_rows(t_bbox['horizontal'], ytol=self.ytol[table_no])
            rows = _join_rows(rows_grouped, text_y_max, text_y_min)
            elements = [len(r) for r in rows_grouped]

            guess = False
            if self.columns is not None and self.columns[table_no] != "":
                # user has to input boundary columns too
                # take (0, width) by default
                # similar to else condition
                # len can't be 1
                cols = self.columns[table_no].split(',')
                cols = [float(c) for c in cols]
                if table_rotation != '':
                    if table_rotation == 'left':
                        cols = [rotate(0, 0, 0, c, -np.pi / 2)[0] for c in cols]
                    elif table_rotation == 'right':
                        cols = [rotate(0, 0, 0, c, np.pi / 2)[0] for c in cols]
                cols.insert(0, text_x_min)
                cols.append(text_x_max)
                cols = [(cols[i], cols[i + 1]) for i in range(0, len(cols) - 1)]
            else:
                if self.ncolumns is not None and self.ncolumns[table_no] != -1:
                    ncols = self.ncolumns[table_no]
                    cols = [(t.x0, t.x1)
                        for r in rows_grouped if len(r) == ncols for t in r]
                    cols = _merge_columns(sorted(cols), mtol=self.mtol[table_no])
                    if len(cols) != self.ncolumns[table_no]:
                        logging.warning("{}: The number of columns after merge"
                                      " isn't the same as what you specified."
                                      " Change the value of mtol.".format(
                                      os.path.basename(bname)))
                    cols = _join_columns(cols, text_x_min, text_x_max)
                else:
                    guess = True
                    ncols = max(set(elements), key=elements.count)
                    len_non_mode = len(filter(lambda x: x != ncols, elements))
                    if ncols == 1 and not self.debug:
                        # no tables detected
                        logging.warning("{}: Only one column was detected, the pdf"
                                      " may have no tables. Specify ncols if"
                                      " the pdf has tables.".format(
                                      os.path.basename(bname)))
                    cols = [(t.x0, t.x1)
                        for r in rows_grouped if len(r) == ncols for t in r]
                    cols = _merge_columns(sorted(cols), mtol=self.mtol[table_no])
                    inner_text = []
                    for i in range(1, len(cols)):
                        left = cols[i - 1][1]
                        right = cols[i][0]
                        inner_text.extend([t for direction in t_bbox
                                           for t in t_bbox[direction]
                                           if t.x0 > left and t.x1 < right])
                    outer_text = [t for direction in t_bbox
                                  for t in t_bbox[direction]
                                  if t.x0 > cols[-1][1] or t.x1 < cols[0][0]]
                    inner_text.extend(outer_text)
                    cols = _add_columns(cols, inner_text, self.ytol[table_no])
                    cols = _join_columns(cols, text_x_min, text_x_max)

            if self.headers is not None and self.headers[table_no] != [""]:
                self.headers[table_no] = self.headers[table_no].split(',')
                if len(self.headers[table_no]) != len(cols):
                    logging.warning("Length of header ({0}) specified for table is not"
                                    " equal to the number of columns ({1}) detected.".format(
                                    len(self.headers[table_no]), len(cols)))
                while len(self.headers[table_no]) != len(cols):
                    self.headers[table_no].append('')

            table = Table(cols, rows)
            table = table.set_all_edges()
            assignment_errors = []
            table_data['split_text'] = []
            table_data['superscript'] = []
            for direction in t_bbox:
                for t in t_bbox[direction]:
                    indices, error = get_table_index(
                        table, t, direction, split_text=self.split_text,
                        flag_size=self.flag_size)
                    assignment_errors.append(error)
                    if len(indices) > 1:
                        table_data['split_text'].append(indices)
                    for r_idx, c_idx, text in indices:
                        if all(s in text for s in ['<s>', '</s>']):
                            table_data['superscript'].append((r_idx, c_idx, text))
                        table.cells[r_idx][c_idx].add_text(text)
            if guess:
                score = get_score([[66, assignment_errors], [34, [len_non_mode / len(elements)]]])
            else:
                score = get_score([[100, assignment_errors]])

            table_data['score'] = score
            ar = table.get_list()
            if self.headers is not None and self.headers[table_no] != ['']:
                ar.insert(0, self.headers[table_no])
            ar = encode_list(ar)
            table_data['data'] = ar
            empty_p, r_nempty_cells, c_nempty_cells = count_empty(ar)
            table_data['empty_p'] = empty_p
            table_data['r_nempty_cells'] = r_nempty_cells
            table_data['c_nempty_cells'] = c_nempty_cells
            table_data['nrows'] = len(ar)
            table_data['ncols'] = len(ar[0])
            tables['table-{0}'.format(table_no + 1)] = table_data
            table_no += 1
        page[os.path.basename(bname)] = tables

        return page