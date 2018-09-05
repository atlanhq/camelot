from .handlers import PDFHandler


def read_pdf(filepath, pages='1', mesh=False, **kwargs):
    # explicit type conversion
    p = PDFHandler(filepath, pages)
    tables, __ = p.parse(mesh=mesh, **kwargs)
    return tables