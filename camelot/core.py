import numpy as np
import pandas as pd


class Cell(object):
    """Cell.
    Defines a cell object with coordinates relative to a left-bottom
    origin, which is also PDFMiner's coordinate space.

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

    bbox : tuple
        Tuple representing the cell's bounding box using the
        lower-bottom and right-top coordinates.

    left : bool
        Whether or not cell is bounded on the left.

    right : bool
        Whether or not cell is bounded on the right.

    top : bool
        Whether or not cell is bounded on the top.

    bottom : bool
        Whether or not cell is bounded on the bottom.

    text_objects : list
        List of text objects assigned to cell.

    text : string
        Text assigned to cell.

    spanning_h : bool
        Whether or not cell spans/extends horizontally.

    spanning_v : bool
        Whether or not cell spans/extends vertically.
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
        self.bbox = (x1, y1, x2, y2)
        self.left = False
        self.right = False
        self.top = False
        self.bottom = False
        self.text_objects = []
        self.text = ''
        self.spanning_h = False
        self.spanning_v = False
        self.image = None

    def add_text(self, text):
        """Adds text to cell.

        Parameters
        ----------
        text : string
        """
        self.text = ''.join([self.text, text])

    def get_text(self):
        """Returns text assigned to cell.

        Returns
        -------
        text : string
        """
        return self.text

    def add_object(self, t_object):
        """Adds PDFMiner text object to cell.

        Parameters
        ----------
        t_object : object
        """
        self.text_objects.append(t_object)

    def get_objects(self):
        """Returns list of text objects assigned to cell.

        Returns
        -------
        text_objects : list
        """
        return self.text_objects

    def get_bounded_edges(self):
        """Returns the number of edges by which a cell is bounded.

        Returns
        -------
        bounded_edges : int
        """
        self.bounded_edges = self.top + self.bottom + self.left + self.right
        return self.bounded_edges


class Table(object):
    """Table.
    Defines a table object with coordinates relative to a left-bottom
    origin, which is also PDFMiner's coordinate space.

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
    cells : list
        List of cell objects with row-major ordering.

    nocont_ : int
        Number of lines that did not contribute to setting cell edges.
    """

    def __init__(self, cols, rows):

        self.cols = cols
        self.rows = rows
        self.cells = [[Cell(c[0], r[1], c[1], r[0])
                       for c in cols] for r in rows]
        self.nocont_ = 0
        self.image = None

    def set_all_edges(self):
        """Sets all table edges to True.
        """
        for r in range(len(self.rows)):
            for c in range(len(self.cols)):
                self.cells[r][c].left = True
                self.cells[r][c].right = True
                self.cells[r][c].top = True
                self.cells[r][c].bottom = True
        return self

    def set_border_edges(self):
        """Sets table border edges to True.
        """
        for r in range(len(self.rows)):
            self.cells[r][0].left = True
            self.cells[r][len(self.cols) - 1].right = True
        for c in range(len(self.cols)):
            self.cells[0][c].top = True
            self.cells[len(self.rows) - 1][c].bottom = True
        return self

    def set_edges(self, vertical, horizontal, jtol=2):
        """Sets a cell's edges to True depending on whether they
        overlap with lines found by imgproc.

        Parameters
        ----------
        vertical : list
            List of vertical lines detected by imgproc. Coordinates
            scaled and translated to the PDFMiner's coordinate space.

        horizontal : list
            List of horizontal lines detected by imgproc. Coordinates
            scaled and translated to the PDFMiner's coordinate space.
        """
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
            #  find closest y coord
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
        """Sets a cell's spanning_h or spanning_v attribute to True
        depending on whether the cell spans/extends horizontally or
        vertically.
        """
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

    def get_list(self):
        """Returns a two-dimensional list of text assigned to each
        cell.

        Returns
        -------
        ar : list
        """
        ar = []
        for r in range(len(self.rows)):
            ar.append([self.cells[r][c].get_text().strip()
                       for c in range(len(self.cols))])
        return ar


class TableSet(object):
    pass