from __future__ import division
import os
import types
import logging
import copy_reg
import subprocess

from .imgproc import (adaptive_threshold, find_lines, find_table_contours,
                      find_table_joints)
from .table import Table
from .utils import (scale_to_pdf, scale_to_image, segments_bbox, text_bbox,
                    detect_vertical, merge_close_values, get_row_index,
                    get_column_index, get_score, reduce_index, outline,
                    fill_spanning, count_empty, encode_list, pdf_to_text)


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
    def __init__(self, table_area=None, fill=None, mtol=[2], scale=15,
                 invert=False, margins=(2.0, 0.5, 0.1), debug=None):

        self.method = 'lattice'
        self.table_area = table_area
        self.fill = fill
        self.mtol = mtol
        self.scale = scale
        self.invert = invert
        self.char_margin, self.line_margin, self.word_margin = margins
        self.debug = debug

    def get_tables(self, pdfname):
        """Returns all tables found in given pdf.

        Returns
        -------
        tables : dict
            Dictionary with page number as key and list of tables on that
            page as value.
        """
        ltchar, lttextlh, width, height = pdf_to_text(pdfname, self.char_margin,
            self.line_margin, self.word_margin)
        bname, __ = os.path.splitext(pdfname)
        if not ltchar:
            logging.warning("{0}: PDF has no text. It may be an image.".format(
                os.path.basename(bname)))
            return None

        imagename = ''.join([bname, '.jpg'])
        gs_call = [
            "-q", "-sDEVICE=png16m", "-o", imagename, "-r600", pdfname
        ]
        if "ghostscript" in subprocess.check_output(["gs", "-version"]).lower():
            gs_call.insert(0, "gs")
        else:
            gs_call.insert(0, "gsc")
        subprocess.call(gs_call)

        img, threshold = adaptive_threshold(imagename, invert=self.invert)
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
            scale=self.scale)
        hmask, h_segments = find_lines(threshold, direction='horizontal',
            scale=self.scale)

        if self.table_area is not None:
            if self.fill is not None:
                if len(self.table_area) != len(self.fill):
                    raise ValueError("message")
            areas = []
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)
                x1, y1, x2, y2 = scale_to_image((x1, y1, x2, y2), factors_image)
                areas.append((x1, y1, abs(x2 - x1), abs(y2 - y1)))
            table_bbox = find_table_joints(areas, vmask, hmask)
        else:
            contours = find_table_contours(vmask, hmask)
            table_bbox = find_table_joints(contours, vmask, hmask)

        if len(self.mtol) == 1 and self.mtol[0] == 2:
            self.mtol = self.mtol * len(table_bbox)

        if self.debug:
            self.debug_images = (img, table_bbox)

        table_bbox, v_segments, h_segments = scale_to_pdf(table_bbox, v_segments,
            h_segments, factors_pdf)

        if self.debug:
            self.debug_segments = (v_segments, h_segments)
            self.debug_tables = []

        page = {}
        tables = {}
        table_no = 0
        # sort tables based on y-coord
        for k in sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True):
            # select elements which lie within table_bbox
            table_data = {}
            v_s, h_s = segments_bbox(k, v_segments, h_segments)
            t_bbox = text_bbox(k, ltchar)
            table_data['text_p'] = 100 * (1 - (len(t_bbox) / len(ltchar)))
            table_rotation = detect_vertical(t_bbox)
            cols, rows = zip(*table_bbox[k])
            cols, rows = list(cols), list(rows)
            cols.extend([k[0], k[2]])
            rows.extend([k[1], k[3]])
            # sort horizontal and vertical segments
            cols = merge_close_values(sorted(cols), mtol=self.mtol[table_no])
            rows = merge_close_values(
                sorted(rows, reverse=True), mtol=self.mtol[table_no])
            # make grid using x and y coord of shortlisted rows and cols
            cols = [(cols[i], cols[i + 1])
                    for i in range(0, len(cols) - 1)]
            rows = [(rows[i], rows[i + 1])
                    for i in range(0, len(rows) - 1)]
            table = Table(cols, rows)
            # set table edges to True using ver+hor lines
            table = table.set_edges(v_s, h_s)
            nouse = table.nocont_ / (len(v_s) + len(h_s))
            table_data['line_p'] = 100 * (1 - nouse)
            # set spanning cells to True
            table = table.set_spanning()
            # set table border edges to True
            table = outline(table)

            if self.debug:
                self.debug_tables.append(table)

            rerror = []
            cerror = []
            for t in ltchar:
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
            table_data['score'] = score

            if self.fill is not None:
                table = fill_spanning(table, fill=self.fill[table_no])
            ar = table.get_list()
            if table_rotation == 'left':
                ar = zip(*ar[::-1])
            elif table_rotation == 'right':
                ar = zip(*ar[::1])
                ar.reverse()
            ar = encode_list(ar)
            table_data['data'] = ar
            empty_p, r_nempty_cells, c_nempty_cells = count_empty(ar)
            table_data['empty_p'] = empty_p
            table_data['r_nempty_cells'] = r_nempty_cells
            table_data['c_nempty_cells'] = c_nempty_cells
            table_data['nrows'] = len(ar)
            table_data['ncols'] = len(ar[0])
            tables['table-{0}'.format(table_no + 1)] = table_data
            table_no += 1
        page[os.path.basename(bname)] = tables

        if self.debug:
            return None

        return page