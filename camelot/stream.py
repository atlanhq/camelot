from __future__ import print_function, division
import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from .table import Table
from .utils import get_row_index, get_score, encode_list


__all__ = ['Stream']


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
                rows.append(temp)
                temp = []
                row_y = t.y0
            temp.append(t)
    rows.append(temp)
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
        raise ValueError("Text doesn't fit any column.")
    c_idx = lt_col_overlap.index(max(lt_col_overlap))
    if t.x0 < columns[c_idx][0]:
        offset1 = abs(t.x0 - columns[c_idx][0])
    if t.x1 > columns[c_idx][1]:
        offset2 = abs(t.x1 - columns[c_idx][1])
    Y = abs(t.y0 - t.y1)
    charea = abs(t.x0 - t.x1) * abs(t.y0 - t.y1)
    error = (Y * (offset1 + offset2)) / charea
    return c_idx, error


def _col_ops(cols, width):
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

    def __init__(self, pdfobject, ncolumns=0, columns=None, ytol=2, mtol=2,
                 ctol=10, debug=False, verbose=False):

        self.pdfobject = pdfobject
        self.ncolumns = ncolumns
        self.columns = columns
        self.ytol = ytol
        self.mtol = mtol
        self.ctol = ctol
        self.debug = debug
        self.verbose = verbose
        self.tables = {}
        self.scores_ = {}
        if self.debug:
            self.debug_text = {}

    def get_tables(self):
        """Returns all tables found in given pdf.

        Returns
        -------
        tables : dict
            Dictionary with page number as key and list of tables on that
            page as value.
        """
        vprint = print if self.verbose else lambda *a, **k: None
        self.pdfobject.split()
        for page in self.pdfobject.extract():
            p, __, text, width, height = page
            pkey = 'page-{0}'.format(p)
            text.sort(key=lambda x: (-x.y0, x.x0))

            if not text:
                vprint("{0} contains no text.".format(pkey))
                continue

            if self.debug:
                self.debug_text[pkey] = text

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
                        raise ValueError("The number of columns after merge"
                                         " isn't the same as what you specified."
                                         " Change the value of mtol.")
                    cols = _col_ops(cols, width)
                else:
                    guess = True
                    ncols = max(set(elements), key=elements.count)
                    len_non_mode = len(filter(lambda x: x != ncols, elements))
                    if ncols == 1 and not self.debug:
                        # no tables detected
                        raise UserWarning("Only one column was detected, the PDF"
                                          " may have no tables. Specify ncols if"
                                          " the PDF has tables.")
                    cols = [(t.x0, t.x1)
                        for r in rows_grouped if len(r) == ncols for t in r]
                    cols = _merge_columns(sorted(cols), mtol=self.mtol)
                    outer_text = [t for t in text if t.x0 > cols[-1][1] or t.x1 < cols[0][0]]
                    if outer_text:
                        outer_text = _group_rows(outer_text, ytol=self.ytol)
                        outer_elements = [len(r) for r in outer_text]
                        outer_cols = [(t.x0, t.x1)
                            for r in outer_text if len(r) == max(outer_elements) for t in r]
                        cols.extend(_merge_columns(sorted(outer_cols)))
                    cols = _col_ops(cols, width)

            table = Table(cols, rows)
            rerror = []
            cerror = []
            for t in text:
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
            ar = table.get_list()
            if guess:
                score = get_score([[33, rerror], [33, cerror], [34, [len_non_mode / len(elements)]]])
            else:
                score = get_score([[50, rerror], [50, cerror]])
            self.scores_[pkey] = score
            vprint("Assigned text to each cell with a score of {0:.2f}".format(score))
            self.tables[pkey] = [encode_list(ar)]
            vprint("Finished processing {0}".format(pkey))

        if self.pdfobject.clean:
            self.pdfobject.remove_tempdir()

        if self.debug:
            return None

        return self.tables

    def plot_text(self):
        """Plots all text objects so user can choose number of columns
        or columns x-coordinates using the matplotlib interface.
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        for pkey in sorted(self.debug_text.keys()):
            fig = plt.figure()
            ax = fig.add_subplot(111, aspect='equal')
            xs, ys = [], []
            for t in self.debug_text[pkey]:
                xs.extend([t.x0, t.x1])
                ys.extend([t.y0, t.y1])
                ax.add_patch(
                    patches.Rectangle(
                        (t.x0, t.y0),
                        t.x1 - t.x0,
                        t.y1 - t.y0
                    )
                )
            ax.set_xlim(min(xs) - 10, max(xs) + 10)
            ax.set_ylim(min(ys) - 10, max(ys) + 10)
            plt.show()
