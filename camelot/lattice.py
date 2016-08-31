from __future__ import division
import os
import types
import copy_reg
import logging

import cv2
import numpy as np

from wand.image import Image

from .table import Table
from .utils import (transform, elements_bbox, detect_vertical, merge_close_values,
                    get_row_index, get_column_index, get_score, reduce_index,
                    outline, fill_spanning, count_empty, encode_list, pdf_to_text)


__all__ = ['Lattice']


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


def _adaptive_threshold(imagename, invert=False):
    img = cv2.imread(imagename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if invert:
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
            15, -0.2)
    else:
        threshold = cv2.adaptiveThreshold(
            np.invert(gray), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15, -0.2)
    return img, threshold


def _extract_lines(threshold, direction=None, scale=15):
    lines = []

    if direction == 'vertical':
        size = threshold.shape[0] // scale
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    elif direction == 'horizontal':
        size = threshold.shape[1] // scale
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (size, 1))
    elif direction is None:
        raise ValueError("Specify direction as either 'vertical' or"
                         " 'horizontal'")

    threshold = cv2.erode(threshold, el, (-1, -1))
    threshold = cv2.dilate(threshold, el, (-1, -1))

    dmask = threshold  # findContours modifies source image

    try:
        _, contours, _ = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except ValueError:
        contours, _ = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        if direction == 'vertical':
            lines.append(((x1 + x2) / 2, y2, (x1 + x2) / 2, y1))
        elif direction == 'horizontal':
            lines.append((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2))

    return dmask, lines


