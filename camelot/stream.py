from __future__ import division
import os
import types
import copy_reg
import logging

import numpy as np

from .table import Table
from .utils import get_row_index, get_score, count_empty, encode_list, pdf_to_text


__all__ = ['Stream']


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


def _group_rows(text, ytol=2):
    """Groups text objects into rows using ytol.

    Parameters
    ----------
    text : list
        List of text objects.

    ytol : int
        Tolerance to account for when grouping rows
        together. (optional, default: 2)

    Returns
    -------
    rows : list
        List of grouped text rows.
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


def _merge_columns(l, mtol=2):
    """Merges overlapping columns and returns list with updated
    columns boundaries.

    Parameters
    ----------
    l : list
        List of column x-coordinates.

    Returns
    -------
    merged : list
        List of merged column x-coordinates.
    """
    merged = []
    for higher in l:
        if not merged:
            merged.append(higher)
        else:
            lower = merged[-1]
            if (higher[0] <= lower[1] or
                    np.isclose(higher[0], lower[1], atol=mtol)):
                upper_bound = max(lower[1], higher[1])
                lower_bound = min(lower[0], higher[0])
                merged[-1] = (lower_bound, upper_bound)
            else:
                merged.append(higher)
    return merged


def _get_column_index(t, columns):
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


def _add_columns(cols, text, ytolerance):
    if text:
        text = _group_rows(text, ytol=ytolerance)
        elements = [len(r) for r in text]
        new_cols = [(t.x0, t.x1)
            for r in text if len(r) == max(elements) for t in r]
        cols.extend(_merge_columns(sorted(new_cols)))
    return cols


def _join_columns(cols, width):
    cols = sorted(cols)
    cols = [(cols[i][0] + cols[i - 1][1]) / 2 for i in range(1, len(cols))]
    cols.insert(0, 0)
    cols.append(width) # or some tolerance
    cols = [(cols[i], cols[i + 1])
            for i in range(0, len(cols) - 1)]
    return cols


class Stream:
    """Stream algorithm

    Groups text objects into rows and guesses number of columns
    using mode of the number of text objects in each row.

    The number of columns can be passed explicitly or specified by a
    list of column x-coordinates.

    Parameters
    ----------
    pdfobject : camelot.pdf.Pdf

    ncolumns : int
        Number of columns. (optional, default: 0)

    columns : string
        Comma-separated list of column x-coordinates.
        (optional, default: None)

    ytol : int
        Tolerance to account for when grouping rows
        together. (optional, default: 2)

    debug : bool
        Debug by visualizing textboxes. (optional, default: False)

    Attributes
    ----------
    tables : dict
        Dictionary with page number as key and list of tables on that
        page as value.
    """

    def __init__(self, ncolumns=0, columns=None, ytol=2, mtol=2,
                 pdf_margin=(2.0, 0.5, 0.1), debug=False):

        self.method = 'stream'
        self.ncolumns = ncolumns
        self.columns = columns
        self.ytol = ytol
        self.mtol = mtol
        self.char_margin, self.line_margin, self.word_margin = pdf_margin
        self.debug = debug

    def get_tables(self, pdfname):
        """Returns all tables found in given pdf.

        Returns
        -------
        tables : dict
            Dictionary with page number as key and list of tables on that
            page as value.
        """
        __, text, width, height = pdf_to_text(pdfname, self.char_margin,
            self.line_margin, self.word_margin)
        bname, __ = os.path.splitext(pdfname)
        if not text:
            logging.warning("{0}: PDF has no text. It may be an image.".format(
                os.path.basename(bname)))
            return None
        text.sort(key=lambda x: (-x.y0, x.x0))

        if self.debug:
            self.debug_text = [(t.x0, t.y0, t.x1, t.y1) for t in text]
            return None

        rows_grouped = _group_rows(text, ytol=self.ytol)
        elements = [len(r) for r in rows_grouped]
        row_mids = [sum([(t.y0 + t.y1) / 2 for t in r]) / len(r)
                    if len(r) > 0 else 0 for r in rows_grouped]
        rows = [(row_mids[i] + row_mids[i - 1]) / 2 for i in range(1, len(row_mids))]
        rows.insert(0, height) # or some tolerance
        rows.append(0)
        rows = [(rows[i], rows[i + 1])
                for i in range(0, len(rows) - 1)]

        guess = False
        if self.columns:
            # user has to input boundary columns too
            # take (0, width) by default
            # similar to else condition
            # len can't be 1
            cols = self.columns.split(',')
            cols = [(float(cols[i]), float(cols[i + 1]))
                    for i in range(0, len(cols) - 1)]
        else:
            if self.ncolumns:
                ncols = self.ncolumns
                cols = [(t.x0, t.x1)
                    for r in rows_grouped if len(r) == ncols for t in r]
                cols = _merge_columns(sorted(cols), mtol=self.mtol)
                if len(cols) != self.ncolumns:
                    logging.warning("{}: The number of columns after merge"
                                  " isn't the same as what you specified."
                                  " Change the value of mtol.".format(
                                  os.path.basename(bname)))
                cols = _join_columns(cols, width)
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
                cols = _merge_columns(sorted(cols), mtol=self.mtol)
                inner_text = []
                for i in range(1, len(cols)):
                    left = cols[i - 1][1]
                    right = cols[i][0]
                    inner_text.extend([t for t in text if t.x0 > left and t.x1 < right])
                outer_text = [t for t in text if t.x0 > cols[-1][1] or t.x1 < cols[0][0]]
                inner_text.extend(outer_text)
                cols = _add_columns(cols, inner_text, self.ytol)
                cols = _join_columns(cols, width)

        pdf_page = {}
        page_tables = {}
        table_info = {}
        table = Table(cols, rows)
        rerror = []
        cerror = []
        for row in rows_grouped:
            for t in row:
                try:
                    r_idx, rass_error = get_row_index(t, rows)
                except ValueError as e:
                    # couldn't assign LTTextLH to any cell
                    vprint(e.message)
                    continue
                try:
                    c_idx, cass_error = _get_column_index(t, cols)
                except ValueError as e:
                    # couldn't assign LTTextLH to any cell
                    vprint(e.message)
                    continue
                rerror.append(rass_error)
                cerror.append(cass_error)
                table.cells[r_idx][c_idx].add_text(
                    t.get_text().strip('\n'))
        if guess:
            score = get_score([[33, rerror], [33, cerror], [34, [len_non_mode / len(elements)]]])
        else:
            score = get_score([[50, rerror], [50, cerror]])
        table_info['score'] = score
        ar = table.get_list()
        ar = encode_list(ar)
        table_info['data'] = ar
        empty_p, r_nempty_cells, c_nempty_cells = count_empty(ar)
        table_info['empty_p'] = empty_p
        table_info['r_nempty_cells'] = r_nempty_cells
        table_info['c_nempty_cells'] = c_nempty_cells
        table_info['nrows'] = len(ar)
        table_info['ncols'] = len(ar[0])
        page_tables['table_1'] = table_info
        pdf_page[os.path.basename(bname)] = page_tables

        return pdf_page