from __future__ import division
import os
import sys
import copy
import types
import logging
import copy_reg
import subprocess

from .imgproc import (adaptive_threshold, find_lines, find_table_contours,
                      find_table_joints)
from .table import Table
from .utils import (scale_to_pdf, scale_to_image, segments_bbox, text_in_bbox,
                    merge_close_values, get_table_index, get_score, count_empty,
                    encode_list, get_text_objects, get_page_layout, remove_empty)


__all__ = ['Lattice']

logger = logging.getLogger("app_logger")


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


def _reduce_index(t, idx, shift_text):
    """Reduces index of a text object if it lies within a spanning
    cell.

    Parameters
    ----------
    table : object
        camelot.table.Table

    idx : list
        List of tuples of the form (r_idx, c_idx, text).

    shift_text : list
        {'l', 'r', 't', 'b'}
        Select one or more from above and pass them as a list to
        specify where the text in a spanning cell should flow.

    Returns
    -------
    indices : list
        List of tuples of the form (idx, text) where idx is the reduced
        index of row/column and text is the an lttextline substring.
    """
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
    """Fills spanning cells.

    Parameters
    ----------
    t : object
        camelot.table.Table

    fill : list
        {'h', 'v'}
        Specify to fill spanning cells in horizontal or vertical
        direction.
        (optional, default: None)

    Returns
    -------
    t : object
        camelot.table.Table
    """
    for f in fill:
        if f == "h":
            for i in range(len(t.cells)):
                for j in range(len(t.cells[i])):
                    if t.cells[i][j].get_text().strip() == '':
                        if t.cells[i][j].spanning_h:
                            t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
        elif f == "v":
            for i in range(len(t.cells)):
                for j in range(len(t.cells[i])):
                    if t.cells[i][j].get_text().strip() == '':
                        if t.cells[i][j].spanning_v:
                            t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    return t


