from __future__ import division
import os
import sys
import copy
import types
import logging
import copy_reg
import warnings
import subprocess

import numpy as np
import pandas as pd

from .core import Table, Geometry
from .image_processing import (adaptive_threshold, find_lines, find_table_contours,
                               find_table_joints)
from .utils import (scale_image, scale_pdf, segments_in_bbox, text_in_bbox,
                    merge_close_values, get_table_index, compute_accuracy, count_empty,
                    get_text_objects, get_page_layout, encode_)


__all__ = ['Stream', 'Lattice']
logger = logging.getLogger('app_logger')


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


class BaseParser(object):
    """

    """
    def _generate_layout(self, filename):
        self.filename = filename
        self.layout, self.dimensions = get_page_layout(
            self.filename,
            char_margin=self.char_margin,
            line_margin=self.line_margin,
            word_margin=self.word_margin)
        self.horizontal_text = get_text_objects(self.layout, ltype="lh")
        self.vertical_text = get_text_objects(self.layout, ltype="lv")
        self.pdf_width, self.pdf_height = self.dimensions
        self.basename, __ = os.path.splitext(self.filename)
        self.g = Geometry()


class Stream(BaseParser):
    """

    """
    def __init__(self, table_area=None, columns=None, ytol=2, mtol=0,
                 margins=(1.0, 0.5, 0.1), split_text=False, flag_size=True,
                 debug=False):
        self.table_area = table_area
        self.columns = columns
        self._validate_columns()
        self.ytol = ytol
        self.mtol = mtol
        self.char_margin, self.line_margin, self.word_margin = margins
        self.split_text = split_text
        self.flag_size = flag_size
        self.debug = debug

    def _validate_columns(self):
        if self.table_area is not None and self.columns is not None:
            if len(self.table_area) != len(self.columns):
                raise ValueError("Length of table_area and columns"
                                 " should be equal.")

    @staticmethod
    def _text_bbox(t_bbox):
        xmin = min([t.x0 for direction in t_bbox for t in t_bbox[direction]])
        ymin = min([t.y0 for direction in t_bbox for t in t_bbox[direction]])
        xmax = max([t.x1 for direction in t_bbox for t in t_bbox[direction]])
        ymax = max([t.y1 for direction in t_bbox for t in t_bbox[direction]])
        text_bbox = (xmin, ymin, xmax, ymax)
        return text_bbox

    @staticmethod
    def _group_rows(text, ytol=2):
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

    @staticmethod
    def _merge_columns(l, mtol=0):
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

    @staticmethod
    def _join_rows(rows_grouped, text_y_max, text_y_min):
        row_mids = [sum([(t.y0 + t.y1) / 2 for t in r]) / len(r)
                    if len(r) > 0 else 0 for r in rows_grouped]
        rows = [(row_mids[i] + row_mids[i - 1]) / 2 for i in range(1, len(row_mids))]
        rows.insert(0, text_y_max)
        rows.append(text_y_min)
        rows = [(rows[i], rows[i + 1])
                for i in range(0, len(rows) - 1)]
        return rows

    @staticmethod
    def _add_columns(cols, text, ytol):
        if text:
            text = Stream._group_rows(text, ytol=ytol)
            elements = [len(r) for r in text]
            new_cols = [(t.x0, t.x1)
                for r in text if len(r) == max(elements) for t in r]
            cols.extend(Stream._merge_columns(sorted(new_cols)))
        return cols

    @staticmethod
    def _join_columns(cols, text_x_min, text_x_max):
        cols = sorted(cols)
        cols = [(cols[i][0] + cols[i - 1][1]) / 2 for i in range(1, len(cols))]
        cols.insert(0, text_x_min)
        cols.append(text_x_max)
        cols = [(cols[i], cols[i + 1])
                for i in range(0, len(cols) - 1)]
        return cols

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
        rows_grouped = self._group_rows(self.t_bbox['horizontal'], ytol=self.ytol)
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
                # no tables condition
                warnings.warn("No tables found on {}".format(
                    os.path.basename(self.basename)))
            cols = [(t.x0, t.x1)
                for r in rows_grouped if len(r) == ncols for t in r]
            cols = self._merge_columns(sorted(cols), mtol=self.mtol)
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
            cols = self._add_columns(cols, inner_text, self.ytol)
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
                        table.cells[r_idx][c_idx].add_text(text)
        accuracy = compute_accuracy([[100, pos_errors]])

        data = table.data
        data = encode_(data)
        table.df = pd.DataFrame(data)
        table.shape = table.df.shape

        whitespace, __, __ = count_empty(data)
        table.accuracy = accuracy
        table.whitespace = whitespace
        table.order = table_idx + 1
        table.page = int(os.path.basename(self.basename).replace('page-', ''))

        return table

    def extract_tables(self, filename):
        """

        Parameters
        ----------
        filename

        Returns
        -------

        """
        logger.info('Processing {}'.format(os.path.basename(filename)))
        self._generate_layout(filename)

        if not self.horizontal_text:
            warnings.warn("No tables found on {}".format(
                os.path.basename(self.basename)))
            return [], self.g

        self._generate_table_bbox()

        _tables = []
        # sort tables based on y-coord
        for table_idx, tk in enumerate(sorted(self.table_bbox.keys(),
                key=lambda x: x[1], reverse=True)):
            cols, rows = self._generate_columns_and_rows(table_idx, tk)
            table = self._generate_table(table_idx, cols, rows)
            _tables.append(table)

        if self.debug:
            text = []
            text.extend([(t.x0, t.y0, t.x1, t.y1) for t in self.horizontal_text])
            text.extend([(t.x0, t.y0, t.x1, t.y1) for t in self.vertical_text])
            self.g.text = text

        return _tables, self.g