def _extract_table_contours(vertical, horizontal):
    mask = vertical + horizontal
    joints = np.bitwise_and(vertical, horizontal)

    try:
        __, contours, __ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except ValueError:
        contours, __ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    tables = {}
    for c in contours:
        c_poly = cv2.approxPolyDP(c, 3, True)
        x, y, w, h = cv2.boundingRect(c_poly)
        roi = joints[y : y + h, x : x + w]
        try:
            __, jc, __ = cv2.findContours(
                roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        except ValueError:
            jc, __ = cv2.findContours(
                roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if len(jc) <= 4:  # remove contours with less than 4 joints
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2 * jx + jw) / 2, y + (2 * jy + jh) / 2
            joint_coords.append((c1, c2))
        tables[(x, y + h, x + w, y)] = joint_coords

    return tables


class Lattice:
    """Lattice algorithm

    Makes use of pdf geometry by processing its image, to make a table
    and fills text objects in table cells.

    Parameters
    ----------
    pdfobject : camelot.pdf.Pdf

    fill : string
        Fill data in horizontal and/or vertical spanning
        cells. (optional, default: None) {None, 'h', 'v', 'hv'}

    scale : int
        Scaling factor. Large scaling factor leads to smaller lines
        being detected. (optional, default: 15)

    jtol : int
        Tolerance to account for when comparing joint and line
        coordinates. (optional, default: 2)

    mtol : int
        Tolerance to account for when merging lines which are
        very close. (optional, default: 2)

    invert : bool
        Invert pdf image to make sure that lines are in foreground.
        (optional, default: False)

    debug : string
        Debug by visualizing pdf geometry.
        (optional, default: None) {'contour', 'line', 'joint', 'table'}

    Attributes
    ----------
    tables : dict
        Dictionary with page number as key and list of tables on that
        page as value.
    """

    def __init__(self, fill=None, scale=15, jtol=2, mtol=2,
                 invert=False, pdf_margin=(2.0, 0.5, 0.1), debug=None):

        self.method = 'lattice'
        self.fill = fill
        self.scale = scale
        self.jtol = jtol
        self.mtol = mtol
        self.invert = invert
        self.char_margin, self.line_margin, self.word_margin = pdf_margin
        self.debug = debug

    def get_tables(self, pdfname):
        """Returns all tables found in given pdf.

        Returns
        -------
        tables : dict
            Dictionary with page number as key and list of tables on that
            page as value.
        """
        text, __, width, height = pdf_to_text(pdfname, self.char_margin,
            self.line_margin, self.word_margin)
        bname, __ = os.path.splitext(pdfname)
        if not text:
            logging.warning("{0}: PDF has no text. It may be an image.".format(
                os.path.basename(bname)))
            return None
        imagename = ''.join([bname, '.png'])
        with Image(filename=pdfname, depth=8, resolution=300) as png:
            png.save(filename=imagename)
        pdf_x = width
        pdf_y = height
        img, threshold = _adaptive_threshold(imagename, invert=self.invert)
        vmask, v_segments = _extract_lines(threshold, direction='vertical',
            scale=self.scale)
        hmask, h_segments = _extract_lines(threshold, direction='horizontal',
            scale=self.scale)
        table_bbox = _extract_table_contours(vmask, hmask)
        img_x = img.shape[1]
        img_y = img.shape[0]
        scaling_factor_x = pdf_x / float(img_x)
        scaling_factor_y = pdf_y / float(img_y)

        if self.debug:
            self.debug_images = (img, table_bbox)

        factors = (scaling_factor_x, scaling_factor_y, img_y)
        table_bbox, v_segments, h_segments = transform(table_bbox, v_segments,
                                                       h_segments, factors)

        if self.debug:
            self.debug_segments = (v_segments, h_segments)
            self.debug_tables = []

        pdf_page = {}
        page_tables = {}
        table_no = 1
        # sort tables based on y-coord
        for k in sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True):
            # select edges which lie within table_bbox
            table_info = {}
            text_bbox, v_s, h_s = elements_bbox(k, text, v_segments,
                                                h_segments)
            table_info['text_p'] = 100 * (1 - (len(text_bbox) / len(text)))
            rotated = detect_vertical(text_bbox)
            cols, rows = zip(*table_bbox[k])
            cols, rows = list(cols), list(rows)
            cols.extend([k[0], k[2]])
            rows.extend([k[1], k[3]])
            # sort horizontal and vertical segments
            cols = merge_close_values(sorted(cols), mtol=self.mtol)
            rows = merge_close_values(
                sorted(rows, reverse=True), mtol=self.mtol)
            # make grid using x and y coord of shortlisted rows and cols
            cols = [(cols[i], cols[i + 1])
                    for i in range(0, len(cols) - 1)]
            rows = [(rows[i], rows[i + 1])
                    for i in range(0, len(rows) - 1)]
            table = Table(cols, rows)
            # set table edges to True using ver+hor lines
            table = table.set_edges(v_s, h_s, jtol=self.jtol)
            nouse = table.nocont_ / (len(v_s) + len(h_s))
            table_info['line_p'] = 100 * (1 - nouse)
            # set spanning cells to True
            table = table.set_spanning()
            # set table border edges to True
            table = outline(table)

            if self.debug:
                self.debug_tables.append(table)

            # fill text after sorting it
            if rotated == '':
                text_bbox.sort(key=lambda x: (-x.y0, x.x0))
            elif rotated == 'left':
                text_bbox.sort(key=lambda x: (x.x0, x.y0))
            elif rotated == 'right':
                text_bbox.sort(key=lambda x: (-x.x0, -x.y0))

            rerror = []
            cerror = []
            for t in text_bbox:
                try:
                    r_idx, rass_error = get_row_index(t, rows)
                except TypeError:
                    # couldn't assign LTChar to any cell
                    continue
                try:
                    c_idx, cass_error = get_column_index(t, cols)
                except TypeError:
                    # couldn't assign LTChar to any cell
                    continue
                rerror.append(rass_error)
                cerror.append(cass_error)
                r_idx, c_idx = reduce_index(
                    table, rotated, r_idx, c_idx)
                table.cells[r_idx][c_idx].add_text(
                    t.get_text().strip('\n'))
            score = get_score([[50, rerror], [50, cerror]])
            table_info['score'] = score

            if self.fill is not None:
                table = fill_spanning(table, fill=self.fill)
            ar = table.get_list()
            if rotated == 'left':
                ar = zip(*ar[::-1])
            elif rotated == 'right':
                ar = zip(*ar[::1])
                ar.reverse()
            ar = encode_list(ar)
            table_info['data'] = ar
            empty_p, r_nempty_cells, c_nempty_cells = count_empty(ar)
            table_info['empty_p'] = empty_p
            table_info['r_nempty_cells'] = r_nempty_cells
            table_info['c_nempty_cells'] = c_nempty_cells
            table_info['nrows'] = len(ar)
            table_info['ncols'] = len(ar[0])
            page_tables['table_{0}'.format(table_no)] = table_info
            table_no += 1
        pdf_page[os.path.basename(bname)] = page_tables

        if self.debug:
            return None

        return pdf_page