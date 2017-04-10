import os
import copy
import subprocess

import pyocr
from PIL import Image

from .table import Table
from .imgproc import (adaptive_threshold, find_lines, find_table_contours,
                      find_table_joints)
from .utils import merge_close_values, encode_list


class OCR:
    """Uses optical character recognition to get text out of image based pdfs.
    Currently works only on pdfs with lines.

    Parameters
    ----------
    table_area : list
        List of strings of the form x1,y1,x2,y2 where
        (x1, y1) -> left-top and (x2, y2) -> right-bottom in PDFMiner's
        coordinate space, denoting table areas to analyze.
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

    dpi : int
        Dots per inch.
        (optional, default: 300)

    lang : string
        Language to be used for OCR.
        (optional, default: 'eng')

    scale : int
        Used to divide the height/width of a pdf to get a structuring
        element for image processing.
        (optional, default: 15)

    debug : string
        {'contour', 'line', 'joint', 'table'}
        Set to one of the above values to generate a matplotlib plot
        of detected contours, lines, joints and the table generated.
        (optional, default: None)
    """
    def __init__(self, table_area=None, mtol=[2], blocksize=15, threshold_constant=-2,
                 dpi=300, lang="eng", scale=15, debug=None):

        self.method = 'ocr'
        self.table_area = table_area
        self.mtol = mtol
        self.blocksize = blocksize
        self.threshold_constant = threshold_constant
        self.tool = pyocr.get_available_tools()[0] # fix this
        self.dpi = dpi
        self.lang = lang
        self.scale = scale
        self.debug = debug

    def get_tables(self, pdfname):
        if self.tool is None:
            return None
        bname, __ = os.path.splitext(pdfname)
        imagename = ''.join([bname, '.png'])

        gs_call = [
            "-q", "-sDEVICE=png16m", "-o", imagename, "-r{0}".format(self.dpi),
            pdfname
        ]
        if "ghostscript" in subprocess.check_output(["gs", "-version"]).lower():
            gs_call.insert(0, "gs")
        else:
            gs_call.insert(0, "gsc")
        subprocess.call(gs_call, stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT)

        img, threshold = adaptive_threshold(imagename, blocksize=self.blocksize,
            c=self.threshold_constant)
        vmask, v_segments = find_lines(threshold, direction='vertical',
            scale=self.scale)
        hmask, h_segments = find_lines(threshold, direction='horizontal',
            scale=self.scale)

        if self.table_area is not None:
            areas = []
            for area in self.table_area:
                x1, y1, x2, y2 = area.split(",")
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)
                areas.append((x1, y1, abs(x2 - x1), abs(y2 - y1)))
            table_bbox = find_table_joints(areas, vmask, hmask)
        else:
            contours = find_table_contours(vmask, hmask)
            table_bbox = find_table_joints(contours, vmask, hmask)

        if self.debug:
            self.debug_images = (img, table_bbox)
            self.debug_segments = (v_segments, h_segments)
            self.debug_tables = []

        if len(self.mtol) == 1 and self.mtol[0] == 2:
            mtolerance = copy.deepcopy(self.mtol) * len(table_bbox)
        else:
            mtolerance = copy.deepcopy(self.mtol)

        page = {}
        tables = {}
        table_no = 0
        for k in sorted(table_bbox.keys(), key=lambda x: x[1]):
            table_data = {}
            cols, rows = zip(*table_bbox[k])
            cols, rows = list(cols), list(rows)
            cols.extend([k[0], k[2]])
            rows.extend([k[1], k[3]])
            cols = merge_close_values(sorted(cols), mtol=mtolerance[table_no])
            rows = merge_close_values(sorted(rows, reverse=True), mtol=mtolerance[table_no])
            cols = [(cols[i], cols[i + 1])
                    for i in range(0, len(cols) - 1)]
            rows = [(rows[i], rows[i + 1])
                    for i in range(0, len(rows) - 1)]
            table = Table(cols, rows)
            if self.debug:
                self.debug_tables.append(table)
            table.image = img[k[3]:k[1],k[0]:k[2]]
            for i in range(len(table.cells)):
                for j in range(len(table.cells[i])):
                    x1 = int(table.cells[i][j].x1)
                    y1 = int(table.cells[i][j].y1)
                    x2 = int(table.cells[i][j].x2)
                    y2 = int(table.cells[i][j].y2)
                    table.cells[i][j].image = img[y1:y2,x1:x2]
                    text = self.tool.image_to_string(
                        Image.fromarray(table.cells[i][j].image),
                        lang=self.lang,
                        builder=pyocr.builders.TextBuilder()
                    )
                    table.cells[i][j].add_text(text)
            ar = table.get_list()
            ar.reverse()
            ar = encode_list(ar)
            table_data['data'] = ar
            tables['table-{0}'.format(table_no + 1)] = table_data
            table_no += 1
        page[os.path.basename(bname)] = tables

        if self.debug:
            return None

        return page