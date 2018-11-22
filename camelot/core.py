# -*- coding: utf-8 -*-

import os
import zipfile
import tempfile
from itertools import chain
from operator import itemgetter

import numpy as np
import pandas as pd


# minimum number of textlines to be considered a textedge
TEXTEDGE_REQUIRED_ELEMENTS = 4
# y coordinate tolerance for extending text edge
TEXTEDGE_EXTEND_TOLERANCE = 50
# padding added to table area's lt and rb
TABLE_AREA_PADDING = 10


class TextEdge(object):
    def __init__(self, x, y0, y1, align='left'):
        self.x = x
        self.y0 = y0
        self.y1 = y1
        self.align = align
        self.intersections = 0
        self.is_valid = False

    def __repr__(self):
        return '<TextEdge x={} y0={} y1={} align={} valid={}>'.format(
            round(self.x, 2), round(self.y0, 2), round(self.y1, 2), self.align, self.is_valid)

    def update_coords(self, x, y0):
        if np.isclose(self.y0, y0, atol=TEXTEDGE_EXTEND_TOLERANCE):
            self.x = (self.intersections * self.x + x) / float(self.intersections + 1)
            self.y0 = y0
            self.intersections += 1
            # a textedge is valid if it extends uninterrupted over required_elements
            if self.intersections > TEXTEDGE_REQUIRED_ELEMENTS:
                self.is_valid = True


class TextEdges(object):
    def __init__(self):
        self._textedges = {'left': [], 'middle': [], 'right': []}

    @staticmethod
    def get_x_coord(textline, align):
        x_left = textline.x0
        x_right = textline.x1
        x_middle = x_left + (x_right - x_left) / 2.0
        x_coord = {'left': x_left, 'middle': x_middle, 'right': x_right}
        return x_coord[align]

    def find(self, x_coord, align):
        for i, te in enumerate(self._textedges[align]):
            if np.isclose(te.x, x_coord):
                return i
        return None

    def add(self, textline, align):
        x = self.get_x_coord(textline, align)
        y0 = textline.y0
        y1 = textline.y1
        te = TextEdge(x, y0, y1, align=align)
        self._textedges[align].append(te)

    def update(self, textline):
        for align in ['left', 'right', 'middle']:
            x_coord = self.get_x_coord(textline, align)
            idx = self.find(x_coord, align)
            if idx is None:
                self.add(textline, align)
            else:
                self._textedges[align][idx].update_coords(x_coord, textline.y0)

    def generate(self, textlines):
        textlines_flat = list(chain.from_iterable(textlines))
        for tl in textlines_flat:
            if len(tl.get_text().strip()) > 1: # TODO: hacky
                self.update(tl)

    def get_relevant(self):
        intersections_sum = {
            'left': sum(te.intersections for te in self._textedges['left'] if te.is_valid),
            'right': sum(te.intersections for te in self._textedges['right'] if te.is_valid),
            'middle': sum(te.intersections for te in self._textedges['middle'] if te.is_valid)
        }

        # TODO: naive
        # get the vertical textedges that intersect maximum number of
        # times with horizontal text rows
        relevant_align = max(intersections_sum.items(), key=itemgetter(1))[0]
        return self._textedges[relevant_align]

    def get_table_areas(self, textlines, relevant_textedges):
        def pad(area):
            x0 = area[0] - TABLE_AREA_PADDING
            y0 = area[1] - TABLE_AREA_PADDING
            x1 = area[2] + TABLE_AREA_PADDING
            # TODO: deal in percentages instead of absolutes
            # add a constant to include table headers
            y1 = area[3] + TABLE_AREA_PADDING + 10
            return (x0, y0, x1, y1)

        # sort relevant textedges in reading order
        relevant_textedges.sort(key=lambda te: (-te.y0, te.x))

        table_areas = {}
        for te in relevant_textedges:
            if te.is_valid:
                if not table_areas:
                    table_areas[(te.x, te.y0, te.x, te.y1)] = None
                else:
                    found = None
                    for area in table_areas:
                        # check for overlap
                        if te.y1 >= area[1] and te.y0 <= area[3]:
                            found = area
                            break
                    if found is None:
                        table_areas[(te.x, te.y0, te.x, te.y1)] = None
                    else:
                        table_areas.pop(found)
                        updated_area = (
                            found[0], min(te.y0, found[1]), max(found[2], te.x), max(found[3], te.y1))
                        table_areas[updated_area] = None

        # extend table areas based on textlines that overlap
        # vertically. it's possible that these textlines were
        # eliminated during textedges generation since numbers and
        # sentences/chars are often aligned differently.
        # drawback: table areas that have paragraphs to their sides
        # will include the paragraphs too.
        for tl in textlines:
            for area in table_areas:
                found = None
                # check for overlap
                if tl.y0 >= area[1] and tl.y1 <= area[3]:
                    found = area
                    break
            if found is not None:
                table_areas.pop(found)
                updated_area = (
                    min(tl.x0, found[0]), min(tl.y0, found[1]), max(found[2], tl.x1), max(found[3], tl.y1))
                table_areas[updated_area] = None

        # add some padding to table areas
        table_areas_padded = {}
        for area in table_areas:
            table_areas_padded[pad(area)] = None

        # debug
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal')
        xs, ys = [], []
        for t in textlines:
            xs.extend([t.x0, t.x1])
            ys.extend([t.y0, t.y1])
            ax.add_patch(
                patches.Rectangle(
                    (t.x0, t.y0),
                    t.x1 - t.x0,
                    t.y1 - t.y0,
                    color='blue'
                )
            )
        for area in table_areas_padded:
            xs.extend([area[0], area[2]])
            ys.extend([area[1], area[3]])
            ax.add_patch(
                patches.Rectangle(
                    (area[0], area[1]),
                    area[2] - area[0],
                    area[3] - area[1],
                    fill=False,
                    color='red'
                )
            )

        ax.set_xlim(min(xs) - 10, max(xs) + 10)
        ax.set_ylim(min(ys) - 10, max(ys) + 10)
        plt.show()

        return table_areas_padded


