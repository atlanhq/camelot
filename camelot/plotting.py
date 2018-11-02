# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def plot(table, plot_type='text', filepath=None):
    """Plot elements found on PDF page based on plot_type
    specified, useful for debugging and playing with different
    parameters to get the best output.

    Parameters
    ----------
    table: Table
        A Camelot Table.
    plot_type : str, optional (default: 'text')
        {'text', 'table', 'contour', 'joint', 'line'}
        The element type for which a plot should be generated.
    filepath: str, optional (default: None)
        Absolute path for saving the generated plot.

    Returns
    -------
    fig : matplotlib.fig.Figure

    """
    if table.flavor == 'stream' and plot_type in ['contour', 'joint', 'line']:
        raise NotImplementedError("{} cannot be plotted with flavor='stream'".format(
                                    plot_type))
    if plot_type == 'text':
        fig = plot_text(table._text)
    elif plot_type == 'table':
        fig = plot_table(table)
    elif plot_type == 'contour':
        fig = plot_contour(table._image)
    elif plot_type == 'joint':
        fig = plot_joint(table._image)
    elif plot_type == 'line':
        fig = plot_line(table._segments)
    if filepath:
        plt.savefig(filepath)
    return fig


def plot_text(text):
    """Generates a plot for all text elements present
    on the PDF page.

    Parameters
    ----------
    text : list

    Returns
    -------
    fig : matplotlib.fig.Figure

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
    """Generates a plot for the detected tables
    on the PDF page.

    Parameters
    ----------
    table : camelot.core.Table

    Returns
    -------
    fig : matplotlib.fig.Figure

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
    """Generates a plot for all table boundaries present
    on the PDF page.

    Parameters
    ----------
    image : tuple

    Returns
    -------
    fig : matplotlib.fig.Figure

    """
    img, table_bbox = image
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    for t in table_bbox.keys():
        ax.add_patch(
            patches.Rectangle(
                (t[0], t[1]),
                t[2] - t[0],
                t[3] - t[1],
                fill=None,
                edgecolor='red'
            )
        )
    ax.imshow(img)
    return fig


def plot_joint(image):
    """Generates a plot for all line intersections present
    on the PDF page.

    Parameters
    ----------
    image : tuple

    Returns
    -------
    fig : matplotlib.fig.Figure

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
    """Generates a plot for all line segments present
    on the PDF page.

    Parameters
    ----------
    segments : tuple

    Returns
    -------
    fig : matplotlib.fig.Figure

    """
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    vertical, horizontal = segments
    for v in vertical:
        ax.plot([v[0], v[2]], [v[1], v[3]])
    for h in horizontal:
        ax.plot([h[0], h[2]], [h[1], h[3]])
    return fig
