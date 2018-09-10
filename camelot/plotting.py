import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from .handlers import PDFHandler
from .utils import validate_input, remove_extra


def plot_geometry(filepath, pages='1', mesh=False, geometry_type=None, **kwargs):
    """Plot geometry found on pdf page based on type specified,
    useful for debugging and playing with different parameters to get
    the best output.

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
    geometry_type : str, optional (default: None)
        'text' : Plot text objects found on page, useful to get
                 table_area and columns coordinates.
        'table' : Plot parsed table.
        'contour'* : Plot detected rectangles.
        'joint'* : Plot detected line intersections.
        'line'* : Plot detected lines.
    table_area : list, optional (default: None)
        List of table areas to analyze as strings of the form
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

    """
    validate_input(kwargs, mesh=mesh, geometry_type=geometry_type)
    p = PDFHandler(filepath, pages)
    kwargs = remove_extra(kwargs, mesh=mesh)
    debug = True if geometry_type is not None else False
    kwargs.update({'debug': debug})
    __, geometry = p.parse(mesh=mesh, **kwargs)

    if geometry_type == 'text':
        for text in geometry.text:
            fig = plt.figure()
            ax = fig.add_subplot(111, aspect='equal')
            xs, ys = [], []
            for t in text:
                xs.extend([t[0], t[1]])
                ys.extend([t[2], t[3]])
                ax.add_patch(
                    patches.Rectangle(
                        (t[0], t[1]),
                        t[2] - t[0],
                        t[3] - t[1]
                    )
                )
            ax.set_xlim(min(xs) - 10, max(xs) + 10)
            ax.set_ylim(min(ys) - 10, max(ys) + 10)
            plt.show()
    elif geometry_type == 'table':
        for tables in geometry.tables:
            for table in tables:
                for row in table.cells:
                    for cell in row:
                        if cell.left:
                            plt.plot([cell.lb[0], cell.lt[0]],
                                     [cell.lb[1], cell.lt[1]])
                        if cell.right:
                            plt.plot([cell.rb[0], cell.rt[0]],
                                     [cell.rb[1], cell.rt[1]])
                        if cell.top:
                            plt.plot([cell.lt[0], cell.rt[0]],
                                     [cell.lt[1], cell.rt[1]])
                        if cell.bottom:
                            plt.plot([cell.lb[0], cell.rb[0]],
                                     [cell.lb[1], cell.rb[1]])
            plt.show()
    elif geometry_type == 'contour':
        for img, table_bbox in geometry.images:
            for t in table_bbox.keys():
                cv2.rectangle(img, (t[0], t[1]),
                              (t[2], t[3]), (255, 0, 0), 3)
            plt.imshow(img)
            plt.show()
    elif geometry_type == 'joint':
        for img, table_bbox in geometry.images:
            x_coord = []
            y_coord = []
            for k in table_bbox.keys():
                for coord in table_bbox[k]:
                    x_coord.append(coord[0])
                    y_coord.append(coord[1])
            max_x, max_y = max(x_coord), max(y_coord)
            plt.plot(x_coord, y_coord, 'ro')
            plt.axis([0, max_x + 100, max_y + 100, 0])
            plt.imshow(img)
            plt.show()
    elif geometry_type == 'line':
        for v_s, h_s in geometry.segments:
            for v in v_s:
                plt.plot([v[0], v[2]], [v[1], v[3]])
            for h in h_s:
                plt.plot([h[0], h[2]], [h[1], h[3]])
            plt.show()