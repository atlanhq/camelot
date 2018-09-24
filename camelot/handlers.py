# -*- coding: utf-8 -*-

import os

from PyPDF2 import PdfFileReader, PdfFileWriter

from .core import TableList
from .parsers import Stream, Lattice
from .utils import (TemporaryDirectory, get_page_layout, get_text_objects,
                    get_rotation)


class PDFHandler(object):
    """Handles all operations like temp directory creation, splitting
    file into single page PDFs, parsing each PDF and then removing the
    temp directory.

    Parameters
    ----------
    filename : str
        Path to PDF file.
    pages : str, optional (default: '1')
        Comma-separated page numbers.
        Example: 1,3,4 or 1,4-end.

    """
    def __init__(self, filename, pages='1'):
        self.filename = filename
        if not self.filename.endswith('.pdf'):
            raise TypeError("File format not supported.")
        self.pages = self._get_pages(self.filename, pages)

    def _get_pages(self, filename, pages):
        """Converts pages string to list of ints.

        Parameters
        ----------
        filename : str
            Path to PDF file.
        pages : str, optional (default: '1')
            Comma-separated page numbers.
            Example: 1,3,4 or 1,4-end.

        Returns
        -------
        P : list
            List of int page numbers.

        """
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

    def _save_page(self, filename, page, temp):
        """Saves specified page from PDF into a temporary directory.

        Parameters
        ----------
        filename : str
            Path to PDF file.
        page : int
            Page number.
        temp : str
            Tmp directory.

        """
        with open(filename, 'rb') as fileobj:
            infile = PdfFileReader(fileobj, strict=False)
            if infile.isEncrypted:
                infile.decrypt('')
            fpath = os.path.join(temp, 'page-{0}.pdf'.format(page))
            froot, fext = os.path.splitext(fpath)
            p = infile.getPage(page - 1)
            outfile = PdfFileWriter()
            outfile.addPage(p)
            with open(fpath, 'wb') as f:
                outfile.write(f)
            layout, dim = get_page_layout(fpath)
            # fix rotated PDF
            lttextlh = get_text_objects(layout, ltype="lh")
            lttextlv = get_text_objects(layout, ltype="lv")
            ltchar = get_text_objects(layout, ltype="char")
            rotation = get_rotation(lttextlh, lttextlv, ltchar)
            if rotation != '':
                fpath_new = ''.join([froot.replace('page', 'p'), '_rotated', fext])
                os.rename(fpath, fpath_new)
                infile = PdfFileReader(open(fpath_new, 'rb'), strict=False)
                if infile.isEncrypted:
                    infile.decrypt('')
                outfile = PdfFileWriter()
                p = infile.getPage(0)
                if rotation == 'anticlockwise':
                    p.rotateClockwise(90)
                elif rotation == 'clockwise':
                    p.rotateCounterClockwise(90)
                outfile.addPage(p)
                with open(fpath, 'wb') as f:
                    outfile.write(f)

    def parse(self, flavor='lattice', **kwargs):
        """Extracts tables by calling parser.get_tables on all single
        page PDFs.

        Parameters
        ----------
        flavor : str (default: 'lattice')
            The parsing method to use ('lattice' or 'stream').
            Lattice is used by default.
        kwargs : dict
            See camelot.read_pdf kwargs.

        Returns
        -------
        tables : camelot.core.TableList
            List of tables found in PDF.
        geometry : camelot.core.GeometryList
            List of geometry objects (contours, lines, joints) found
            in PDF.

        """
        tables = []
        with TemporaryDirectory() as tempdir:
            for p in self.pages:
                self._save_page(self.filename, p, tempdir)
            pages = [os.path.join(tempdir, 'page-{0}.pdf'.format(p))
                     for p in self.pages]
            parser = Lattice(**kwargs) if flavor == 'lattice' else Stream(**kwargs)
            for p in pages:
                t = parser.extract_tables(p)
                tables.extend(t)
        return TableList(tables)