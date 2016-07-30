import os
import shutil
import tempfile

from PyPDF2 import PdfFileReader, PdfFileWriter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal
from wand.image import Image


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


def _extract_text_objects(layout, LTObject, t=None):
    """Recursively parses pdf layout to get a list of
    text objects.

    Parameters
    ----------
    layout : object
        Layout object.

    LTObject : object
        Text object, either LTChar or LTTextLineHorizontal.

    t : list (optional, default: None)

    Returns
    -------
    t : list
        List of text objects.
    """
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTObject):
                t.append(obj)
            else:
                t += _extract_text_objects(obj, LTObject)
    except AttributeError:
        pass
    return t


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

    def __init__(self, pdfname, pagenos=[{'start': 1, 'end': 1}],
                 char_margin=2.0, line_margin=0.5, word_margin=0.1,
                 clean=False):

        self.pdfname = pdfname
        self.pagenos = _parse_page_numbers(pagenos)
        self.char_margin = char_margin
        self.line_margin = line_margin
        self.word_margin = word_margin
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
            with open(os.path.join(self.temp, 'pg-{0}.pdf'.format(p)), 'wb') as f:
                outfile.write(f)

    def extract(self):
        """Extracts text objects, width, height from a pdf.
        """
        for p in self.pagenos:
            pkey = 'pg-{0}'.format(p)
            pname = os.path.join(self.temp, '{}.pdf'.format(pkey))
            with open(pname, 'r') as f:
                parser = PDFParser(f)
                document = PDFDocument(parser)
                if not document.is_extractable:
                    raise PDFTextExtractionNotAllowed
                laparams = LAParams(char_margin=self.char_margin,
                                    line_margin=self.line_margin,
                                    word_margin=self.word_margin)
                rsrcmgr = PDFResourceManager()
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                for page in PDFPage.create_pages(document):
                    interpreter.process_page(page)
                    layout = device.get_result()
                    lattice_objects = _extract_text_objects(layout, LTChar)
                    stream_objects = _extract_text_objects(
                        layout, LTTextLineHorizontal)
                    width = layout.bbox[2]
                    height = layout.bbox[3]
                yield p, lattice_objects, stream_objects, width, height

    def convert(self):
        """Converts single page pdfs to images.
        """
        for p in self.pagenos:
            pdfname = os.path.join(self.temp, 'pg-{0}.pdf'.format(p))
            imagename = os.path.join(self.temp, 'pg-{0}.png'.format(p))
            with Image(filename=pdfname, depth=8, resolution=300) as png:
                png.save(filename=imagename)

    def remove_tempdir(self):
        shutil.rmtree(self.temp)