class Lattice(BaseParser):
    """

    """
    def __init__(self, table_area=None, fill=None, mtol=2, jtol=2,
                 blocksize=15, threshold_constant=-2, scale=15, iterations=0,
                 invert=False, margins=(1.0, 0.5, 0.1), split_text=False,
                 flag_size=True, shift_text=['l', 't'], debug=None):
        self.table_area = table_area
        self.fill = fill
        self.mtol = mtol
        self.jtol = jtol
        self.blocksize = blocksize
        self.threshold_constant = threshold_constant
        self.scale = scale
        self.iterations = iterations
        self.invert = invert
        self.char_margin, self.line_margin, self.word_margin = margins
        self.split_text = split_text
        self.flag_size = flag_size
        self.shift_text = shift_text
        self.debug = debug

    @staticmethod
    def _reduce_index(t, idx, shift_text):
        indices = []
        for r_idx, c_idx, text in idx:
            for d in shift_text:
                if d == 'l':
                    if t.cells[r_idx][c_idx].spanning_h:
                        while not t.cells[r_idx][c_idx].left:
                            c_idx -= 1
                if d == 'r':
                    if t.cells[r_idx][c_idx].spanning_h:
                        while not t.cells[r_idx][c_idx].right:
                            c_idx += 1
                if d == 't':
                    if t.cells[r_idx][c_idx].spanning_v:
                        while not t.cells[r_idx][c_idx].top:
                            r_idx -= 1
                if d == 'b':
                    if t.cells[r_idx][c_idx].spanning_v:
                        while not t.cells[r_idx][c_idx].bottom:
                            r_idx += 1
            indices.append((r_idx, c_idx, text))
        return indices

    @staticmethod
    def _fill_spanning(t, fill=None):
        for f in fill:
            if f == "h":
                for i in range(len(t.cells)):
                    for j in range(len(t.cells[i])):
                        if t.cells[i][j].get_text().strip() == '':
                            if t.cells[i][j].spanning_h and not t.cells[i][j].left:
                                t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
            elif f == "v":
                for i in range(len(t.cells)):
                    for j in range(len(t.cells[i])):
                        if t.cells[i][j].get_text().strip() == '':
                            if t.cells[i][j].spanning_v and not t.cells[i][j].top:
                                t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
        return t

    def _generate_image(self):
        self.imagename = ''.join([self.basename, '.png'])
        gs_call = [
            "-q", "-sDEVICE=png16m", "-o", self.imagename, "-r600", self.filename
        ]
        if "ghostscript" in subprocess.check_output(["gs", "-version"]).lower():
            gs_call.insert(0, "gs")
        else:
            gs_call.insert(0, "gsc")
        subprocess.call(gs_call, stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT)

    def _generate_table_bbox(self):
        self.image, self.threshold = adaptive_threshold(self.imagename, invert=self.invert,
            blocksize=self.blocksize, c=self.threshold_constant)
        image_width = self.image.shape[1]
        image_height = self.image.shape[0]
        image_width_scaler = image_width / float(self.pdf_width)
        image_height_scaler = image_height / float(self.pdf_height)
        pdf_width_scaler = self.pdf_width / float(image_width)
        pdf_height_scaler = self.pdf_height / float(image_height)
        image_scalers = (image_width_scaler, image_height_scaler, self.pdf_height)
        pdf_scalers = (pdf_width_scaler, pdf_height_scaler, image_height)

        vertical_mask, vertical_segments = find_lines(self.threshold,
            direction='vertical', scale=self.scale, iterations=self.iterations)
        horizontal_mask, horizontal_segments = find_lines(self.threshold,
            direction='horizontal', scale=self.scale, iterations=self.iterations)

        if self.table_area is not None:
            areas = []
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = float(x1)
                y1 = float(y1)
                x2 = float(x2)
                y2 = float(y2)
                x1, y1, x2, y2 = scale_pdf((x1, y1, x2, y2), image_scalers)
                areas.append((x1, y1, abs(x2 - x1), abs(y2 - y1)))
            table_bbox = find_table_joints(areas, vertical_mask, horizontal_mask)
        else:
            contours = find_table_contours(vertical_mask, horizontal_mask)
            table_bbox = find_table_joints(contours, vertical_mask, horizontal_mask)

        self.table_bbox_unscaled = copy.deepcopy(table_bbox)

        self.table_bbox, self.vertical_segments, self.horizontal_segments = scale_image(
            table_bbox, vertical_segments, horizontal_segments, pdf_scalers)

    def _generate_columns_and_rows(self, table_idx, tk):
        # select elements which lie within table_bbox
        t_bbox = {}
        v_s, h_s = segments_in_bbox(
            tk, self.vertical_segments, self.horizontal_segments)
        t_bbox['horizontal'] = text_in_bbox(tk, self.horizontal_text)
        t_bbox['vertical'] = text_in_bbox(tk, self.vertical_text)
        self.t_bbox = t_bbox

        for direction in t_bbox:
            t_bbox[direction].sort(key=lambda x: (-x.y0, x.x0))

        cols, rows = zip(*self.table_bbox[tk])
        cols, rows = list(cols), list(rows)
        cols.extend([tk[0], tk[2]])
        rows.extend([tk[1], tk[3]])
        # sort horizontal and vertical segments
        cols = merge_close_values(sorted(cols), mtol=self.mtol)
        rows = merge_close_values(sorted(rows, reverse=True), mtol=self.mtol)
        # make grid using x and y coord of shortlisted rows and cols
        cols = [(cols[i], cols[i + 1])
                for i in range(0, len(cols) - 1)]
        rows = [(rows[i], rows[i + 1])
                for i in range(0, len(rows) - 1)]

        return cols, rows, v_s, h_s

    def _generate_table(self, table_idx, cols, rows, **kwargs):
        v_s = kwargs.get('v_s')
        h_s = kwargs.get('h_s')
        if v_s is None or h_s is None:
            raise ValueError('No segments found on {}'.format(self.basename))

        table = Table(cols, rows)
        # set table edges to True using ver+hor lines
        table = table.set_edges(v_s, h_s, jtol=self.jtol)
        # set spanning cells to True
        table = table.set_spanning()
        # set table border edges to True
        table = table.set_border_edges()

        pos_errors = []
        for direction in self.t_bbox:
            for t in self.t_bbox[direction]:
                indices, error = get_table_index(
                    table, t, direction, split_text=self.split_text,
                    flag_size=self.flag_size)
                if indices[:2] != (-1, -1):
                    pos_errors.append(error)
                    indices = Lattice._reduce_index(table, indices, shift_text=self.shift_text)
                    for r_idx, c_idx, text in indices:
                        table.cells[r_idx][c_idx].add_text(text)
        accuracy = compute_accuracy([[100, pos_errors]])

        if self.fill is not None:
            table = Lattice._fill_spanning(table, fill=self.fill)

        data = table.data
        data = encode_(data)
        table.df = pd.DataFrame(data)
        table.shape = table.df.shape

        whitespace, __, __ = count_empty(data)
        table.accuracy = accuracy
        table.whitespace = whitespace
        table.order = table_idx + 1
        table.page = int(os.path.basename(self.basename).replace('page-', ''))

        return table

    def extract_tables(self, filename):
        """

        Parameters
        ----------
        filename

        Returns
        -------

        """
        logger.info('Processing {}'.format(os.path.basename(filename)))
        self._generate_layout(filename)

        if not self.horizontal_text:
            warnings.warn("No tables found on {}".format(
                os.path.basename(self.basename)))
            return [], self.g

        self._generate_image()
        self._generate_table_bbox()

        _tables = []
        # sort tables based on y-coord
        for table_idx, tk in enumerate(sorted(self.table_bbox.keys(),
                key=lambda x: x[1], reverse=True)):
            cols, rows, v_s, h_s = self._generate_columns_and_rows(table_idx, tk)
            table = self._generate_table(table_idx, cols, rows, v_s=v_s, h_s=h_s)
            _tables.append(table)

        if self.debug:
            self.g.images = (self.image, self.table_bbox_unscaled)
            self.g.segments = (self.vertical_segments, self.horizontal_segments)
            self.g.tables = _tables

        return _tables, self.g