class Cell(object):
    """Defines a cell in a table with coordinates relative to a
    left-bottom origin. (PDF coordinate space)

    Parameters
    ----------
    x1 : float
        x-coordinate of left-bottom point.
    y1 : float
        y-coordinate of left-bottom point.
    x2 : float
        x-coordinate of right-top point.
    y2 : float
        y-coordinate of right-top point.

    Attributes
    ----------
    lb : tuple
        Tuple representing left-bottom coordinates.
    lt : tuple
        Tuple representing left-top coordinates.
    rb : tuple
        Tuple representing right-bottom coordinates.
    rt : tuple
        Tuple representing right-top coordinates.
    left : bool
        Whether or not cell is bounded on the left.
    right : bool
        Whether or not cell is bounded on the right.
    top : bool
        Whether or not cell is bounded on the top.
    bottom : bool
        Whether or not cell is bounded on the bottom.
    hspan : bool
        Whether or not cell spans horizontally.
    vspan : bool
        Whether or not cell spans vertically.
    text : string
        Text assigned to cell.

    """

    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.lb = (x1, y1)
        self.lt = (x1, y2)
        self.rb = (x2, y1)
        self.rt = (x2, y2)
        self.left = False
        self.right = False
        self.top = False
        self.bottom = False
        self.hspan = False
        self.vspan = False
        self._text = ''

    def __repr__(self):
        return '<Cell x1={} y1={} x2={} y2={}>'.format(
            round(self.x1, 2), round(self.y1, 2), round(self.x2, 2), round(self.y2, 2))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, t):
        self._text = ''.join([self._text, t])

    @property
    def bound(self):
        """The number of sides on which the cell is bounded.
        """
        return self.top + self.bottom + self.left + self.right


