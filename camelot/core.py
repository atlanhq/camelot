import json

import numpy as np


class Cell(object):
    """

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
        return '<Cell x1={} y1={} x2={} y2={}'.format(
            self.x1, self.y1, self.x2, self.y2)

    @property
    def text(self):
        """

        Returns
        -------

        """
        return self._text

    @text.setter
    def text(self, t):
        """

        Parameters
        ----------
        t
        """
        self._text = ''.join([self._text, t])

    @property
    def bound(self):
        """

        Returns
        -------

        """
        return self.top + self.bottom + self.left + self.right


class Table(object):
    """

    """
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.cells = [[Cell(c[0], r[1], c[1], r[0])
                       for c in cols] for r in rows]
        self._df = None
        self._shape = (0, 0)
        self._accuracy = 0
        self._whitespace = 0
        self._order = None
        self._page = None

    def __repr__(self):
        return '<{} shape={}>'.format(self.__class__.__name__, self._shape)

    def set_border(self):
        """

        Returns
        -------

        """
        for r in range(len(self.rows)):
            self.cells[r][0].left = True
            self.cells[r][len(self.cols) - 1].right = True
        for c in range(len(self.cols)):
            self.cells[0][c].top = True
            self.cells[len(self.rows) - 1][c].bottom = True
        return self

    def set_all_edges(self):
        """

        Returns
        -------

        """
        for row in self.cells:
            for cell in row:
                cell.left = cell.right = cell.top = cell.bottom = True
        return self

    def set_edges(self, vertical, horizontal, jtol=2):
        """

        Parameters
        ----------
        vertical
        horizontal
        jtol

        Returns
        -------

        """
        for v in vertical:
            # find closest x coord
            # iterate over y coords and find closest start and end points
            i = [i for i, t in enumerate(self.cols)
                 if np.isclose(v[0], t[0], atol=jtol)]
            j = [j for j, t in enumerate(self.rows)
                 if np.isclose(v[3], t[0], atol=jtol)]
            k = [k for k, t in enumerate(self.rows)
                 if np.isclose(v[1], t[0], atol=jtol)]
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
                 if np.isclose(h[1], t[0], atol=jtol)]
            j = [j for j, t in enumerate(self.cols)
                 if np.isclose(h[0], t[0], atol=jtol)]
            k = [k for k, t in enumerate(self.cols)
                 if np.isclose(h[2], t[0], atol=jtol)]
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

    def set_span(self):
        """

        Returns
        -------

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
        return self

    @property
    def data(self):
        """

        Returns
        -------

        """
        d = []
        for row in self.cells:
            d.append([cell.text.strip() for cell in row])
        return d

    @property
    def df(self):
        """

        Returns
        -------

        """
        return self._df

    @df.setter
    def df(self, dataframe):
        self._df = dataframe

    @property
    def shape(self):
        """

        Returns
        -------

        """
        return self._shape

    @shape.setter
    def shape(self, s):
        self._shape = s

    @property
    def accuracy(self):
        """

        Returns
        -------

        """
        return self._accuracy

    @accuracy.setter
    def accuracy(self, a):
        self._accuracy = a

    @property
    def whitespace(self):
        """

        Returns
        -------

        """
        return self._whitespace

    @whitespace.setter
    def whitespace(self, w):
        self._whitespace = w

    @property
    def order(self):
        """

        Returns
        -------

        """
        return self._order

    @order.setter
    def order(self, o):
        self._order = o

    @property
    def page(self):
        """

        Returns
        -------

        """
        return self._page

    @page.setter
    def page(self, p):
        self._page = p

    @property
    def parsing_report(self):
        """

        Returns
        -------

        """
        # pretty?
        report = {
            'accuracy': self._accuracy,
            'whitespace': self._whitespace,
            'order': self._order,
            'page': self._page
        }
        return report


class TableList(object):
    """

    """
    def __init__(self, tables):
        self._tables = tables

    def __repr__(self):
        return '<{} tables={}>'.format(
            self.__class__.__name__, len(self._tables))

    def __len__(self):
        return len(self._tables)

    def __getitem__(self, idx):
        return self._tables[idx]


class Geometry(object):
    """

    """
    def __init__(self):
        self._text = []
        self._images = ()
        self._segments = ()
        self._tables = []

    @property
    def text(self):
        """

        Returns
        -------

        """
        return self._text

    @text.setter
    def text(self, t):
        self._text = t

    @property
    def images(self):
        """

        Returns
        -------

        """
        return self._images

    @images.setter
    def images(self, i):
        self._images = i

    @property
    def segments(self):
        """

        Returns
        -------

        """
        return self._segments

    @segments.setter
    def segments(self, s):
        self._segments = s

    @property
    def tables(self):
        """

        Returns
        -------

        """
        return self._tables

    @tables.setter
    def tables(self, tb):
        self._tables = tb


class GeometryList(object):
    """

    """
    def __init__(self, geometry):
        self._text = [g.text for g in geometry]
        self._images = [g.images for g in geometry]
        self._segments = [g.segments for g in geometry]
        self._tables = [g.tables for g in geometry]

    def __repr__(self):
        return '<{} text={} images={} segments={} tables={}>'.format(
            self.__class__.__name__,
            len(self._text),
            len(self._images),
            len(self._segments),
            len(self._tables))

    @property
    def text(self):
        """

        Returns
        -------

        """
        return self._text

    @property
    def images(self):
        """

        Returns
        -------

        """
        return self._images

    @property
    def segments(self):
        """

        Returns
        -------

        """
        return self._segments

    @property
    def tables(self):
        """

        Returns
        -------

        """
        return self._tables