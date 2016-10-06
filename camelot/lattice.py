from __future__ import division
import os
import types
import logging
import copy_reg
import subprocess

from .imgproc import (adaptive_threshold, find_lines, find_table_contours,
                      find_table_joints)
from .table import Table
from .utils import (scale_to_pdf, scale_to_image, get_rotation, segments_bbox,
                    text_bbox, merge_close_values, get_row_index,
                    get_column_index, get_score, count_empty, encode_list,
                    get_text_objects, get_page_layout)


__all__ = ['Lattice']


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


def _fill_spanning(t, fill=None):
    """Fills spanning cells.

    Parameters
    ----------
    t : object
        camelot.table.Table

    fill : string
        {'h', 'v', 'hv'}
        Specify to fill spanning cells in horizontal, vertical or both
        directions.
        (optional, default: None)

    Returns
    -------
    t : object
        camelot.table.Table
    """
    if fill == "h":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_h:
                        t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
    elif fill == "v":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_v:
                        t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    elif fill == "hv":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_h:
                        t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
                    elif t.cells[i][j].spanning_v:
                        t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    return t


def _outline(t):
    """Sets table border edges to True.

    Parameters
    ----------
    t : object
        camelot.table.Table

    Returns
    -------
    t : object
        camelot.table.Table
    """
    for i in range(len(t.cells)):
        t.cells[i][0].left = True
        t.cells[i][len(t.cells[i]) - 1].right = True
    for i in range(len(t.cells[0])):
        t.cells[0][i].top = True
        t.cells[len(t.cells) - 1][i].bottom = True
    return t


def _reduce_index(t, rotation, r_idx, c_idx):
    """Reduces index of a text object if it lies within a spanning
    cell taking in account table rotation.

    Parameters
    ----------
    t : object
        camelot.table.Table

    rotation : string
        {'', 'left', 'right'}

    r_idx : int
        Current row index.

    c_idx : int
        Current column index.

    Returns
    -------
    r_idx : int
        Reduced row index.

    c_idx : int
        Reduced column index.
    """
    if not rotation:
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].left:
                c_idx -= 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].top:
                r_idx -= 1
    elif rotation == 'left':
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].left:
                c_idx -= 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].bottom:
                r_idx += 1
    elif rotation == 'right':
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].right:
                c_idx += 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].top:
                r_idx -= 1
    return r_idx, c_idx


class Lattice:
    """Lattice looks for lines in the pdf to form a table.

    If you want to give fill and mtol for each table when specifying
    multiple table areas, make sure that the length of fill and mtol
    is equal to the length of table_area. Mapping between them is based
    on index.

    Parameters
    ----------
    table_area : list
        List of tuples of the form (x1, y1, x2, y2) where
        (x1, y1) -> left-top and (x2, y2) -> right-bottom in PDFMiner's
        coordinate space, denoting table areas to analyze.
        (optional, default: None)

    fill : list
        List of strings specifying directions to fill spanning cells.
        {'h', 'v', 'hv'} to fill spanning cells in horizontal, vertical
        or both directions.
        (optional, default: None)

    mtol : list
        List of ints specifying m-tolerance parameters.
        (optional, default: [2])

    scale : int
        Used to divide the height/width of a pdf to get a structuring
        element for image processing.
        (optional, default: 15)

    invert : bool
        Whether or not to invert the image. Useful when pdfs have
        tables with lines in background.
        (optional, default: False)

    margins : tuple
        PDFMiner margins. (char_margin, line_margin, word_margin)
        (optional, default: (1.0, 0.5, 0.1))

    split_text : bool
        Whether or not to split a text line if it spans across
        multiple cells.
        (optional, default: False)

    gravity : list
        {'l', 'r', 't', 'b'}
        Select one or more from above and pass them as a list to
        specify where the text in a spanning cell should flow.
        (optional, default: None)

    debug : string
        {'contour', 'line', 'joint', 'table'}
        Set to one of the above values to generate a matplotlib plot
        of detected contours, lines, joints and the table generated.
        (optional, default: None)
    """
    def __init__(self, table_area=None, fill=None, mtol=[2], scale=15,
                 invert=False, margins=(1.0, 0.5, 0.1), split_text=False,
                 gravity=None, debug=None):

        self.method = 'lattice'
        self.table_area = table_area
        self.fill = fill
        self.mtol = mtol
        self.scale = scale
        self.invert = invert
        self.char_margin, self.line_margin, self.word_margin = margins
        self.split_text = split_text
        self.gravity = gravity
        self.debug = debug

    def get_tables(self, pdfname):
        """get_tables

        Parameters
        ----------
        pdfname : string
            Path to single page pdf file.

        Returns
        -------
        page : dict
        """
        layout, dim = get_page_layout(pdfname, char_margin=self.char_margin,
            line_margin=self.line_margin, word_margin=self.word_margin)
        ltchar = get_text_objects(layout, LTType="char")
        lttextlh = get_text_objects(layout, LTType="lh")
        lttextlv = get_text_objects(layout, LTType="lv")
        width, height = dim
        bname, __ = os.path.splitext(pdfname)
        if not ltchar:
            logging.warning("{0}: PDF has no text. It may be an image.".format(
                os.path.basename(bname)))
            return None

        imagename = ''.join([bname, '.png'])
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
                    raise ValueError("Length of fill should be equal to table_area.")
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
            char_bbox = text_bbox(k, ltchar)
            lh_bbox = text_bbox(k, lttextlh)
            lv_bbox = text_bbox(k, lttextlv)
            table_data['text_p'] = 100 * (1 - (len(char_bbox) / len(ltchar)))
            table_rotation = get_rotation(char_bbox, lh_bbox, lv_bbox)
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
            table = _outline(table)

            if self.debug:
                self.debug_tables.append(table)

            rerror = []
            cerror = []
            for t in char_bbox:
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
                r_idx, c_idx = _reduce_index(table, table_rotation, r_idx, c_idx)
                table.cells[r_idx][c_idx].add_object(t)

            for i in range(len(table.cells)):
                for j in range(len(table.cells[i])):
                    t_bbox = table.cells[i][j].get_objects()
                    try:
                        cell_rotation = get_rotation(t_bbox)
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
                table = _fill_spanning(table, fill=self.fill[table_no])
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