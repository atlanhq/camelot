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

from .core import Table, Geometry
from .image_processing import (adaptive_threshold, find_lines, find_table_contours,
                               find_table_joints)
from .utils import (scale_to_pdf, scale_to_image, segments_bbox, text_in_bbox,
                    merge_close_values, get_table_index, get_score, count_empty,
                    encode_list, get_text_objects, get_page_layout)


__all__ = ['Stream', 'Lattice']
logger = logging.getLogger('app_logger')


def _reduce_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)
copy_reg.pickle(types.MethodType, _reduce_method)


class Stream:
    """Stream looks for spaces between text elements to form a table.

    If you want to give columns, ytol or mtol for each table
    when specifying multiple table areas, make sure that their length
    is equal to the length of table_area. Mapping between them is based
    on index.

    If you don't want to specify columns for the some tables in a pdf
    page having multiple tables, pass them as empty strings.
    For example: ['', 'x1,x2,x3,x4', '']

    Parameters
    ----------
    table_area : list
        List of strings of the form x1,y1,x2,y2 where
        (x1, y1) -> left-top and (x2, y2) -> right-bottom in PDFMiner's
        coordinate space, denoting table areas to analyze.
        (optional, default: None)

    columns : list
        List of strings where each string is comma-separated values of
        x-coordinates in PDFMiner's coordinate space.
        (optional, default: None)

    ytol : list
        List of ints specifying the y-tolerance parameters.
        (optional, default: [2])

    mtol : list
        List of ints specifying the m-tolerance parameters.
        (optional, default: [0])

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

    debug : bool
        Set to True to generate a matplotlib plot of
        LTTextLineHorizontals in order to select table_area, columns.
        (optional, default: False)
    """
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
        """Returns bounding box for the text present on a page.

        Parameters
        ----------
        t_bbox : dict
            Dict with two keys 'horizontal' and 'vertical' with lists of
            LTTextLineHorizontals and LTTextLineVerticals respectively.

        Returns
        -------
        text_bbox : tuple
            Tuple of the form (x0, y0, x1, y1) in PDFMiner's coordinate
            space.
        """
        xmin = min([t.x0 for direction in t_bbox for t in t_bbox[direction]])
        ymin = min([t.y0 for direction in t_bbox for t in t_bbox[direction]])
        xmax = max([t.x1 for direction in t_bbox for t in t_bbox[direction]])
        ymax = max([t.y1 for direction in t_bbox for t in t_bbox[direction]])
        text_bbox = (xmin, ymin, xmax, ymax)
        return text_bbox

    @staticmethod
    def _group_rows(text, ytol=2):
        """Groups PDFMiner text objects into rows using their
        y-coordinates taking into account some tolerance ytol.

        Parameters
        ----------
        text : list
            List of PDFMiner text objects.

        ytol : int
            Tolerance parameter.
            (optional, default: 2)

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
        """Merges column boundaries if they overlap or lie within some
        tolerance mtol.

        Parameters
        ----------
        l : list
            List of column coordinate tuples.

        mtol : int
            TODO
            (optional, default: 0)

        Returns
        -------
        merged : list
            List of merged column coordinate tuples.
        """
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
            List of continuous row coordinate tuples.
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
    def _add_columns(cols, text, ytol):
        """Adds columns to existing list by taking into account
        the text that lies outside the current column coordinates.

        Parameters
        ----------
        cols : list
            List of column coordinate tuples.

        text : list
            List of PDFMiner text objects.

        ytol : int
            Tolerance parameter.

        Returns
        -------
        cols : list
            Updated list of column coordinate tuples.
        """
        if text:
            text = Stream._group_rows(text, ytol=ytol)
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
            List of column coordinate tuples.

        text_x_min : int

        text_y_max : int

        Returns
        -------
        cols : list
            Updated list of column coordinate tuples.
        """
        cols = sorted(cols)
        cols = [(cols[i][0] + cols[i - 1][1]) / 2 for i in range(1, len(cols))]
        cols.insert(0, text_x_min)
        cols.append(text_x_max)
        cols = [(cols[i], cols[i + 1])
                for i in range(0, len(cols) - 1)]
        return cols

    def extract_tables(self, pdfname):
        """Expects a single page pdf as input with rotation corrected.

        Parameters
        ---------
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
            return [None], [g]

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

        page = {}
        tables = {}
        # sort tables based on y-coord
        for table_no, k in enumerate(sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True)):
            # select elements which lie within table_bbox
            table_data = {}
            t_bbox = {}
            t_bbox['horizontal'] = text_in_bbox(k, lttextlh)
            t_bbox['vertical'] = text_in_bbox(k, lttextlv)
            char_bbox = text_in_bbox(k, ltchar)
            table_data['text_p'] = 100 * (1 - (len(char_bbox) / len(ltchar)))
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
            assignment_errors = []
            table_data['split_text'] = []
            table_data['superscript'] = []
            for direction in t_bbox:
                for t in t_bbox[direction]:
                    indices, error = get_table_index(
                        table, t, direction, split_text=self.split_text,
                        flag_size=self.flag_size)
                    assignment_errors.append(error)
                    if len(indices) > 1:
                        table_data['split_text'].append(indices)
                    for r_idx, c_idx, text in indices:
                        if all(s in text for s in ['<s>', '</s>']):
                            table_data['superscript'].append((r_idx, c_idx, text))
                        table.cells[r_idx][c_idx].add_text(text)
            if guess:
                score = get_score([[66, assignment_errors], [34, [len_non_mode / len(elements)]]])
            else:
                score = get_score([[100, assignment_errors]])

            table_data['score'] = score
            ar = table.get_list()
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

        return page


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

    mtol : list
        List of ints specifying m-tolerance parameters.
        (optional, default: [2])

    jtol : list
        List of ints specifying j-tolerance parameters.
        (optional, default: [2])

    blocksize : int
        Size of a pixel neighborhood that is used to calculate a
        threshold value for the pixel: 3, 5, 7, and so on.
        (optional, default: 15)

    threshold_constant : float
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
        (optional, default: 0)

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
            g.images = [(img, table_bbox)]

        table_bbox, v_segments, h_segments = scale_to_pdf(table_bbox, v_segments,
            h_segments, factors_pdf)

        if self.debug:
            g.segments = [(v_segments, h_segments)]
            _tables = []

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

            table = Table(cols, rows)
            # set table edges to True using ver+hor lines
            table = table.set_edges(v_s, h_s, jtol=jtolerance[table_no])
            # set spanning cells to True
            table = table.set_spanning()
            # set table border edges to True
            table = table.set_border_edges()

            if self.debug:
                _tables.append(table)

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
                        indices = self._reduce_index(table, indices, shift_text=self.shift_text)
                        if len(indices) > 1:
                            table_data['split_text'].append(indices)
                        for r_idx, c_idx, text in indices:
                            if all(s in text for s in ['<s>', '</s>']):
                                table_data['superscript'].append((r_idx, c_idx, text))
                            table.cells[r_idx][c_idx].add_text(text)
            score = get_score([[100, assignment_errors]])
            table_data['score'] = score

            if self.fill is not None:
                table = self._fill_spanning(table, fill=self.fill)
            ar = table.get_list()
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
            g.tables = _tables
            return [None], [g]

        return page