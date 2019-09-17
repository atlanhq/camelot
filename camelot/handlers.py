# -*- coding: utf-8 -*-

import os
import sys

from PyPDF2 import PdfFileReader, PdfFileWriter

from .core import TableList
from .parsers import Stream, Lattice
from .utils import (
    TemporaryDirectory,
    get_page_layout,
    get_text_objects,
    get_rotation,
    is_url,
    download_url,
)


class PDFHandler(object):
    """Handles all operations like temp directory creation, splitting
    file into single page PDFs, parsing each PDF and then removing the
    temp directory.

    Parameters
    ----------
    file_path : str
        File path or URL of the PDF file.
    file_obj: str
        File object of the PDF file
    pages : str, optional (default: '1')
        Comma-separated page numbers.
        Example: '1,3,4' or '1,4-end' or 'all'.
    password : str, optional (default: None)
        Password for decryption.

    """
    def __init__(self, file_path="", file_obj="", pages='1', password=None):
        if password is None:
            self.password = ''
        else:
            self.password = password
            if sys.version_info[0] < 3:
                self.password = self.password.encode('ascii')

        if file_path:
            if is_url(file_path):
                file_path = download_url(file_path)
            if not file_path.lower().endswith('.pdf'):
                raise NotImplementedError("File format not supported")

        self.file_path = file_path
        self.file_obj = file_obj

        if self.file_path:
            self.pages = self._get_pages(filepath=file_path, pages=pages)
        elif self.file_obj:
            self.pages = self._get_pages(fileObj=file_obj, pages=pages)
        else:
            raise ValueError("You must have either file_path or file_obj not empty")

    def _get_pages(self, filepath="", pages="1", fileObj=""):
        """Converts pages string to list of ints.

        Parameters
        ----------
        filepath : str
            Filepath or URL of the PDF file.
        fileObj : str
            File Object of the PDF file.
        pages : str, optional (default: '1')
            Comma-separated page numbers.
            Example: '1,3,4' or '1,4-end' or 'all'.

        Returns
        -------
        P : list
            List of int page numbers.

        """
        page_numbers = []
        if pages == "1":
            page_numbers.append({"start": 1, "end": 1})
        else:
            if filepath:
                infile = PdfFileReader(open(filepath, 'rb'), strict=False)
            if fileObj:
                infile = PdfFileReader(fileObj, strict=False)
            if infile.isEncrypted:
                infile.decrypt(self.password)
            if pages == "all":
                page_numbers.append({"start": 1, "end": infile.getNumPages()})
            else:
                for r in pages.split(","):
                    if "-" in r:
                        a, b = r.split("-")
                        if b == "end":
                            b = infile.getNumPages()
                        page_numbers.append({"start": int(a), "end": int(b)})
                    else:
                        page_numbers.append({"start": int(r), "end": int(r)})
        P = []
        for p in page_numbers:
            P.extend(range(p["start"], p["end"] + 1))
        return sorted(set(P))

    def _save_page(self, file_obj, page, temp):
        """Saves specified page from PDF into a temporary directory.

        Parameters
        ----------
        filepath : str
            Filepath or URL of the PDF file.
        page : int
            Page number.
        temp : str
            Tmp directory.

        """
        infile = PdfFileReader(file_obj, strict=False)
        if infile.isEncrypted:
            infile.decrypt(self.password)
        fpath = os.path.join(temp, "page-{0}.pdf".format(page))
        froot, fext = os.path.splitext(fpath)
        p = infile.getPage(page - 1)
        outfile = PdfFileWriter()
        outfile.addPage(p)
        with open(fpath, "wb") as f:
            outfile.write(f)
        layout, dim = get_page_layout(fpath)
        # fix rotated PDF
        chars = get_text_objects(layout, ltype="char")
        horizontal_text = get_text_objects(layout, ltype="horizontal_text")
        vertical_text = get_text_objects(layout, ltype="vertical_text")
        rotation = get_rotation(chars, horizontal_text, vertical_text)
        if rotation != "":
            fpath_new = "".join([froot.replace("page", "p"), "_rotated", fext])
            os.rename(fpath, fpath_new)
            infile = PdfFileReader(open(fpath_new, "rb"), strict=False)
            if infile.isEncrypted:
                infile.decrypt(self.password)
            outfile = PdfFileWriter()
            p = infile.getPage(0)
            if rotation == "anticlockwise":
                p.rotateClockwise(90)
            elif rotation == "clockwise":
                p.rotateCounterClockwise(90)
            outfile.addPage(p)
            with open(fpath, "wb") as f:
                outfile.write(f)

    def parse(
        self, flavor="lattice", suppress_stdout=False, layout_kwargs={}, **kwargs
    ):
        """Extracts tables by calling parser.get_tables on all single
        page PDFs.

        Parameters
        ----------
        flavor : str (default: 'lattice')
            The parsing method to use ('lattice' or 'stream').
            Lattice is used by default.
        suppress_stdout : str (default: False)
            Suppress logs and warnings.
        layout_kwargs : dict, optional (default: {})
            A dict of `pdfminer.layout.LAParams <https://github.com/euske/pdfminer/blob/master/pdfminer/layout.py#L33>`_ kwargs.
        kwargs : dict
            See camelot.read_pdf kwargs.

        Returns
        -------
        tables : camelot.core.TableList
            List of tables found in PDF.

        """
        tables = []
        with TemporaryDirectory() as tempdir:
            for p in self.pages:
                if self.file_path != "":
                    with open(self.file_path, "rb") as file_obj:
                        self._save_page(file_obj=file_obj, page=p, temp=tempdir)
                if self.file_obj != "":
                    self._save_page(file_obj=self.file_obj, page=p, temp=tempdir)
            pages = [
                os.path.join(tempdir, "page-{0}.pdf".format(p)) for p in self.pages
            ]
            parser = Lattice(**kwargs) if flavor == "lattice" else Stream(**kwargs)
            for p in pages:
                t = parser.extract_tables(
                    p, suppress_stdout=suppress_stdout, layout_kwargs=layout_kwargs
                )
                tables.extend(t)
        return TableList(sorted(tables))
