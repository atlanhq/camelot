import json

import numpy as np


class Cell(object):
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.lb = (x1, y1)
        self.lt = (x1, y2)
        self.rb = (x2, y1)
        self.rt = (x2, y2)
        self.bbox = (x1, y1, x2, y2)
        self.left = False
        self.right = False
        self.top = False
        self.bottom = False
        self.text_objects = []
        self.text = ''
        self.spanning_h = False
        self.spanning_v = False

    def __repr__(self):
        pass

    def add_text(self, text):
        self.text = ''.join([self.text, text])

    def get_text(self):
        return self.text

    def add_object(self, t_object):
        self.text_objects.append(t_object)

    def get_objects(self):
        return self.text_objects

    def get_bounded_edges(self):
        self.bounded_edges = self.top + self.bottom + self.left + self.right
        return self.bounded_edges


class Table(object):
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

    def set_all_edges(self):
        for r in range(len(self.rows)):
            for c in range(len(self.cols)):
                self.cells[r][c].left = True
                self.cells[r][c].right = True
                self.cells[r][c].top = True
                self.cells[r][c].bottom = True
        return self

    def set_border_edges(self):
        for r in range(len(self.rows)):
            self.cells[r][0].left = True
            self.cells[r][len(self.cols) - 1].right = True
        for c in range(len(self.cols)):
            self.cells[0][c].top = True
            self.cells[len(self.rows) - 1][c].bottom = True
        return self

    def set_edges(self, vertical, horizontal, jtol=2):
        for v in vertical:
            # find closest x coord
            # iterate over y coords and find closest points
            i = [i for i, t in enumerate(self.cols)
                 if np.isclose(v[0], t[0], atol=jtol)]
            j = [j for j, t in enumerate(self.rows)
                 if np.isclose(v[3], t[0], atol=jtol)]
            k = [k for k, t in enumerate(self.rows)
                 if np.isclose(v[1], t[0], atol=jtol)]
            if not j:
                self.nocont_ += 1
                continue
            J = j[0]
            if i == [0]:  # only left edge
                I = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[J][I].left = True
                        J += 1
                else:
                    K = len(self.rows)
                    while J < K:
                        self.cells[J][I].left = True
                        J += 1
            elif i == []:  # only right edge
                I = len(self.cols) - 1
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[J][I].right = True
                        J += 1
                else:
                    K = len(self.rows)
                    while J < K:
                        self.cells[J][I].right = True
                        J += 1
            else:  # both left and right edges
                I = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[J][I].left = True
                        self.cells[J][I - 1].right = True
                        J += 1
                else:
                    K = len(self.rows)
                    while J < K:
                        self.cells[J][I].left = True
                        self.cells[J][I - 1].right = True
                        J += 1

        for h in horizontal:
            # find closest y coord
            # iterate over x coords and find closest points
            i = [i for i, t in enumerate(self.rows)
                 if np.isclose(h[1], t[0], atol=jtol)]
            j = [j for j, t in enumerate(self.cols)
                 if np.isclose(h[0], t[0], atol=jtol)]
            k = [k for k, t in enumerate(self.cols)
                 if np.isclose(h[2], t[0], atol=jtol)]
            if not j:
                self.nocont_ += 1
                continue
            J = j[0]
            if i == [0]:  # only top edge
                I = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[I][J].top = True
                        J += 1
                else:
                    K = len(self.cols)
                    while J < K:
                        self.cells[I][J].top = True
                        J += 1
            elif i == []:  # only bottom edge
                I = len(self.rows) - 1
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[I][J].bottom = True
                        J += 1
                else:
                    K = len(self.cols)
                    while J < K:
                        self.cells[I][J].bottom = True
                        J += 1
            else:  # both top and bottom edges
                I = i[0]
                if k:
                    K = k[0]
                    while J < K:
                        self.cells[I][J].top = True
                        self.cells[I - 1][J].bottom = True
                        J += 1
                else:
                    K = len(self.cols)
                    while J < K:
                        self.cells[I][J].top = True
                        self.cells[I - 1][J].bottom = True
                        J += 1

        return self

    def set_spanning(self):
        for r in range(len(self.rows)):
            for c in range(len(self.cols)):
                bound = self.cells[r][c].get_bounded_edges()
                if bound == 4:
                    continue
                elif bound == 3:
                    if not self.cells[r][c].left:
                        if (self.cells[r][c].right and
                                self.cells[r][c].top and
                                self.cells[r][c].bottom):
                            self.cells[r][c].spanning_h = True
                    elif not self.cells[r][c].right:
                        if (self.cells[r][c].left and
                                self.cells[r][c].top and
                                self.cells[r][c].bottom):
                            self.cells[r][c].spanning_h = True
                    elif not self.cells[r][c].top:
                        if (self.cells[r][c].left and
                                self.cells[r][c].right and
                                self.cells[r][c].bottom):
                            self.cells[r][c].spanning_v = True
                    elif not self.cells[r][c].bottom:
                        if (self.cells[r][c].left and
                                self.cells[r][c].right and
                                self.cells[r][c].top):
                            self.cells[r][c].spanning_v = True
                elif bound == 2:
                    if self.cells[r][c].left and self.cells[r][c].right:
                        if (not self.cells[r][c].top and
                                not self.cells[r][c].bottom):
                            self.cells[r][c].spanning_v = True
                    elif self.cells[r][c].top and self.cells[r][c].bottom:
                        if (not self.cells[r][c].left and
                                not self.cells[r][c].right):
                            self.cells[r][c].spanning_h = True

        return self

    @property
    def data(self):
        d = []
        for r in range(len(self.rows)):
            d.append([self.cells[r][c].get_text().strip()
                       for c in range(len(self.cols))])
        return d

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, dataframe):
        self._df = dataframe

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, s):
        self._shape = s

    @property
    def accuracy(self):
        return self._accuracy

    @accuracy.setter
    def accuracy(self, a):
        self._accuracy = a

    @property
    def whitespace(self):
        return self._whitespace

    @whitespace.setter
    def whitespace(self, w):
        self._whitespace = w

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, o):
        self._order = o

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, p):
        self._page = p

    @property
    def parsing_report(self):
        # pretty?
        report = {
            'accuracy': self._accuracy,
            'whitespace': self._whitespace,
            'order': self._order,
            'page': self._page
        }
        return report


class TableList(list):
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
    def __init__(self):
        self._text = []
        self._images = ()
        self._segments = ()
        self._tables = []

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, t):
        self._text = t

    @property
    def images(self):
        return self._images

    @images.setter
    def images(self, i):
        self._images = i

    @property
    def segments(self):
        return self._segments

    @segments.setter
    def segments(self, s):
        self._segments = s

    @property
    def tables(self):
        return self._tables

    @tables.setter
    def tables(self, tb):
        self._tables = tb


class GeometryList(object):
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
        return self._text

    @property
    def images(self):
        return self._images

    @property
    def segments(self):
        return self._segments

    @property
    def tables(self):
        return self._tables