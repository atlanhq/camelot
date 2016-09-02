from __future__ import division
import os
import types
import copy_reg
import logging

from wand.image import Image

from .image_ops import (adaptive_threshold, extract_lines, extract_table_contours,
                        extract_table_joints)
from .table import Table
from .utils import (transform, segments_bbox, text_bbox, detect_vertical, merge_close_values,
                    get_row_index, get_column_index, get_score, reduce_index,
                    outline, fill_spanning, count_empty, encode_list, pdf_to_text)


__all__ = ['Lattice']


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


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
        img, threshold = adaptive_threshold(imagename, invert=self.invert)
        vmask, v_segments = extract_lines(threshold, direction='vertical',
            scale=self.scale)
        hmask, h_segments = extract_lines(threshold, direction='horizontal',
            scale=self.scale)
        contours = extract_table_contours(vmask, hmask)
        table_bbox = extract_table_joints(contours, vmask, hmask)
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
            v_s, h_s = segments_bbox(k, v_segments, h_segments)
            t_bbox = text_bbox(k, text)
            table_info['text_p'] = 100 * (1 - (len(t_bbox) / len(text)))
            table_rotation = detect_vertical(t_bbox)
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

            rerror = []
            cerror = []
            for t in text:
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
                r_idx, c_idx = reduce_index(table, table_rotation, r_idx, c_idx)
                table.cells[r_idx][c_idx].add_object(t)

            for i in range(len(table.cells)):
                for j in range(len(table.cells[i])):
                    t_bbox = table.cells[i][j].get_objects()
                    try:
                        cell_rotation = detect_vertical(t_bbox)
                    except ZeroDivisionError:
                        cell_rotation = ''
                        pass
                    # fill text after sorting it
                    if cell_rotation == '':
                        t_bbox.sort(key=lambda x: (-x.y0, x.x0))
                    elif cell_rotation == 'left':
                        t_bbox.sort(key=lambda x: (x.x0, x.y0))
                    elif cell_rotation == 'right':
                        t_bbox.sort(key=lambda x: (-x.x0, -x.y0))
                    table.cells[i][j].add_text(''.join([t.get_text()
                        for t in t_bbox]))

            score = get_score([[50, rerror], [50, cerror]])
            table_info['score'] = score

            if self.fill is not None:
                table = fill_spanning(table, fill=self.fill)
            ar = table.get_list()
            if table_rotation == 'left':
                ar = zip(*ar[::-1])
            elif table_rotation == 'right':
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