class Table(object):
    """Defines a table with coordinates relative to a left-bottom
    origin. (PDF coordinate space)

    Parameters
    ----------
    cols : list
        List of tuples representing column x-coordinates in increasing
        order.
    rows : list
        List of tuples representing row y-coordinates in decreasing
        order.

    Attributes
    ----------
    df : :class:`pandas.DataFrame`
    shape : tuple
        Shape of the table.
    accuracy : float
        Accuracy with which text was assigned to the cell.
    whitespace : float
        Percentage of whitespace in the table.
    order : int
        Table number on PDF page.
    page : int
        PDF page number.

    """
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.cells = [[Cell(c[0], r[1], c[1], r[0])
                       for c in cols] for r in rows]
        self.df = None
        self.shape = (0, 0)
        self.accuracy = 0
        self.whitespace = 0
        self.order = None
        self.page = None

    def __repr__(self):
        return '<{} shape={}>'.format(self.__class__.__name__, self.shape)

    @property
    def data(self):
        """Returns two-dimensional list of strings in table.
        """
        d = []
        for row in self.cells:
            d.append([cell.text.strip() for cell in row])
        return d

    @property
    def parsing_report(self):
        """Returns a parsing report with %accuracy, %whitespace,
        table number on page and page number.
        """
        # pretty?
        report = {
            'accuracy': round(self.accuracy, 2),
            'whitespace': round(self.whitespace, 2),
            'order': self.order,
            'page': self.page
        }
        return report

    def set_all_edges(self):
        """Sets all table edges to True.
        """
        for row in self.cells:
            for cell in row:
                cell.left = cell.right = cell.top = cell.bottom = True
        return self

    def set_edges(self, vertical, horizontal, joint_close_tol=2):
        """Sets a cell's edges to True depending on whether the cell's
        coordinates overlap with the line's coordinates within a
        tolerance.

        Parameters
        ----------
        vertical : list
            List of detected vertical lines.
        horizontal : list
            List of detected horizontal lines.

        """
        for v in vertical:
            # find closest x coord
            # iterate over y coords and find closest start and end points
            i = [i for i, t in enumerate(self.cols)
                 if np.isclose(v[0], t[0], atol=joint_close_tol)]
            j = [j for j, t in enumerate(self.rows)
                 if np.isclose(v[3], t[0], atol=joint_close_tol)]
            k = [k for k, t in enumerate(self.rows)
                 if np.isclose(v[1], t[0], atol=joint_close_tol)]
            if not j:
                continue
            J = j[0]
            if i == [0]:  # only left edge
                L = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[J][L].left = True
                        J += 1
                else:
                    K = len(self.rows)
                    while J < K:
                        self.cells[J][L].left = True
                        J += 1
            elif i == []:  # only right edge
                L = len(self.cols) - 1
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[J][L].right = True
                        J += 1
                else:
                    K = len(self.rows)
                    while J < K:
                        self.cells[J][L].right = True
                        J += 1
            else:  # both left and right edges
                L = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[J][L].left = True
                        self.cells[J][L - 1].right = True
                        J += 1
                else:
                    K = len(self.rows)
                    while J < K:
                        self.cells[J][L].left = True
                        self.cells[J][L - 1].right = True
                        J += 1

        for h in horizontal:
            # find closest y coord
            # iterate over x coords and find closest start and end points
            i = [i for i, t in enumerate(self.rows)
                 if np.isclose(h[1], t[0], atol=joint_close_tol)]
            j = [j for j, t in enumerate(self.cols)
                 if np.isclose(h[0], t[0], atol=joint_close_tol)]
            k = [k for k, t in enumerate(self.cols)
                 if np.isclose(h[2], t[0], atol=joint_close_tol)]
            if not j:
                continue
            J = j[0]
            if i == [0]:  # only top edge
                L = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[L][J].top = True
                        J += 1
                else:
                    K = len(self.cols)
                    while J < K:
                        self.cells[L][J].top = True
                        J += 1
            elif i == []:  # only bottom edge
                I = len(self.rows) - 1
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[L][J].bottom = True
                        J += 1
                else:
                    K = len(self.cols)
                    while J < K:
                        self.cells[L][J].bottom = True
                        J += 1
            else:  # both top and bottom edges
                L = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[L][J].top = True
                        self.cells[L - 1][J].bottom = True
                        J += 1
                else:
                    K = len(self.cols)
                    while J < K:
                        self.cells[L][J].top = True
                        self.cells[L - 1][J].bottom = True
                        J += 1

        return self

    def set_border(self):
        """Sets table border edges to True.
        """
        for r in range(len(self.rows)):
            self.cells[r][0].left = True
            self.cells[r][len(self.cols) - 1].right = True
        for c in range(len(self.cols)):
            self.cells[0][c].top = True
            self.cells[len(self.rows) - 1][c].bottom = True
        return self

    def set_span(self):
        """Sets a cell's hspan or vspan attribute to True depending
        on whether the cell spans horizontally or vertically.
        """
        for row in self.cells:
            for cell in row:
                left = cell.left
                right = cell.right
                top = cell.top
                bottom = cell.bottom
                if cell.bound == 4:
                    continue
                elif cell.bound == 3:
                    if not left and (right and top and bottom):
                        cell.hspan = True
                    elif not right and (left and top and bottom):
                        cell.hspan = True
                    elif not top and (left and right and bottom):
                        cell.vspan = True
                    elif not bottom and (left and right and top):
                        cell.vspan = True
                elif cell.bound == 2:
                    if left and right and (not top and not bottom):
                        cell.vspan = True
                    elif top and bottom and (not left and not right):
                        cell.hspan = True
                elif cell.bound in [0, 1]:
                    cell.vspan = True
                    cell.hspan = True
        return self

    def to_csv(self, path, **kwargs):
        """Writes Table to a comma-separated values (csv) file.

        For kwargs, check :meth:`pandas.DataFrame.to_csv`.

        Parameters
        ----------
        path : str
            Output filepath.

        """
        kw = {
            'encoding': 'utf-8',
            'index': False,
            'header': False,
            'quoting': 1
        }
        kw.update(kwargs)
        self.df.to_csv(path, **kw)

    def to_json(self, path, **kwargs):
        """Writes Table to a JSON file.

        For kwargs, check :meth:`pandas.DataFrame.to_json`.

        Parameters
        ----------
        path : str
            Output filepath.

        """
        kw = {
            'orient': 'records'
        }
        kw.update(kwargs)
        json_string = self.df.to_json(**kw)
        with open(path, 'w') as f:
            f.write(json_string)

    def to_excel(self, path, **kwargs):
        """Writes Table to an Excel file.

        For kwargs, check :meth:`pandas.DataFrame.to_excel`.

        Parameters
        ----------
        path : str
            Output filepath.

        """
        kw = {
            'sheet_name': 'page-{}-table-{}'.format(self.page, self.order),
            'encoding': 'utf-8'
        }
        kw.update(kwargs)
        writer = pd.ExcelWriter(path)
        self.df.to_excel(writer, **kw)
        writer.save()

    def to_html(self, path, **kwargs):
        """Writes Table to an HTML file.

        For kwargs, check :meth:`pandas.DataFrame.to_html`.

        Parameters
        ----------
        path : str
            Output filepath.

        """
        html_string = self.df.to_html(**kwargs)
        with open(path, 'w') as f:
            f.write(html_string)


