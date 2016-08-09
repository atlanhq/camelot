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
    row_y = text[0].y0
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


def _get_column_index(t, columns, ctol=10):
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
    offset = 0
    for c in range(len(columns)):
        if columns[c][0] < t.x0 < columns[c][1]:
            if t.x1 > columns[c][1]:
                offset = abs(t.x1 - columns[c][1])
            Y = abs(t.y0 - t.y1)
            charea = abs(t.x0 - t.x1) * abs(t.y0 - t.y1)
            error1 = (Y * offset) / charea
            if abs(t.x0 - columns[c][1]) < ctol:
                try:
                    offset1, offset2 = 0, 0
                    if t.x0 < columns[c + 1][0]:
                        offset1 = abs(t.x0 - columns[c + 1][0])
                    if t.x1 > columns[c + 1][1]:
                        offset2 = abs(t.x1 - columns[c + 1][1])
                    error2 = (Y * (offset1 + offset2)) / charea
                    if error2 < error1:
                        return c + 1, error2
                except IndexError:
                    pass
            return c, error1


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
            pkey = 'pg-{0}'.format(p)
            text.sort(key=lambda x: (-x.y0, x.x0))

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
                cols = self.columns.split(',')
                cols = [(float(cols[i]), float(cols[i + 1]))
                        for i in range(0, len(cols) - 1)]
            else:
                if self.ncolumns:
                    ncols = self.ncolumns
                else:
                    guess = True
                    ncols = max(set(elements), key=elements.count)
                    len_nomode = len(filter(lambda x: x != ncols, elements))
                    if ncols == 1 and not self.debug:
                        # no tables detected
                        raise UserWarning("Only one column was detected, the PDF"
                                          " may have no tables. Specify ncols if"
                                          " the PDF has tables.")
                cols = [(t.x0, t.x1)
                        for r in rows_grouped if len(r) == ncols for t in r]
                cols = _merge_columns(sorted(cols), mtol=self.mtol)
                if len(cols) != ncols:
                    raise ValueError("The number of columns after merge"
                                     " isn't the same as what you specified."
                                     " Change the value of mtol.")
                cols = [(cols[i][0] + cols[i - 1][1]) / 2 for i in range(1, len(cols))]
                cols.insert(0, 0)
                cols.append(width) # or some tolerance
                cols = [(cols[i], cols[i + 1])
                        for i in range(0, len(cols) - 1)]

            table = Table(cols, rows)
            rerror = []
            cerror = []
            for t in text:
                try:
                    r_idx, rass_error = get_row_index(t, rows)
                except TypeError:
                    # couldn't assign LTTextLH to any cell
                    continue
                try:
                    c_idx, cass_error = _get_column_index(t, cols, ctol=self.ctol)
                except TypeError:
                    # couldn't assign LTTextLH to any cell
                    continue
                rerror.append(rass_error)
                cerror.append(cass_error)
                table.cells[r_idx][c_idx].add_text(
                    t.get_text().strip('\n'))
            ar = table.get_list()
            if guess:
                score = get_score({tuple(rerror): 33, tuple(cerror): 33, tuple([len_nomode / len(elements)]): 34})
            else:
                score = get_score({tuple(rerror): 50, tuple(cerror): 50})
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