class Lattice:
    """Lattice looks for lines in the pdf to form a table.

    If you want to give fill and mtol for each table when specifying
    multiple table areas, make sure that the length of fill and mtol
    is equal to the length of table_area. Mapping between them is based
    on index.

    Parameters
    ----------
    table_area : list
        List of strings of the form x1,y1,x2,y2 where
        (x1, y1) -> left-top and (x2, y2) -> right-bottom in PDFMiner's
        coordinate space, denoting table areas to analyze.
        (optional, default: None)

    fill : list
        List of strings specifying directions to fill spanning cells.
        {'h', 'v'} to fill spanning cells in horizontal or vertical
        direction.
        (optional, default: None)

    headers : list
        List of strings where each string is a csv header for a table.
        (optional, default: None)

    mtol : list
        List of ints specifying m-tolerance parameters.
        (optional, default: [2])

    blocksize: int
        Size of a pixel neighborhood that is used to calculate a
        threshold value for the pixel: 3, 5, 7, and so on.
        (optional, default: 15)

    threshold_constant: float
        Constant subtracted from the mean or weighted mean
        (see the details below). Normally, it is positive but may be
        zero or negative as well.
        (optional, default: -2)

    scale : int
        Used to divide the height/width of a pdf to get a structuring
        element for image processing.
        (optional, default: 15)

    iterations : int
        Number of iterations for dilation.
        (optional, default: 2)

    invert : bool
        Whether or not to invert the image. Useful when pdfs have
        tables with lines in background.
        (optional, default: False)

    margins : tuple
        PDFMiner margins. (char_margin, line_margin, word_margin)
        (optional, default: (1.0, 0.5, 0.1))

    split_text : bool
        Whether or not to split a text line if it spans across
        different cells.
        (optional, default: False)

    flag_size : bool
        Whether or not to highlight a substring using <s></s>
        if its size is different from rest of the string, useful for
        super and subscripts.
        (optional, default: True)

    shift_text : list
        {'l', 'r', 't', 'b'}
        Select one or more from above and pass them as a list to
        specify where the text in a spanning cell should flow.
        (optional, default: ['l', 't'])

    debug : string
        {'contour', 'line', 'joint', 'table'}
        Set to one of the above values to generate a matplotlib plot
        of detected contours, lines, joints and the table generated.
        (optional, default: None)
    """
    def __init__(self, table_area=None, fill=None, headers=None, mtol=[2],
                 blocksize=15, threshold_constant=-2, scale=15, iterations=2,
                 invert=False, margins=(1.0, 0.5, 0.1), split_text=False,
                 flag_size=True, shift_text=['l', 't'], debug=None):

        self.method = 'lattice'
        self.table_area = table_area
        self.fill = fill
        self.headers = headers
        self.mtol = mtol
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

    def get_tables(self, pdfname):
        """Expects a single page pdf as input with rotation corrected.

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
        lttextlh = get_text_objects(layout, ltype="lh")
        lttextlv = get_text_objects(layout, ltype="lv")
        ltchar = get_text_objects(layout, ltype="char")
        width, height = dim
        bname, __ = os.path.splitext(pdfname)
        logger.info('Parsing tables from {0}.'.format(os.path.basename(bname)))
        if not ltchar:
            logger.warning("{0}: PDF has no text. It may be an image.".format(
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
            if self.fill is not None:
                if len(self.table_area) != len(self.fill):
                    raise ValueError("Length of fill should be equal to table_area.")
            if self.headers is not None:
                if len(self.table_area) != len(self.headers):
                    raise ValueError("Length of headers should be equal to table_area.")

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

        if self.debug:
            self.debug_images = (img, table_bbox)

        table_bbox, v_segments, h_segments = scale_to_pdf(table_bbox, v_segments,
            h_segments, factors_pdf)

        if self.debug:
            self.debug_segments = (v_segments, h_segments)
            self.debug_tables = []

        page = {}
        tables = {}
        # sort tables based on y-coord
        for table_no, k in enumerate(sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True)):
            # select elements which lie within table_bbox
            table_data = {}
            t_bbox = {}
            v_s, h_s = segments_bbox(k, v_segments, h_segments)
            t_bbox['horizontal'] = text_in_bbox(k, lttextlh)
            t_bbox['vertical'] = text_in_bbox(k, lttextlv)
            char_bbox = text_in_bbox(k, ltchar)
            table_data['text_p'] = 100 * (1 - (len(char_bbox) / len(ltchar)))
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

            if self.headers is not None and self.headers[table_no] != [""]:
                self.headers[table_no] = self.headers[table_no].split(',')
                if len(self.headers[table_no]) != len(cols):
                    logger.warning("Length of header ({0}) specified for table is not"
                                   " equal to the number of columns ({1}) detected.".format(
                                   len(self.headers[table_no]), len(cols)))
                while len(self.headers[table_no]) != len(cols):
                    self.headers[table_no].append('')

            table = Table(cols, rows)
            # set table edges to True using ver+hor lines
            table = table.set_edges(v_s, h_s)
            nouse = table.nocont_ / (len(v_s) + len(h_s))
            table_data['line_p'] = 100 * (1 - nouse)
            # set spanning cells to True
            table = table.set_spanning()
            # set table border edges to True
            table = table.set_border_edges()

            if self.debug:
                self.debug_tables.append(table)

            assignment_errors = []
            table_data['split_text'] = []
            table_data['superscript'] = []
            for direction in ['vertical', 'horizontal']:
                for t in t_bbox[direction]:
                    indices, error = get_table_index(
                        table, t, direction, split_text=self.split_text,
                        flag_size=self.flag_size)
                    if indices[:2] != (-1, -1):
                        assignment_errors.append(error)
                        indices = _reduce_index(table, indices, shift_text=self.shift_text)
                        if len(indices) > 1:
                            table_data['split_text'].append(indices)
                        for r_idx, c_idx, text in indices:
                            if all(s in text for s in ['<s>', '</s>']):
                                table_data['superscript'].append((r_idx, c_idx, text))
                            table.cells[r_idx][c_idx].add_text(text)
            score = get_score([[100, assignment_errors]])
            table_data['score'] = score

            if self.fill is not None:
                table = _fill_spanning(table, fill=self.fill[table_no])
            ar = table.get_list()
            ar = remove_empty(ar)
            if self.headers is not None and self.headers[table_no] != ['']:
                ar.insert(0, self.headers[table_no])
            ar = encode_list(ar)
            table_data['data'] = ar
            empty_p, r_nempty_cells, c_nempty_cells = count_empty(ar)
            table_data['empty_p'] = empty_p
            table_data['r_nempty_cells'] = r_nempty_cells
            table_data['c_nempty_cells'] = c_nempty_cells
            table_data['nrows'] = len(ar)
            table_data['ncols'] = len(ar[0])
            tables['table-{0}'.format(table_no + 1)] = table_data
        page[os.path.basename(bname)] = tables

        if self.debug:
            return None

        return page