from __future__ import print_function
import os

import numpy as np

from .utils import get_column_index, encode_list


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
                row_y = t.y0
                rows.append(temp)
                temp = []
            temp.append(t)
    return rows


def _merge_columns(l):
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
            if higher[0] <= lower[1]:
                upper_bound = max(lower[1], higher[1])
                lower_bound = min(lower[0], higher[0])
                merged[-1] = (lower_bound, upper_bound)
            else:
                merged.append(higher)
    return merged


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

    def __init__(self, pdfobject, ncolumns=0, columns=None, ytol=2,
                 debug=False, verbose=False):

        self.pdfobject = pdfobject
        self.ncolumns = ncolumns
        self.columns = columns
        self.ytol = ytol
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
            p, __, text, __, __ = page
            pkey = 'pg-{0}'.format(p)
            text.sort(key=lambda x: (-x.y0, x.x0))

            if self.debug:
                self.debug_text[pkey] = text

            rows = _group_rows(text, ytol=self.ytol)
            elements = [len(r) for r in rows]
            # a table can't have just 1 column, can it?
            elements = filter(lambda x: x != 1, elements)

            guess = False
            if self.columns:
                cols = self.columns.split(',')
                cols = [(float(cols[i]), float(cols[i + 1]))
                        for i in range(0, len(cols) - 1)]
            else:
                guess = True
                ncols = self.ncolumns if self.ncolumns else max(
                    set(elements), key=elements.count)
                if ncols == 0:
                    # no tables detected
                    continue
                cols = [(t.x0, t.x1)
                        for r in rows for t in r if len(r) == ncols]
                cols = _merge_columns(sorted(cols))
                cols = [(c[0] + c[1]) / 2.0 for c in cols]

            ar = [['' for c in cols] for r in rows]
            for r_idx, r in enumerate(rows):
                for t in r:
                    if guess:
                        cog = (t.x0 + t.x1) / 2.0
                        diff = [abs(cog - c) for c in cols]
                        c_idx = diff.index(min(diff))
                    else:
                        c_idx = get_column_index(t, cols)
                    if None in [r_idx, c_idx]:  # couldn't assign LTTextLH to any cell
                        continue
                    if ar[r_idx][c_idx]:
                        ar[r_idx][c_idx] = ' '.join(
                            [ar[r_idx][c_idx], t.get_text().strip()])
                    else:
                        ar[r_idx][c_idx] = t.get_text().strip()
            vprint(pkey)
            self.tables[pkey] = [encode_list(ar)]

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
