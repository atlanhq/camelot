"""
usage: python print_text.py file.pdf

prints horizontal and vertical text lines present in a pdf file.
"""

import sys
import time
from pprint import pprint

from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.layout import (LAParams, LTChar, LTAnno, LTTextBoxHorizontal,
                             LTTextLineHorizontal, LTTextLineVertical, LTLine)


def timeit(func):
    def timed(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print 'Function: %r took: %2.4f seconds' % (func.__name__, end - start)
        return result
    return timed


def extract_text_objects(layout, LTObject, t=None):
    if t is None:
        t = []
    try:
        for obj in layout._objs:
            if isinstance(obj, LTObject):
                t.append(obj)
            else:
                t += extract_text_objects(obj, LTObject)
    except AttributeError:
        pass
    return t


@timeit
def main():
    with open(sys.argv[1], 'rb') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        # 2.0, 0.5, 0.1
        kwargs = {
            'char_margin': 1.0,
            'line_margin': 0.5,
            'word_margin': 0.1,
            'detect_vertical': True
        }
        laparams = LAParams(**kwargs)
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            lh = extract_text_objects(layout, LTTextLineHorizontal)
            lv = extract_text_objects(layout, LTTextLineVertical)
            print "number of horizontal text lines -> {0}".format(len(lh))
            print "horizontal text lines ->"
            pprint([t.get_text() for t in lh])
            print "number of vertical text lines -> {0}".format(len(lv))
            print "vertical text lines ->"
            pprint([t.get_text() for t in lv])


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()