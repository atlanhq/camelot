import cv2
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

matplotlib.use('agg')


def plot_pdf(table, geometry_type, filename=None):
        """Plot geometry found on PDF page based on geometry_type
        specified, useful for debugging and playing with different
        parameters to get the best output.

        Parameters
        ----------
        table: Table
            The table object to plot data from
        geometry_type : str
            The geometry type for which a plot should be generated.
            Can be 'text', 'table', 'contour', 'joint', 'line'
        filename: str
            If specified, saves the plot to a file with the given name
        """
        if table.flavor == 'stream' and geometry_type in ['contour', 'joint', 'line']:
            raise NotImplementedError("{} cannot be plotted with flavor='stream'".format(
                                       geometry_type))
        if geometry_type == 'text':
            plot_text(table._text)
        elif geometry_type == 'table':
            plot_table(table)
        elif geometry_type == 'contour':
            plot_contour(table._image)
        elif geometry_type == 'joint':
            plot_joint(table._image)
        elif geometry_type == 'line':
            plot_line(table._segments)
        if filename:
            plt.savefig(filename)
        plt.show()

def plot_text(text):
    """Generates a plot for all text present on the PDF page.

    Parameters
    ----------
    text : list

    """
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    xs, ys = [], []
    for t in text:
        xs.extend([t[0], t[2]])
        ys.extend([t[1], t[3]])
        ax.add_patch(
            patches.Rectangle(
                (t[0], t[1]),
                t[2] - t[0],
                t[3] - t[1]
            )
        )
    ax.set_xlim(min(xs) - 10, max(xs) + 10)
    ax.set_ylim(min(ys) - 10, max(ys) + 10)
    return fig


def plot_table(table):
    """Generates a plot for the table.

    Parameters
    ----------
    table : camelot.core.Table

    """
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    for row in table.cells:
        for cell in row:
            if cell.left:
                ax.plot([cell.lb[0], cell.lt[0]],
                         [cell.lb[1], cell.lt[1]])
            if cell.right:
                ax.plot([cell.rb[0], cell.rt[0]],
                         [cell.rb[1], cell.rt[1]])
            if cell.top:
                ax.plot([cell.lt[0], cell.rt[0]],
                         [cell.lt[1], cell.rt[1]])
            if cell.bottom:
                ax.plot([cell.lb[0], cell.rb[0]],
                         [cell.lb[1], cell.rb[1]])
    return fig


def plot_contour(image):
    """Generates a plot for all table boundaries present on the
    PDF page.

    Parameters
    ----------
    image : tuple

    """
    img, table_bbox = image
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')    
    for t in table_bbox.keys():
        cv2.rectangle(img, (t[0], t[1]),
                      (t[2], t[3]), (255, 0, 0), 20)
    ax.imshow(img)
    return fig


def plot_joint(image):
    """Generates a plot for all line intersections present on the
    PDF page.

    Parameters
    ----------
    image : tuple

    """
    img, table_bbox = image
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')    
    x_coord = []
    y_coord = []
    for k in table_bbox.keys():
        for coord in table_bbox[k]:
            x_coord.append(coord[0])
            y_coord.append(coord[1])
    ax.plot(x_coord, y_coord, 'ro')
    ax.imshow(img)
    return fig


def plot_line(segments):
    """Generates a plot for all line segments present on the PDF page.

    Parameters
    ----------
    segments : tuple

    """
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')    
    vertical, horizontal = segments
    for v in vertical:
        ax.plot([v[0], v[2]], [v[1], v[3]])
    for h in horizontal:
        ax.plot([h[0], h[2]], [h[1], h[3]])
    return fig
