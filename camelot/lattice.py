from __future__ import print_function
import os

import cv2
import numpy as np

from .table import Table
from .utils import (transform, elements_bbox, detect_vertical, merge_close_values,
                    get_row_index, get_column_index, reduce_index, outline,
                    fill_spanning, remove_empty, encode_list)


__all__ = ['Lattice']


def _morph_transform(imagename, scale=15, invert=False):
    """Morphological Transformation

    Applies a series of morphological operations on the image
    to find table contours and line segments.
    http://answers.opencv.org/question/63847/how-to-extract-tables-from-an-image/

    Empirical result for adaptiveThreshold's blockSize=5 and C=-0.2
    taken from http://pequan.lip6.fr/~bereziat/pima/2012/seuillage/sezgin04.pdf

    Parameters
    ----------
    imagename : Path to image.

    scale : int
        Scaling factor. Large scaling factor leads to smaller lines
        being detected. (optional, default: 15)

    invert : bool
        Invert pdf image to make sure that lines are in foreground.
        (optional, default: False)

    Returns
    -------
    img : ndarray

    tables : dict
        Dictionary with table bounding box as key and list of
        joints found in the table as value.

    v_segments : list
        List of vertical line segments found in the image.

    h_segments : list
        List of horizontal line segments found in the image.
    """
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

    vertical = threshold
    horizontal = threshold

    verticalsize = vertical.shape[0] / scale
    horizontalsize = horizontal.shape[1] / scale

    ver = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    hor = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalsize, 1))

    vertical = cv2.erode(vertical, ver, (-1, -1))
    vertical = cv2.dilate(vertical, ver, (-1, -1))

    horizontal = cv2.erode(horizontal, hor, (-1, -1))
    horizontal = cv2.dilate(horizontal, hor, (-1, -1))

    mask = vertical + horizontal
    joints = np.bitwise_and(vertical, horizontal)
    __, contours, __ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    tables = {}
    for c in contours:
        c_poly = cv2.approxPolyDP(c, 3, True)
        x, y, w, h = cv2.boundingRect(c_poly)
        roi = joints[y : y + h, x : x + w]
        __, jc, __ = cv2.findContours(
            roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if len(jc) <= 4:  # remove contours with less than <=4 joints
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2 * jx + jw) / 2, y + (2 * jy + jh) / 2
            joint_coords.append((c1, c2))
        tables[(x, y + h, x + w, y)] = joint_coords

    v_segments, h_segments = [], []
    _, vcontours, _ = cv2.findContours(
        vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for vc in vcontours:
        x, y, w, h = cv2.boundingRect(vc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        v_segments.append(((x1 + x2) / 2, y2, (x1 + x2) / 2, y1))

    _, hcontours, _ = cv2.findContours(
        horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for hc in hcontours:
        x, y, w, h = cv2.boundingRect(hc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        h_segments.append((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2))

    return img, tables, v_segments, h_segments


class Lattice:
    """Lattice algorithm

    Makes use of pdf geometry by processing its image, to make a table
    and fills text objects in table cells.

    Parameters
    ----------
    pdfobject : camelot.pdf.Pdf

    fill : None, 'h', 'v', 'hv'
        Fill data in horizontal and/or vertical spanning
        cells. (optional, default: None)

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

    debug : 'contour', 'line', 'joint', 'table'
        Debug by visualizing pdf geometry.
        (optional, default: None)

    Attributes
    ----------
    tables : dict
        Dictionary with page number as key and list of tables on that
        page as value.
    """

    def __init__(self, pdfobject, fill=None, scale=15, jtol=2, mtol=2,
                 invert=False, debug=None, verbose=False):

        self.pdfobject = pdfobject
        self.fill = fill
        self.scale = scale
        self.jtol = jtol
        self.mtol = mtol
        self.invert = invert
        self.debug = debug
        self.verbose = verbose
        self.tables = {}
        if self.debug is not None:
            self.debug_images = {}
            self.debug_segments = {}
            self.debug_tables = {}

    def get_tables(self):
        """Returns all tables found in given pdf.

        Returns
        -------
        tables : dict
            Dictionary with page number as key and list of tables on that
            page as value.
        """
        vprint = print if self.verbose else lambda *a, **k: None
        self.pdfobject.split()
        self.pdfobject.convert()
        for page in self.pdfobject.extract():
            p, text, __, width, height = page
            pkey = 'pg-{0}'.format(p)
            imagename = os.path.join(
                self.pdfobject.temp, '{}.png'.format(pkey))
            pdf_x = width
            pdf_y = height
            img, table_bbox, v_segments, h_segments = _morph_transform(
                imagename, scale=self.scale, invert=self.invert)
            img_x = img.shape[1]
            img_y = img.shape[0]
            scaling_factor_x = pdf_x / float(img_x)
            scaling_factor_y = pdf_y / float(img_y)

            if self.debug is not None:
                self.debug_images[pkey] = (img, table_bbox)

            factors = (scaling_factor_x, scaling_factor_y, img_y)
            table_bbox, v_segments, h_segments = transform(table_bbox, v_segments,
                                                           h_segments, factors)

            if self.debug is not None:
                self.debug_segments[pkey] = (v_segments, h_segments)

            if self.debug is not None:
                debug_page_tables = []
            page_tables = []
            # sort tables based on y-coord
            for k in sorted(table_bbox.keys(), key=lambda x: x[1], reverse=True):
                # select edges which lie within table_bbox
                text_bbox, v_s, h_s = elements_bbox(k, text, v_segments,
                                                    h_segments)
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
                # set spanning cells to True
                table = table.set_spanning()
                # set table border edges to True
                table = outline(table)

                if self.debug is not None:
                    debug_page_tables.append(table)

                # fill text after sorting it
                if rotated == '':
                    text_bbox.sort(key=lambda x: (-x.y0, x.x0))
                elif rotated == 'left':
                    text_bbox.sort(key=lambda x: (x.x0, x.y0))
                elif rotated == 'right':
                    text_bbox.sort(key=lambda x: (-x.x0, -x.y0))
                for t in text_bbox:
                    r_idx = get_row_index(t, rows)
                    c_idx = get_column_index(t, cols)
                    if None in [r_idx, c_idx]:
                        # couldn't assign LTChar to any cell
                        pass
                    else:
                        r_idx, c_idx = reduce_index(
                            table, rotated, r_idx, c_idx)
                        table.cells[r_idx][c_idx].add_text(
                            t.get_text().strip('\n'))

                if self.fill is not None:
                    table = fill_spanning(table, fill=self.fill)
                ar = table.get_list()
                if rotated == 'left':
                    ar = zip(*ar[::-1])
                elif rotated == 'right':
                    ar = zip(*ar[::1])
                    ar.reverse()
                ar = remove_empty(ar)
                ar = [list(o) for o in ar]
                page_tables.append(encode_list(ar))
            vprint(pkey)
            self.tables[pkey] = page_tables

        if self.debug is not None:
            self.debug_tables[pkey] = debug_page_tables

        if self.pdfobject.clean:
            self.pdfobject.remove_tempdir()

        if self.debug is not None:
            return None

        return self.tables

    def plot_geometry(self, geometry):
        """Plots various pdf geometries that are detected so user can choose
        tweak scale, jtol, mtol parameters.
        """
        import matplotlib.pyplot as plt

        if geometry == 'contour':
            for pkey in self.debug_images.keys():
                img, table_bbox = self.debug_images[pkey]
                for t in table_bbox.keys():
                    cv2.rectangle(img, (t[0], t[1]),
                                  (t[2], t[3]), (255, 0, 0), 3)
                plt.imshow(img)
                plt.show()
        elif geometry == 'joint':
            x_coord = []
            y_coord = []
            for pkey in self.debug_images.keys():
                img, table_bbox = self.debug_images[pkey]
                for k in table_bbox.keys():
                    for coord in table_bbox[k]:
                        x_coord.append(coord[0])
                        y_coord.append(coord[1])
                max_x, max_y = max(x_coord), max(y_coord)
                plt.plot(x_coord, y_coord, 'ro')
                plt.axis([0, max_x + 100, max_y + 100, 0])
                plt.imshow(img)
                plt.show()
        elif geometry == 'line':
            for pkey in self.debug_segments.keys():
                v_s, h_s = self.debug_segments[pkey]
                for v in v_s:
                    plt.plot([v[0], v[2]], [v[1], v[3]])
                for h in h_s:
                    plt.plot([h[0], h[2]], [h[1], h[3]])
                plt.show()
        elif geometry == 'table':
            for pkey in self.debug_tables.keys():
                for table in self.debug_tables[pkey]:
                    for i in range(len(table.cells)):
                        for j in range(len(table.cells[i])):
                            if table.cells[i][j].left:
                                plt.plot([table.cells[i][j].lb[0],
                                          table.cells[i][j].lt[0]],
                                         [table.cells[i][j].lb[1],
                                          table.cells[i][j].lt[1]])
                            if table.cells[i][j].right:
                                plt.plot([table.cells[i][j].rb[0],
                                          table.cells[i][j].rt[0]],
                                         [table.cells[i][j].rb[1],
                                          table.cells[i][j].rt[1]])
                            if table.cells[i][j].top:
                                plt.plot([table.cells[i][j].lt[0],
                                          table.cells[i][j].rt[0]],
                                         [table.cells[i][j].lt[1],
                                          table.cells[i][j].rt[1]])
                            if table.cells[i][j].bottom:
                                plt.plot([table.cells[i][j].lb[0],
                                          table.cells[i][j].rb[0]],
                                         [table.cells[i][j].lb[1],
                                          table.cells[i][j].rb[1]])
                plt.show()