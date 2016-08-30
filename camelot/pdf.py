import os
import shutil
import tempfile
import itertools
import multiprocessing as mp

import cv2
from PyPDF2 import PdfFileReader, PdfFileWriter


__all__ = ['Pdf']


def _parse_page_numbers(pagenos):
    """Converts list of page ranges to a list of page numbers.

    Parameters
    ----------
    pagenos : list
        List of dicts containing page ranges.

    Returns
    -------
    page_numbers : list
        List of page numbers.
    """
    page_numbers = []
    for p in pagenos:
        page_numbers.extend(range(p['start'], p['end'] + 1))
    page_numbers = sorted(set(page_numbers))
    return page_numbers


class Pdf:
    """Handles all pdf operations which include:

        1. Split pdf into single page pdfs using given page numbers
        2. Convert single page pdfs into images
        3. Extract text from single page pdfs

    Parameters
    ----------
    pdfname : string
        Path to pdf.

    pagenos : list
        List of dicts which specify pdf page ranges.
        (optional, default: [{'start': 1, 'end': 1}])

    char_margin : float
        Chars closer than char_margin are grouped together to form a
        word. (optional, default: 2.0)

    line_margin : float
        Lines closer than line_margin are grouped together to form a
        textbox. (optional, default: 0.5)

    word_margin : float
        Insert blank spaces between chars if distance between words
        is greater than word_margin. (optional, default: 0.1)
    """

    def __init__(self, extractor, pdfname, pagenos=[{'start': 1, 'end': 1}],
                 parallel=False, clean=False):

        self.extractor = extractor
        self.pdfname = pdfname
        if not self.pdfname.endswith('.pdf'):
            raise TypeError("Only PDF format is supported right now.")
        self.pagenos = _parse_page_numbers(pagenos)
        self.parallel = parallel
        self.cpu_count = mp.cpu_count()
        self.pool = mp.Pool(processes=self.cpu_count)
        self.clean = clean
        self.temp = tempfile.mkdtemp()

    def split(self):
        """Splits pdf into single page pdfs.
        """
        infile = PdfFileReader(open(self.pdfname, 'rb'), strict=False)
        for p in self.pagenos:
            page = infile.getPage(p - 1)
            outfile = PdfFileWriter()
            outfile.addPage(page)
            with open(os.path.join(self.temp, 'page-{0}.pdf'.format(p)), 'wb') as f:
                outfile.write(f)

    def remove_tempdir(self):
        shutil.rmtree(self.temp)

    def extract(self):
        """Extracts text objects, width, height from a pdf.
        """
        self.split()
        pages = [os.path.join(self.temp, 'page-{0}.pdf'.format(p))
                 for p in self.pagenos]
        if self.parallel:
            tables = self.pool.map(self.extractor.get_tables, pages)
            tables = {k: v for d in tables if d is not None for k, v in d.items()}
        else:
            tables = {}
            if self.extractor.debug:
                if self.extractor.method == 'stream':
                    self.debug = self.extractor.debug
                    self.debug_text = []
                elif self.extractor.method == 'lattice':
                    self.debug = self.extractor.debug
                    self.debug_images = []
                    self.debug_segments = []
                    self.debug_tables = []
            for p in pages:
                table = self.extractor.get_tables(p)
                if table is not None:
                    tables.update(table)
                if self.extractor.debug:
                    if self.extractor.method == 'stream':
                        self.debug_text.append(self.extractor.debug_text)
                    elif self.extractor.method == 'lattice':
                        self.debug_images.append(self.extractor.debug_images)
                        self.debug_segments.append(self.extractor.debug_segments)
                        self.debug_tables.append(self.extractor.debug_tables)
        if self.clean:
            self.remove_tempdir()
        return tables

    def debug_plot(self):
        """Plots all text objects and various pdf geometries so that
        user can choose number of columns, columns x-coordinates for
        Stream or tweak Lattice parameters (scale, jtol, mtol).
        """
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        if self.debug is True:
            try:
                for text in self.debug_text:
                    fig = plt.figure()
                    ax = fig.add_subplot(111, aspect='equal')
                    xs, ys = [], []
                    for t in text:
                        xs.extend([t[0], t[1]])
                        ys.extend([t[2], t[3]])
                        ax.add_patch(
                            patches.Rectangle(
                                (t[0], t[1]),
                                t[2] - t[0],
                                t[3] - t[1]
                            )
                        )
                    ax.set_xlim(min(xs) - 10, max(xs) + 10)
                    ax.set_ylim(min(ys) - 10, max(ys) + 10)
                    plt.show()
            except AttributeError:
                raise ValueError("This option only be used with Stream.")
        elif self.debug == 'contour':
            try:
                for img, table_bbox in self.debug_images:
                    for t in table_bbox.keys():
                        cv2.rectangle(img, (t[0], t[1]),
                                      (t[2], t[3]), (255, 0, 0), 3)
                    plt.imshow(img)
                    plt.show()
            except AttributeError:
                raise ValueError("This option only be used with Lattice.")
        elif self.debug == 'joint':
            try:
                for img, table_bbox in self.debug_images:
                    x_coord = []
                    y_coord = []
                    for k in table_bbox.keys():
                        for coord in table_bbox[k]:
                            x_coord.append(coord[0])
                            y_coord.append(coord[1])
                    max_x, max_y = max(x_coord), max(y_coord)
                    plt.plot(x_coord, y_coord, 'ro')
                    plt.axis([0, max_x + 100, max_y + 100, 0])
                    plt.imshow(img)
                    plt.show()
            except AttributeError:
                raise ValueError("This option only be used with Lattice.")
        elif self.debug == 'line':
            try:
                for v_s, h_s in self.debug_segments:
                    for v in v_s:
                        plt.plot([v[0], v[2]], [v[1], v[3]])
                    for h in h_s:
                        plt.plot([h[0], h[2]], [h[1], h[3]])
                    plt.show()
            except AttributeError:
                raise ValueError("This option only be used with Lattice.")
        elif self.debug == 'table':
            try:
                for tables in self.debug_tables:
                    for table in tables:
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
            except AttributeError:
                raise ValueError("This option only be used with Lattice.")
        else:
            raise UserWarning("This method can only be called after"
                " debug has been specified.")