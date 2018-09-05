from .handlers import PDFHandler


def read_pdf(filepath, pages='1', mesh=False, **kwargs):
    """

    Parameters
    ----------
    filepath
    pages
    mesh
    kwargs

    Returns
    -------

    """
    # explicit type conversion
    p = PDFHandler(filepath, pages)
    tables, __ = p.parse(mesh=mesh, **kwargs)
    return tables