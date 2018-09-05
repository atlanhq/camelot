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
from .utils import (scale_to_pdf, scale_to_image, segments_bbox, text_in_bbox,
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


class Stream:
    def __init__(self, table_area=None, columns=None, ytol=[2], mtol=[0],
                 margins=(1.0, 0.5, 0.1), split_text=False, flag_size=True,
                 debug=False):

        self.method = 'stream'
        self.table_area = table_area
        self.columns = columns
        self.ytol = ytol
        self.mtol = mtol
        self.char_margin, self.line_margin, self.word_margin = margins
        self.split_text = split_text
        self.flag_size = flag_size
        self.debug = debug

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

    def extract_tables(self, pdfname):
        layout, dim = get_page_layout(pdfname, char_margin=self.char_margin,
            line_margin=self.line_margin, word_margin=self.word_margin)
        lttextlh = get_text_objects(layout, ltype="lh")
        lttextlv = get_text_objects(layout, ltype="lv")
        ltchar = get_text_objects(layout, ltype="char")
        width, height = dim
        bname, __ = os.path.splitext(pdfname)
        logger.info('Processing {0}.'.format(os.path.basename(bname)))
        if not lttextlh:
            warnings.warn("{0}: Page contains no text.".format(
                os.path.basename(bname)))
            return {os.path.basename(bname): None}

        g = Geometry()
        if self.debug:
            text = []
            text.extend([(t.x0, t.y0, t.x1, t.y1) for t in lttextlh])
            text.extend([(t.x0, t.y0, t.x1, t.y1) for t in lttextlv])
            g.text = text

        if self.table_area is not None:
            if self.columns is not None:
                if len(self.table_area) != len(self.columns):
                    raise ValueError("{0}: Length of table area and columns"
                                     " should be equal.".format(os.path.basename(bname)))

            table_bbox = {}
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = float(x1)
                y1 = float(y1)
                x2 = float(x2)
                y2 = float(y2)
                table_bbox[(x1, y2, x2, y1)] = None
        else:
            table_bbox = {(0, 0, width, height): None}

        if len(self.ytol) == 1 and self.ytol[0] == 2:
            ytolerance = copy.deepcopy(self.ytol) * len(table_bbox)
        else:
            ytolerance = copy.deepcopy(self.ytol)

        if len(self.mtol) == 1 and self.mtol[0] == 0:
            mtolerance = copy.deepcopy(self.mtol) * len(table_bbox)
        else:
            mtolerance = copy.deepcopy(self.mtol)

        _tables = []
        # sort tables based on y-coord
        for table_no, k in enumerate(sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True)):
            # select elements which lie within table_bbox
            t_bbox = {}
            t_bbox['horizontal'] = text_in_bbox(k, lttextlh)
            t_bbox['vertical'] = text_in_bbox(k, lttextlv)
            for direction in t_bbox:
                t_bbox[direction].sort(key=lambda x: (-x.y0, x.x0))
            text_x_min, text_y_min, text_x_max, text_y_max = self._text_bbox(t_bbox)
            rows_grouped = self._group_rows(t_bbox['horizontal'], ytol=ytolerance[table_no])
            rows = self._join_rows(rows_grouped, text_y_max, text_y_min)
            elements = [len(r) for r in rows_grouped]

            guess = False
            if self.columns is not None and self.columns[table_no] != "":
                # user has to input boundary columns too
                # take (0, width) by default
                # similar to else condition
                # len can't be 1
                cols = self.columns[table_no].split(',')
                cols = [float(c) for c in cols]
                cols.insert(0, text_x_min)
                cols.append(text_x_max)
                cols = [(cols[i], cols[i + 1]) for i in range(0, len(cols) - 1)]
            else:
                guess = True
                ncols = max(set(elements), key=elements.count)
                len_non_mode = len(filter(lambda x: x != ncols, elements))
                if ncols == 1:
                    # no tables detected
                    warnings.warn("{0}: Page contains no tables.".format(
                        os.path.basename(bname)))
                cols = [(t.x0, t.x1)
                    for r in rows_grouped if len(r) == ncols for t in r]
                cols = self._merge_columns(sorted(cols), mtol=mtolerance[table_no])
                inner_text = []
                for i in range(1, len(cols)):
                    left = cols[i - 1][1]
                    right = cols[i][0]
                    inner_text.extend([t for direction in t_bbox
                                       for t in t_bbox[direction]
                                       if t.x0 > left and t.x1 < right])
                outer_text = [t for direction in t_bbox
                              for t in t_bbox[direction]
                              if t.x0 > cols[-1][1] or t.x1 < cols[0][0]]
                inner_text.extend(outer_text)
                cols = self._add_columns(cols, inner_text, ytolerance[table_no])
                cols = self._join_columns(cols, text_x_min, text_x_max)

            table = Table(cols, rows)
            table = table.set_all_edges()
            pos_errors = []
            for direction in t_bbox:
                for t in t_bbox[direction]:
                    indices, error = get_table_index(
                        table, t, direction, split_text=self.split_text,
                        flag_size=self.flag_size)
                    if indices[:2] != (-1, -1):
                        pos_errors.append(error)
                        for r_idx, c_idx, text in indices:
                            table.cells[r_idx][c_idx].add_text(text)
            if guess:
                accuracy = compute_accuracy([[66, pos_errors], [34, [len_non_mode / len(elements)]]])
            else:
                accuracy = compute_accuracy([[100, pos_errors]])

            data = table.data
            data = encode_(data)
            table.df = pd.DataFrame(data)
            table.shape = table.df.shape

            whitespace, __, __ = count_empty(data)
            table.accuracy = accuracy
            table.whitespace = whitespace
            table.order = table_no + 1
            table.page = int(os.path.basename(bname).replace('page-', ''))

            _tables.append(table)

        return _tables, g


