from .handlers import PDFHandler
from .utils import validate_input, remove_extra


def read_pdf(filepath, pages='1', mesh=False, **kwargs):
    """Read PDF and return parsed data tables.

    Note: kwargs annotated with ^ can only be used with mesh=False
    and kwargs annotated with * can only be used with mesh=True.

    Parameters
    ----------
    filepath : str
        Path to pdf file.
    pages : str
        Comma-separated page numbers to parse.
        Example: 1,3,4 or 1,4-end
    mesh : bool (default: False)
        Whether or not to use Lattice method of parsing. Stream
        is used by default.
    table_area : list, optional (default: None)
        List of table areas to process as strings of the form
        x1,y1,x2,y2 where (x1, y1) -> left-top and
        (x2, y2) -> right-bottom in pdf coordinate space.
    columns^ : list, optional (default: None)
        List of column x-coordinates as strings where the coordinates
        are comma-separated.
    split_text : bool, optional (default: False)
        Whether or not to split a text line if it spans across
        multiple cells.
    flag_size : bool, optional (default: False)
        Whether or not to highlight a substring using <s></s>
        if its size is different from rest of the string, useful for
        super and subscripts.
    row_close_tol^ : int, optional (default: 2)
        Rows will be formed by combining text vertically
        within this tolerance.
    col_close_tol^ : int, optional (default: 0)
        Columns will be formed by combining text horizontally
        within this tolerance.
    process_background* : bool, optional (default: False)
        Whether or not to process lines that are in background.
    line_size_scaling* : int, optional (default: 15)
        Factor by which the page dimensions will be divided to get
        smallest length of lines that should be detected.

        The larger this value, smaller the detected lines. Making it
        too large will lead to text being detected as lines.
    copy_text* : list, optional (default: None)
        {'h', 'v'}
        Select one or more strings from above and pass them as a list
        to specify the direction in which text should be copied over
        when a cell spans multiple rows or columns.
    shift_text* : list, optional (default: ['l', 't'])
        {'l', 'r', 't', 'b'}
        Select one or more strings from above and pass them as a list
        to specify where the text in a spanning cell should flow.
    line_close_tol* : int, optional (default: 2)
        Tolerance parameter used to merge vertical and horizontal
        detected lines which lie close to each other.
    joint_close_tol* : int, optional (default: 2)
        Tolerance parameter used to decide whether the detected lines
        and points lie close to each other.
    threshold_blocksize : int, optional (default: 15)
        Size of a pixel neighborhood that is used to calculate a
        threshold value for the pixel: 3, 5, 7, and so on.

        For more information, refer `OpenCV's adaptiveThreshold <https://docs.opencv.org/2.4/modules/imgproc/doc/miscellaneous_transformations.html#adaptivethreshold>`_.
    threshold_constant : int, optional (default: -2)
        Constant subtracted from the mean or weighted mean.
        Normally, it is positive but may be zero or negative as well.

        For more information, refer `OpenCV's adaptiveThreshold <https://docs.opencv.org/2.4/modules/imgproc/doc/miscellaneous_transformations.html#adaptivethreshold>`_.
    iterations : int, optional (default: 0)
        Number of times for erosion/dilation is applied.

        For more information, refer `OpenCV's dilate <https://docs.opencv.org/2.4/modules/imgproc/doc/filtering.html#dilate>`_.
    margins : tuple
        PDFMiner margins. (char_margin, line_margin, word_margin)

        For for information, refer `PDFMiner docs <https://euske.github.io/pdfminer/>`_.

    Returns
    -------
    tables : camelot.core.TableList

    """
    validate_input(kwargs, mesh=mesh)
    p = PDFHandler(filepath, pages)
    kwargs = remove_extra(kwargs, mesh=mesh)
    tables, __ = p.parse(mesh=mesh, **kwargs)
    return tables