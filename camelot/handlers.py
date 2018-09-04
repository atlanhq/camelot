import os
import tempfile

from PyPDF2 import PdfFileReader, PdfFileWriter

from .parsers import Stream, Lattice
from .utils import get_page_layout, get_text_objects, get_rotation


class PDFHandler(object):
    def __init__(self, filename, pages='1'):
        self.filename = filename
        if not self.filename.endswith('.pdf'):
            raise TypeError("File format not supported.")
        self.pages = self.__get_pages(self.filename, pages)
        self.temp = tempfile.mkdtemp()

    def __get_pages(self, filename, pages):
        # refactor
        page_numbers = []
        if pages == '1':
            page_numbers.append({'start': 1, 'end': 1})
        else:
            infile = PdfFileReader(open(filename, 'rb'), strict=False)
            if pages == 'all':
                page_numbers.append({'start': 1, 'end': infile.getNumPages()})
            else:
                for r in pages.split(','):
                    if '-' in r:
                        a, b = r.split('-')
                        if b == 'end':
                            b = infile.getNumPages()
                        page_numbers.append({'start': int(a), 'end': int(b)})
                    else:
                        page_numbers.append({'start': int(r), 'end': int(r)})
        P = []
        for p in page_numbers:
            P.extend(range(p['start'], p['end'] + 1))
        return sorted(set(P))

    def __save_page(self, filename, page, temp):
        # refactor
        with open(filename, 'rb') as fileobj:
            infile = PdfFileReader(fileobj, strict=False)
            fpath = os.path.join(temp, 'page-{0}.pdf'.format(page))
            fname, fext = os.path.splitext(fpath)
            p = infile.getPage(page - 1)
            outfile = PdfFileWriter()
            outfile.addPage(p)
            with open(fpath, 'wb') as f:
                outfile.write(f)
            layout, dim = get_page_layout(fpath)
            # fix rotated pdf
            lttextlh = get_text_objects(layout, ltype="lh")
            lttextlv = get_text_objects(layout, ltype="lv")
            ltchar = get_text_objects(layout, ltype="char")
            rotation = get_rotation(lttextlh, lttextlv, ltchar)
            if rotation != '':
                fpath_new = ''.join([fname.replace('page', 'p'), '_rotated', fext])
                os.rename(fpath, fpath_new)
                infile = PdfFileReader(open(fpath_new, 'rb'), strict=False)
                outfile = PdfFileWriter()
                p = infile.getPage(0)
                if rotation == 'left':
                    p.rotateClockwise(90)
                elif rotation == 'right':
                    p.rotateCounterClockwise(90)
                outfile.addPage(p)
                with open(fpath, 'wb') as f:
                    outfile.write(f)

    def parse(self, mesh=False, **kwargs):
        for p in self.pages:
            self.__save_page(self.filename, p, self.temp)
        pages = [os.path.join(self.temp, 'page-{0}.pdf'.format(p))
                 for p in self.pages]
        tables = {}
        parser = Stream(**kwargs) if not mesh else Lattice(**kwargs)
        for p in pages:
            table = parser.get_tables(p)
            if table is not None:
                tables.update(table)
        return tables