class Lattice:
    def __init__(self, table_area=None, fill=None, mtol=[2], jtol=[2],
                 blocksize=15, threshold_constant=-2, scale=15, iterations=0,
                 invert=False, margins=(1.0, 0.5, 0.1), split_text=False,
                 flag_size=True, shift_text=['l', 't'], debug=None):

        self.method = 'lattice'
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

    def extract_tables(self, pdfname):
        layout, dim = get_page_layout(pdfname, char_margin=self.char_margin,
            line_margin=self.line_margin, word_margin=self.word_margin)
        lttextlh = get_text_objects(layout, ltype="lh")
        lttextlv = get_text_objects(layout, ltype="lv")
        ltchar = get_text_objects(layout, ltype="char")
        width, height = dim
        bname, __ = os.path.splitext(pdfname)
        logger.info('Processing {0}.'.format(os.path.basename(bname)))
        if not ltchar:
            warnings.warn("{0}: Page contains no text.".format(
                os.path.basename(bname)))
            return {os.path.basename(bname): None}

        imagename = ''.join([bname, '.png'])
        gs_call = [
            "-q", "-sDEVICE=png16m", "-o", imagename, "-r600", pdfname
        ]
        if "ghostscript" in subprocess.check_output(["gs", "-version"]).lower():
            gs_call.insert(0, "gs")
        else:
            gs_call.insert(0, "gsc")
        subprocess.call(gs_call, stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT)

        img, threshold = adaptive_threshold(imagename, invert=self.invert,
            blocksize=self.blocksize, c=self.threshold_constant)
        pdf_x = width
        pdf_y = height
        img_x = img.shape[1]
        img_y = img.shape[0]
        sc_x_image = img_x / float(pdf_x)
        sc_y_image = img_y / float(pdf_y)
        sc_x_pdf = pdf_x / float(img_x)
        sc_y_pdf = pdf_y / float(img_y)
        factors_image = (sc_x_image, sc_y_image, pdf_y)
        factors_pdf = (sc_x_pdf, sc_y_pdf, img_y)

        vmask, v_segments = find_lines(threshold, direction='vertical',
            scale=self.scale, iterations=self.iterations)
        hmask, h_segments = find_lines(threshold, direction='horizontal',
            scale=self.scale, iterations=self.iterations)

        if self.table_area is not None:
            areas = []
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = float(x1)
                y1 = float(y1)
                x2 = float(x2)
                y2 = float(y2)
                x1, y1, x2, y2 = scale_to_image((x1, y1, x2, y2), factors_image)
                areas.append((x1, y1, abs(x2 - x1), abs(y2 - y1)))
            table_bbox = find_table_joints(areas, vmask, hmask)
        else:
            contours = find_table_contours(vmask, hmask)
            table_bbox = find_table_joints(contours, vmask, hmask)

        if len(self.mtol) == 1 and self.mtol[0] == 2:
            mtolerance = copy.deepcopy(self.mtol) * len(table_bbox)
        else:
            mtolerance = copy.deepcopy(self.mtol)

        if len(self.jtol) == 1 and self.jtol[0] == 2:
            jtolerance = copy.deepcopy(self.jtol) * len(table_bbox)
        else:
            jtolerance = copy.deepcopy(self.jtol)

        g = Geometry()
        if self.debug:
            g.images = (img, table_bbox)

        table_bbox, v_segments, h_segments = scale_to_pdf(table_bbox, v_segments,
            h_segments, factors_pdf)

        if self.debug:
            g.segments = (v_segments, h_segments)

        _tables = []
        # sort tables based on y-coord
        for table_no, k in enumerate(sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True)):
            # select elements which lie within table_bbox
            t_bbox = {}
            v_s, h_s = segments_bbox(k, v_segments, h_segments)
            t_bbox['horizontal'] = text_in_bbox(k, lttextlh)
            t_bbox['vertical'] = text_in_bbox(k, lttextlv)
            for direction in t_bbox:
                t_bbox[direction].sort(key=lambda x: (-x.y0, x.x0))
            cols, rows = zip(*table_bbox[k])
            cols, rows = list(cols), list(rows)
            cols.extend([k[0], k[2]])
            rows.extend([k[1], k[3]])
            # sort horizontal and vertical segments
            cols = merge_close_values(sorted(cols), mtol=mtolerance[table_no])
            rows = merge_close_values(
                sorted(rows, reverse=True), mtol=mtolerance[table_no])
            # make grid using x and y coord of shortlisted rows and cols
            cols = [(cols[i], cols[i + 1])
                    for i in range(0, len(cols) - 1)]
            rows = [(rows[i], rows[i + 1])
                    for i in range(0, len(rows) - 1)]

            table = Table(cols, rows)
            # set table edges to True using ver+hor lines
            table = table.set_edges(v_s, h_s, jtol=jtolerance[table_no])
            # set spanning cells to True
            table = table.set_spanning()
            # set table border edges to True
            table = table.set_border_edges()

            pos_errors = []
            for direction in ['vertical', 'horizontal']:
                for t in t_bbox[direction]:
                    indices, error = get_table_index(
                        table, t, direction, split_text=self.split_text,
                        flag_size=self.flag_size)
                    if indices[:2] != (-1, -1):
                        pos_errors.append(error)
                        indices = self._reduce_index(table, indices, shift_text=self.shift_text)
                        for r_idx, c_idx, text in indices:
                            table.cells[r_idx][c_idx].add_text(text)
            accuracy = compute_accuracy([[100, pos_errors]])

            if self.fill is not None:
                table = self._fill_spanning(table, fill=self.fill)

            data = table.data
            data = encode_(data)
            table.df = pd.DataFrame(data)
            table.shape = table.df.shape

            whitespace, __, __ = count_empty(data)
            table.accuracy = accuracy
            table.whitespace = whitespace
            table.order = table_no + 1
            table.page = int(os.path.basename(bname).replace('page-', ''))

            _tables.append(table)

        if self.debug:
            g.tables = _tables

        return _tables, g