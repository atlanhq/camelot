from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal


def parse_text_stream(layout, t=None):
    """Recursively parse pdf layout to get a list of
    LTTextHorizontal objects.

    Parameters
    ----------
    layout : object

    t : list

    Returns
    -------
    t : list
    """
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTTextLineHorizontal):
                t.append(obj)
            else:
                t += parse_text_stream(obj)
    except AttributeError:
        pass
    return t


def parse_text_lattice(layout, t=None):
    """Recursively parse pdf layout to get a list of
    LTChar objects.
    
    Parameters
    ----------
    layout : object

    t : list

    Returns
    -------
    t : list
    """
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTChar):
                t.append(obj)
            else:
                t += parse_text_lattice(obj)
    except AttributeError:
        pass
    return t


def get_pdf_info(pdfname, method=None, char_margin=2.0, line_margin=0.5,
                 word_margin=0.1):
    """Get list of text objects along with pdf width and height.

    Parameters
    ----------
    pdfname : string

    method : string

    char_margin : float

    line_margin : float

    word_margin : float

    Returns
    -------
    text : list

    pdf_x : int

    pdf_y : int
    """
    if not method:
        return None
    with open(pdfname, 'r') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        laparams = LAParams(char_margin=char_margin,
                            line_margin=line_margin,
                            word_margin=word_margin)
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            if method == 'stream':
                text = parse_text_stream(layout)
            elif method == 'lattice':
                text = parse_text_lattice(layout)
            pdf_x, pdf_y = layout.bbox[2], layout.bbox[3]
    return text, pdf_x, pdf_y
