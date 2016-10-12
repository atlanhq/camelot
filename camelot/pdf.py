import os
import shutil
import tempfile
import itertools
import multiprocessing as mp

import cv2
from PyPDF2 import PdfFileReader, PdfFileWriter


__all__ = ['Pdf']


def _parse_page_numbers(pagenos):
    """Converts list of dicts to list of ints.

    Parameters
    ----------
    pagenos : list
        List of dicts representing page ranges. A dict must have only
        two keys named 'start' and 'end' having int as their value.

    Returns
    -------
    page_numbers : list
        List of int page numbers.
    """
    page_numbers = []
    for p in pagenos:
        page_numbers.extend(range(p['start'], p['end'] + 1))
    page_numbers = sorted(set(page_numbers))
    return page_numbers


class Pdf:
    """Pdf manager.
    Handles all operations like temp directory creation, splitting file
    into single page pdfs, running extraction using multiple processes
    and removing the temp directory.

    Parameters
    ----------
    extractor : object
        camelot.stream.Stream or camelot.lattice.Lattice extractor
        object.

    pdfname : string
        Path to pdf file.

    pagenos : list
        List of dicts representing page ranges. A dict must have only
        two keys named 'start' and 'end' having int as their value.
        (optional, default: [{'start': 1, 'end': 1}])

    parallel : bool
        Whether or not to run using multiple processes.
        (optional, default: False)

    clean : bool
        Whether or not to remove the temp directory.
        (optional, default: False)
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
        """Splits file into single page pdfs.
        """
        infile = PdfFileReader(open(self.pdfname, 'rb'), strict=False)
        for p in self.pagenos:
            page = infile.getPage(p - 1)
            outfile = PdfFileWriter()
            outfile.addPage(page)
            with open(os.path.join(self.temp, 'page-{0}.pdf'.format(p)), 'wb') as f:
                outfile.write(f)

    def extract(self):
        """Runs table extraction by calling extractor.get_tables
        on all single page pdfs.
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

    def remove_tempdir(self):
        """Removes temporary directory that was created to save single
        page pdfs and their images.
        """
        shutil.rmtree(self.temp)

    def debug_plot(self):
        """Generates a matplotlib plot based on the selected extractor
        debug option.
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
                        for r in range(len(table.rows)):
                            for c in range(len(table.cols)):
                                if table.cells[r][c].left:
                                    plt.plot([table.cells[r][c].lb[0],
                                              table.cells[r][c].lt[0]],
                                             [table.cells[r][c].lb[1],
                                              table.cells[r][c].lt[1]])
                                if table.cells[r][c].right:
                                    plt.plot([table.cells[r][c].rb[0],
                                              table.cells[r][c].rt[0]],
                                             [table.cells[r][c].rb[1],
                                              table.cells[r][c].rt[1]])
                                if table.cells[r][c].top:
                                    plt.plot([table.cells[r][c].lt[0],
                                              table.cells[r][c].rt[0]],
                                             [table.cells[r][c].lt[1],
                                              table.cells[r][c].rt[1]])
                                if table.cells[r][c].bottom:
                                    plt.plot([table.cells[r][c].lb[0],
                                              table.cells[r][c].rb[0]],
                                             [table.cells[r][c].lb[1],
                                              table.cells[r][c].rb[1]])
                    plt.show()
            except AttributeError:
                raise ValueError("This option only be used with Lattice.")
        else:
            raise UserWarning("This method can only be called after"
                " debug has been specified.")