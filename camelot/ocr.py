import os
import subprocess

from PIL import Image
import pyocr

from .table import Table
from .imgproc import (adaptive_threshold, find_lines, find_table_contours,
                      find_table_joints)
from .utils import merge_close_values, encode_list


class OCR:
    """OCR
    """
    def __init__(self, dpi=300, lang="eng", scale=15, mtol=2, debug=False):
        self.tool = pyocr.get_available_tools()[0]
        self.dpi = dpi
        self.lang = lang
        self.scale = scale
        self.mtol = mtol
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
        subprocess.call(gs_call)

        img, threshold = adaptive_threshold(imagename)
        vmask, v_segments = find_lines(threshold, direction='vertical',
            scale=self.scale)
        hmask, h_segments = find_lines(threshold, direction='horizontal',
            scale=self.scale)
        contours = find_table_contours(vmask, hmask)
        table_bbox = find_table_joints(contours, vmask, hmask)

        page = {}
        tables = {}
        table_no = 0
        for k in sorted(table_bbox.keys(), key=lambda x: x[1]):
            table_data = {}
            cols, rows = zip(*table_bbox[k])
            cols, rows = list(cols), list(rows)
            cols.extend([k[0], k[2]])
            rows.extend([k[1], k[3]])
            cols = merge_close_values(sorted(cols), mtol=self.mtol)
            rows = merge_close_values(sorted(rows, reverse=True), mtol=self.mtol)
            cols = [(cols[i], cols[i + 1])
                    for i in range(0, len(cols) - 1)]
            rows = [(rows[i], rows[i + 1])
                    for i in range(0, len(rows) - 1)]
            table = Table(cols, rows)
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

        return page