class TableList(object):
    """Defines a list of camelot.core.Table objects. Each table can
    be accessed using its index.

    Attributes
    ----------
    n : int
        Number of tables in the list.

    """
    def __init__(self, tables):
        self._tables = tables

    def __repr__(self):
        return '<{} n={}>'.format(
            self.__class__.__name__, self.n)

    def __len__(self):
        return len(self._tables)

    def __getitem__(self, idx):
        return self._tables[idx]

    @staticmethod
    def _format_func(table, f):
        return getattr(table, 'to_{}'.format(f))

    @property
    def n(self):
        return len(self)

    def _write_file(self, f=None, **kwargs):
        dirname = kwargs.get('dirname')
        root = kwargs.get('root')
        ext = kwargs.get('ext')
        for table in self._tables:
            filename = os.path.join('{}-page-{}-table-{}{}'.format(
                                    root, table.page, table.order, ext))
            filepath = os.path.join(dirname, filename)
            to_format = self._format_func(table, f)
            to_format(filepath)

    def _compress_dir(self, **kwargs):
        path = kwargs.get('path')
        dirname = kwargs.get('dirname')
        root = kwargs.get('root')
        ext = kwargs.get('ext')
        zipname = os.path.join(os.path.dirname(path), root) + '.zip'
        with zipfile.ZipFile(zipname, 'w', allowZip64=True) as z:
            for table in self._tables:
                filename = os.path.join('{}-page-{}-table-{}{}'.format(
                                        root, table.page, table.order, ext))
                filepath = os.path.join(dirname, filename)
                z.write(filepath, os.path.basename(filepath))

    def export(self, path, f='csv', compress=False):
        """Exports the list of tables to specified file format.

        Parameters
        ----------
        path : str
            Output filepath.
        f : str
            File format. Can be csv, json, excel and html.
        compress : bool
            Whether or not to add files to a ZIP archive.

        """
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        root, ext = os.path.splitext(basename)
        if compress:
            dirname = tempfile.mkdtemp()

        kwargs = {
            'path': path,
            'dirname': dirname,
            'root': root,
            'ext': ext
        }

        if f in ['csv', 'json', 'html']:
            self._write_file(f=f, **kwargs)
            if compress:
                self._compress_dir(**kwargs)
        elif f == 'excel':
            filepath = os.path.join(dirname, basename)
            writer = pd.ExcelWriter(filepath)
            for table in self._tables:
                sheet_name = 'page-{}-table-{}'.format(table.page, table.order)
                table.df.to_excel(writer, sheet_name=sheet_name, encoding='utf-8')
            writer.save()
            if compress:
                zipname = os.path.join(os.path.dirname(path), root) + '.zip'
                with zipfile.ZipFile(zipname, 'w', allowZip64=True) as z:
                    z.write(filepath, os.path.basename(filepath))
