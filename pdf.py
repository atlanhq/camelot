from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal


def parse_text_basic(layout, t=None):
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if type(obj) is LTTextLineHorizontal:
                t.append(obj)
            else:
                t += parse_text_basic(obj)
    except AttributeError:
        pass
    return t


def parse_text_spreadsheet(layout, t=None):
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if type(obj) is LTChar:
                t.append(obj)
            else:
                t += parse_text_spreadsheet(obj)
    except AttributeError:
        pass
    return t


def get_pdf_info(pdfname, method, char_margin, line_margin, word_margin):
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
            if method == 'basic':
                text = parse_text_basic(layout)
            elif method == 'spreadsheet':
                text = parse_text_spreadsheet(layout)
            pdf_x, pdf_y = layout.bbox[2], layout.bbox[3]
    return text, pdf_x, pdf_y
