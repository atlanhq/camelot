from __future__ import division
import os
import types
import logging
import copy_reg

import numpy as np

from .table import Table
from .utils import (rotate, get_rotation, text_bbox, get_row_index, get_score,
                    count_empty, encode_list, get_text_objects, get_page_layout)


__all__ = ['Stream']


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


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


def _get_column_index(t, columns):
    """Gets index of the column in which the given text object lies by
    comparing their x-coordinates.

    Parameters
    ----------
    t : object

    columns : list
        List of column coordinate tuples.

    Returns
    -------
    c_idx : int

    error : float
    """
    offset1, offset2 = 0, 0
    lt_col_overlap = []
    for c in columns:
        if c[0] <= t.x1 and c[1] >= t.x0:
            left = t.x0 if c[0] <= t.x0 else c[0]
            right = t.x1 if c[1] >= t.x1 else c[1]
            lt_col_overlap.append(abs(left - right) / abs(c[0] - c[1]))
        else:
            lt_col_overlap.append(-1)
    if len(filter(lambda x: x != -1, lt_col_overlap)) == 0:
        logging.warning("Text doesn't fit any column.")
    c_idx = lt_col_overlap.index(max(lt_col_overlap))
    if t.x0 < columns[c_idx][0]:
        offset1 = abs(t.x0 - columns[c_idx][0])
    if t.x1 > columns[c_idx][1]:
        offset2 = abs(t.x1 - columns[c_idx][1])
    Y = abs(t.y0 - t.y1)
    charea = abs(t.x0 - t.x1) * abs(t.y0 - t.y1)
    error = (Y * (offset1 + offset2)) / charea
    return c_idx, error


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
        List of tuples of the form (x1, y1, x2, y2) where
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

    ytol : list
        List of ints specifying the y-tolerance parameters.
        (optional, default: [2])

    mtol : list
        List of ints specifying the m-tolerance parameters.
        (optional, default: [0])

    margins : tuple
        PDFMiner margins. (char_margin, line_margin, word_margin)
        (optional, default: (1.0, 0.5, 0.1))

    debug : bool
        Set to True to generate a matplotlib plot of
        LTTextLineHorizontals in order to select table_area, columns.
        (optional, default: False)
    """
    def __init__(self, table_area=None, columns=None, ncolumns=None, ytol=[2],
                 mtol=[0], margins=(1.0, 0.5, 0.1), debug=False):

        self.method = 'stream'
        self.table_area = table_area
        self.columns = columns
        self.ncolumns = ncolumns
        self.ytol = ytol
        self.mtol = mtol
        self.char_margin, self.line_margin, self.word_margin = margins
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
        ltchar = get_text_objects(layout, LTType="char")
        lttextlh = get_text_objects(layout, LTType="lh")
        lttextlv = get_text_objects(layout, LTType="lv")
        width, height = dim
        bname, __ = os.path.splitext(pdfname)
        if not lttextlh:
            logging.warning("{0}: PDF has no text. It may be an image.".format(
                os.path.basename(bname)))
            return None

        if self.debug:
            self.debug_text = []

        if self.table_area is not None:
            if self.columns is not None:
                if len(self.table_area) != len(self.columns):
                    raise ValueError("Length of columns should be equal to table_area.")
            if self.ncolumns is not None:
                if len(self.table_area) != len(self.ncolumns):
                    raise ValueError("Length of ncolumns should be equal to table_area.")
            table_bbox = {}
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)
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
            table_rotation = get_rotation(ltchar, lttextlh, lttextlv)
            if table_rotation != '':
                t_bbox = text_bbox(k, lttextlv)
                if table_rotation == 'left':
                    if self.debug:
                        self.debug_text.extend([(t.x0, t.y0, t.x1, t.y1) for t in lttextlv])
                    for t in t_bbox:
                        x0, y0, x1, y1 = t.bbox
                        x0, y0 = rotate(0, 0, x0, y0, -np.pi / 2)
                        x1, y1 = rotate(0, 0, x1, y1, -np.pi / 2)
                        t.set_bbox((x0, y1, x1, y0))
                elif table_rotation == 'right':
                    for t in t_bbox:
                        x0, y0, x1, y1 = t.bbox
                        x0, y0 = rotate(0, 0, x0, y0, np.pi / 2)
                        x1, y1 = rotate(0, 0, x1, y1, np.pi / 2)
                        t.set_bbox((x1, y0, x0, y1))
            else:
                if self.debug:
                    self.debug_text.extend([(t.x0, t.y0, t.x1, t.y1) for t in lttextlh])
                t_bbox = text_bbox(k, lttextlh)
            t_bbox.sort(key=lambda x: (-x.y0, x.x0))

            text_x_min = min([t.x0 for t in t_bbox])
            text_y_min = min([t.y0 for t in t_bbox])
            text_x_max = max([t.x1 for t in t_bbox])
            text_y_max = max([t.y1 for t in t_bbox])
            rows_grouped = _group_rows(t_bbox, ytol=self.ytol[table_no])
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
                        logging.warning("{}: Only one column was detected, the PDF"
                                      " may have no tables. Specify ncols if"
                                      " the PDF has tables.".format(
                                      os.path.basename(bname)))
                    cols = [(t.x0, t.x1)
                        for r in rows_grouped if len(r) == ncols for t in r]
                    cols = _merge_columns(sorted(cols), mtol=self.mtol[table_no])
                    inner_text = []
                    for i in range(1, len(cols)):
                        left = cols[i - 1][1]
                        right = cols[i][0]
                        inner_text.extend([t for t in t_bbox if t.x0 > left and t.x1 < right])
                    outer_text = [t for t in t_bbox if t.x0 > cols[-1][1] or t.x1 < cols[0][0]]
                    inner_text.extend(outer_text)
                    cols = _add_columns(cols, inner_text, self.ytol[table_no])
                    cols = _join_columns(cols, text_x_min, text_x_max)

            table = Table(cols, rows)
            rerror = []
            cerror = []
            for row in rows_grouped:
                for t in row:
                    try:
                        r_idx, rass_error = get_row_index(t, rows)
                    except ValueError as e:
                        # couldn't assign LTTextLH to any cell
                        continue
                    try:
                        c_idx, cass_error = _get_column_index(t, cols)
                    except ValueError as e:
                        # couldn't assign LTTextLH to any cell
                        continue
                    rerror.append(rass_error)
                    cerror.append(cass_error)
                    table.cells[r_idx][c_idx].add_text(
                        t.get_text().strip('\n'))
            if guess:
                score = get_score([[33, rerror], [33, cerror], [34, [len_non_mode / len(elements)]]])
            else:
                score = get_score([[50, rerror], [50, cerror]])

            table_data['score'] = score
            ar = table.get_list()
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