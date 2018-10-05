# -*- coding: utf-8 -*-

from __future__ import division
import os
import logging
import warnings

import numpy as np
import pandas as pd

from .base import BaseParser
from ..core import Table
from ..utils import (text_in_bbox, get_table_index, compute_accuracy,
                     compute_whitespace)


logger = logging.getLogger('camelot')


class Stream(BaseParser):
    """Stream method of parsing looks for spaces between text
    to parse the table.

    If you want to specify columns when specifying multiple table
    areas, make sure that the length of both lists are equal.

    Parameters
    ----------
    table_area : list, optional (default: None)
        List of table area strings of the form x1,y1,x2,y2
        where (x1, y1) -> left-top and (x2, y2) -> right-bottom
        in PDF coordinate space.
    columns : list, optional (default: None)
        List of column x-coordinates strings where the coordinates
        are comma-separated.
    split_text : bool, optional (default: False)
        Split text that spans across multiple cells.
    flag_size : bool, optional (default: False)
        Flag text based on font size. Useful to detect
        super/subscripts. Adds <s></s> around flagged text.
    row_close_tol : int, optional (default: 2)
        Tolerance parameter used to combine text vertically,
        to generate rows.
    col_close_tol : int, optional (default: 0)
        Tolerance parameter used to combine text horizontally,
        to generate columns.
    margins : tuple, optional (default: (1.0, 0.5, 0.1))
        PDFMiner char_margin, line_margin and word_margin.

        For more information, refer `PDFMiner docs <https://euske.github.io/pdfminer/>`_.

    """
    def __init__(self, table_area=None, columns=None, split_text=False,
                 flag_size=False, row_close_tol=2, col_close_tol=0,
                 margins=(1.0, 0.5, 0.1), **kwargs):
        self.table_area = table_area
        self.columns = columns
        self._validate_columns()
        self.split_text = split_text
        self.flag_size = flag_size
        self.row_close_tol = row_close_tol
        self.col_close_tol = col_close_tol
        self.char_margin, self.line_margin, self.word_margin = margins

    @staticmethod
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
            Tuple (x0, y0, x1, y1) in pdf coordinate space.

        """
        xmin = min([t.x0 for direction in t_bbox for t in t_bbox[direction]])
        ymin = min([t.y0 for direction in t_bbox for t in t_bbox[direction]])
        xmax = max([t.x1 for direction in t_bbox for t in t_bbox[direction]])
        ymax = max([t.y1 for direction in t_bbox for t in t_bbox[direction]])
        text_bbox = (xmin, ymin, xmax, ymax)
        return text_bbox

    @staticmethod
    def _group_rows(text, row_close_tol=2):
        """Groups PDFMiner text objects into rows vertically
        within a tolerance.

        Parameters
        ----------
        text : list
            List of PDFMiner text objects.
        row_close_tol : int, optional (default: 2)

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
                if not np.isclose(row_y, t.y0, atol=row_close_tol):
                    rows.append(sorted(temp, key=lambda t: t.x0))
                    temp = []
                    row_y = t.y0
                temp.append(t)
        rows.append(sorted(temp, key=lambda t: t.x0))
        __ = rows.pop(0)  # hacky
        return rows

    @staticmethod
    def _merge_columns(l, col_close_tol=0):
        """Merges column boundaries horizontally if they overlap
        or lie within a tolerance.

        Parameters
        ----------
        l : list
            List of column x-coordinate tuples.
        col_close_tol : int, optional (default: 0)

        Returns
        -------
        merged : list
            List of merged column x-coordinate tuples.

        """
        merged = []
        for higher in l:
            if not merged:
                merged.append(higher)
            else:
                lower = merged[-1]
                if col_close_tol >= 0:
                    if (higher[0] <= lower[1] or
                            np.isclose(higher[0], lower[1], atol=col_close_tol)):
                        upper_bound = max(lower[1], higher[1])
                        lower_bound = min(lower[0], higher[0])
                        merged[-1] = (lower_bound, upper_bound)
                    else:
                        merged.append(higher)
                elif col_close_tol < 0:
                    if higher[0] <= lower[1]:
                        if np.isclose(higher[0], lower[1], atol=abs(col_close_tol)):
                            merged.append(higher)
                        else:
                            upper_bound = max(lower[1], higher[1])
                            lower_bound = min(lower[0], higher[0])
                            merged[-1] = (lower_bound, upper_bound)
                    else:
                        merged.append(higher)
        return merged

    @staticmethod
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
            List of continuous row y-coordinate tuples.

        """
        row_mids = [sum([(t.y0 + t.y1) / 2 for t in r]) / len(r)
                    if len(r) > 0 else 0 for r in rows_grouped]
        rows = [(row_mids[i] + row_mids[i - 1]) / 2 for i in range(1, len(row_mids))]
        rows.insert(0, text_y_max)
        rows.append(text_y_min)
        rows = [(rows[i], rows[i + 1])
                for i in range(0, len(rows) - 1)]
        return rows

    @staticmethod
    def _add_columns(cols, text, row_close_tol):
        """Adds columns to existing list by taking into account
        the text that lies outside the current column x-coordinates.

        Parameters
        ----------
        cols : list
            List of column x-coordinate tuples.
        text : list
            List of PDFMiner text objects.
        ytol : int

        Returns
        -------
        cols : list
            Updated list of column x-coordinate tuples.

        """
        if text:
            text = Stream._group_rows(text, row_close_tol=row_close_tol)
            elements = [len(r) for r in text]
            new_cols = [(t.x0, t.x1)
                        for r in text if len(r) == max(elements) for t in r]
            cols.extend(Stream._merge_columns(sorted(new_cols)))
        return cols

    @staticmethod
    def _join_columns(cols, text_x_min, text_x_max):
        """Makes column coordinates continuous.

        Parameters
        ----------
        cols : list
            List of column x-coordinate tuples.
        text_x_min : int
        text_y_max : int

        Returns
        -------
        cols : list
            Updated list of column x-coordinate tuples.

        """
        cols = sorted(cols)
        cols = [(cols[i][0] + cols[i - 1][1]) / 2 for i in range(1, len(cols))]
        cols.insert(0, text_x_min)
        cols.append(text_x_max)
        cols = [(cols[i], cols[i + 1])
                for i in range(0, len(cols) - 1)]
        return cols

    def _validate_columns(self):
        if self.table_area is not None and self.columns is not None:
            if len(self.table_area) != len(self.columns):
                raise ValueError("Length of table_area and columns"
                                 " should be equal")

    def _generate_table_bbox(self):
        if self.table_area is not None:
            table_bbox = {}
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = float(x1)
                y1 = float(y1)
                x2 = float(x2)
                y2 = float(y2)
                table_bbox[(x1, y2, x2, y1)] = None
        else:
            table_bbox = {(0, 0, self.pdf_width, self.pdf_height): None}
        self.table_bbox = table_bbox

    def _generate_columns_and_rows(self, table_idx, tk):
        # select elements which lie within table_bbox
        t_bbox = {}
        t_bbox['horizontal'] = text_in_bbox(tk, self.horizontal_text)
        t_bbox['vertical'] = text_in_bbox(tk, self.vertical_text)
        self.t_bbox = t_bbox

        for direction in self.t_bbox:
            self.t_bbox[direction].sort(key=lambda x: (-x.y0, x.x0))

        text_x_min, text_y_min, text_x_max, text_y_max = self._text_bbox(self.t_bbox)
        rows_grouped = self._group_rows(self.t_bbox['horizontal'], row_close_tol=self.row_close_tol)
        rows = self._join_rows(rows_grouped, text_y_max, text_y_min)
        elements = [len(r) for r in rows_grouped]

        if self.columns is not None and self.columns[table_idx] != "":
            # user has to input boundary columns too
            # take (0, pdf_width) by default
            # similar to else condition
            # len can't be 1
            cols = self.columns[table_idx].split(',')
            cols = [float(c) for c in cols]
            cols.insert(0, text_x_min)
            cols.append(text_x_max)
            cols = [(cols[i], cols[i + 1]) for i in range(0, len(cols) - 1)]
        else:
            ncols = max(set(elements), key=elements.count)
            if ncols == 1:
                warnings.warn("No tables found on {}".format(
                    os.path.basename(self.rootname)))
            cols = [(t.x0, t.x1) for r in rows_grouped if len(r) == ncols for t in r]
            cols = self._merge_columns(sorted(cols), col_close_tol=self.col_close_tol)
            inner_text = []
            for i in range(1, len(cols)):
                left = cols[i - 1][1]
                right = cols[i][0]
                inner_text.extend([t for direction in self.t_bbox
                                     for t in self.t_bbox[direction]
                                     if t.x0 > left and t.x1 < right])
            outer_text = [t for direction in self.t_bbox
                            for t in self.t_bbox[direction]
                            if t.x0 > cols[-1][1] or t.x1 < cols[0][0]]
            inner_text.extend(outer_text)
            cols = self._add_columns(cols, inner_text, self.row_close_tol)
            cols = self._join_columns(cols, text_x_min, text_x_max)

        return cols, rows

    def _generate_table(self, table_idx, cols, rows, **kwargs):
        table = Table(cols, rows)
        table = table.set_all_edges()
        pos_errors = []
        for direction in self.t_bbox:
            for t in self.t_bbox[direction]:
                indices, error = get_table_index(
                    table, t, direction, split_text=self.split_text,
                    flag_size=self.flag_size)
                if indices[:2] != (-1, -1):
                    pos_errors.append(error)
                    for r_idx, c_idx, text in indices:
                        table.cells[r_idx][c_idx].text = text
        accuracy = compute_accuracy([[100, pos_errors]])

        data = table.data
        table.df = pd.DataFrame(data)
        table.shape = table.df.shape

        whitespace = compute_whitespace(data)
        table.flavor = 'stream'
        table.accuracy = accuracy
        table.whitespace = whitespace
        table.order = table_idx + 1
        table.page = int(os.path.basename(self.rootname).replace('page-', ''))

        # for plotting
        _text = []
        _text.extend([(t.x0, t.y0, t.x1, t.y1) for t in self.horizontal_text])
        _text.extend([(t.x0, t.y0, t.x1, t.y1) for t in self.vertical_text])
        table._text = _text
        table._image = None
        table._segments = None

        return table

    def extract_tables(self, filename):
        self._generate_layout(filename)
        logger.info('Processing {}'.format(os.path.basename(self.rootname)))

        if not self.horizontal_text:
            warnings.warn("No tables found on {}".format(
                os.path.basename(self.rootname)))
            return []

        self._generate_table_bbox()

        _tables = []
        # sort tables based on y-coord
        for table_idx, tk in enumerate(sorted(
                self.table_bbox.keys(), key=lambda x: x[1], reverse=True)):
            cols, rows = self._generate_columns_and_rows(table_idx, tk)
            table = self._generate_table(table_idx, cols, rows)
            _tables.append(table)

        return _tables
