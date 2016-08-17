import os
import shutil
import tempfile
import itertools
import multiprocessing as mp

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
            raise TypeError("Only PDF format is supported.")
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
            tables = {k: v for d in tables for k, v in d.items()}
        else:
            tables = {}
            for p in pages:
                table = self.extractor.get_tables(p)
                tables.update(table)
        if self.clean:
            self.remove_tempdir()
        return tables

    def debug(self, debug):
        if debug is True:
            self.extractor.plot_text()
        elif debug in ['contour', 'joint', 'line', 'table']:
            self.extractor.plot_geometry(debug)
