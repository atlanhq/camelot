from itertools import groupby
from operator import itemgetter

import cv2
import numpy as np

from .utils import merge_tuples


def adaptive_threshold(imagename, invert=False, blocksize=15, c=-2):
    """Thresholds an image using OpenCV's adaptiveThreshold.

    Parameters
    ----------
    imagename : string
        Path to image file.

    invert : bool
        Whether or not to invert the image. Useful when pdfs have
        tables with lines in background.
        (optional, default: False)

    blocksize: int
        Size of a pixel neighborhood that is used to calculate a
        threshold value for the pixel: 3, 5, 7, and so on.

    c: float
        Constant subtracted from the mean or weighted mean
        (see the details below). Normally, it is positive but may be
        zero or negative as well.

    Returns
    -------
    img : object
        numpy.ndarray representing the original image.

    threshold : object
        numpy.ndarray representing the thresholded image.
    """
    img = cv2.imread(imagename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if invert:
        threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blocksize, c)
    else:
        threshold = cv2.adaptiveThreshold(np.invert(gray), 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blocksize, c)
    return img, threshold


def find_lines(threshold, direction='horizontal', scale=15, iterations=0):
    """Finds horizontal and vertical lines by applying morphological
    transformations on an image.

    Parameters
    ----------
    threshold : object
        numpy.ndarray representing the thresholded image.

    direction : string
        Specifies whether to find vertical or horizontal lines.
        (default: 'horizontal')

    scale : int
        Used to divide the height/width to get a structuring element
        for morph transform.
        (optional, default: 15)

    iterations : int
        Number of iterations for dilation.
        (optional, default: 2)

    Returns
    -------
    dmask : object
        numpy.ndarray representing pixels where vertical/horizontal
        lines lie.

    lines : list
        List of tuples representing vertical/horizontal lines with
        coordinates relative to a left-top origin in
        OpenCV's coordinate space.
    """
    lines = []

    if direction == 'vertical':
        size = threshold.shape[0] // scale
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    elif direction == 'horizontal':
        size = threshold.shape[1] // scale
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (size, 1))
    elif direction is None:
        raise ValueError("Specify direction as either 'vertical' or"
                         " 'horizontal'")

    threshold = cv2.erode(threshold, el)
    threshold = cv2.dilate(threshold, el)
    dmask = cv2.dilate(threshold, el, iterations=iterations)

    try:
        _, contours, _ = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except ValueError:
        contours, _ = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        if direction == 'vertical':
            lines.append(((x1 + x2) / 2, y2, (x1 + x2) / 2, y1))
        elif direction == 'horizontal':
            lines.append((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2))

    return dmask, lines


def find_table_contours(vertical, horizontal):
    """Finds table boundaries using OpenCV's findContours.

    Parameters
    ----------
    vertical : object
        numpy.ndarray representing pixels where vertical lines lie.

    horizontal : object
        numpy.ndarray representing pixels where horizontal lines lie.

    Returns
    -------
    cont : list
        List of tuples representing table boundaries. Each tuple is of
        the form (x, y, w, h) where (x, y) -> left-top, w -> width and
        h -> height in OpenCV's coordinate space.
    """
    mask = vertical + horizontal

    try:
        __, contours, __ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except ValueError:
        contours, __ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    cont = []
    for c in contours:
        c_poly = cv2.approxPolyDP(c, 3, True)
        x, y, w, h = cv2.boundingRect(c_poly)
        cont.append((x, y, w, h))
    return cont


def find_table_joints(contours, vertical, horizontal):
    """Finds joints/intersections present inside each table boundary.

    Parameters
    ----------
    contours : list
        List of tuples representing table boundaries. Each tuple is of
        the form (x, y, w, h) where (x, y) -> left-top, w -> width and
        h -> height in OpenCV's coordinate space.

    vertical : object
        numpy.ndarray representing pixels where vertical lines lie.

    horizontal : object
        numpy.ndarray representing pixels where horizontal lines lie.

    Returns
    -------
    tables : dict
        Dict with table boundaries as keys and list of intersections
        in that boundary as their value.

        Keys are of the form (x1, y1, x2, y2) where (x1, y1) -> lb
        and (x2, y2) -> rt in OpenCV's coordinate space.
    """
    joints = np.bitwise_and(vertical, horizontal)
    tables = {}
    for c in contours:
        x, y, w, h = c
        roi = joints[y : y + h, x : x + w]
        try:
            __, jc, __ = cv2.findContours(
                roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        except ValueError:
            jc, __ = cv2.findContours(
                roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if len(jc) <= 4:  # remove contours with less than 4 joints
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2 * jx + jw) / 2, y + (2 * jy + jh) / 2
            joint_coords.append((c1, c2))
        tables[(x, y + h, x + w, y)] = joint_coords

    return tables


def remove_lines(threshold, line_scale=15):
    """Removes lines from a thresholded image.

    Parameters
    ----------
    threshold : object
        numpy.ndarray representing the thresholded image.

    line_scale : int
        Line scaling factor.
        (optional, default: 15)

    Returns
    -------
    threshold : object
        numpy.ndarray representing the thresholded image
        with horizontal and vertical lines removed.
    """
    size = threshold.shape[0] // line_scale
    vertical_erode_el = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    horizontal_erode_el = cv2.getStructuringElement(cv2.MORPH_RECT, (size, 1))
    dilate_el = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))

    vertical = cv2.erode(threshold, vertical_erode_el)
    vertical = cv2.dilate(vertical, dilate_el)

    horizontal = cv2.erode(threshold, horizontal_erode_el)
    horizontal = cv2.dilate(horizontal, dilate_el)

    threshold = np.bitwise_and(threshold, np.invert(vertical))
    threshold = np.bitwise_and(threshold, np.invert(horizontal))
    return threshold


def find_cuts(threshold, char_scale=200):
    """Finds cuts made by text projections on y-axis.

    Parameters
    ----------
    threshold : object
        numpy.ndarray representing the thresholded image.

    char_scale : int
        Char scaling factor.
        (optional, default: 200)

    Returns
    -------
    y_cuts : list
        List of cuts on y-axis.
    """
    size = threshold.shape[0] // char_scale
    char_el = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))

    threshold = cv2.erode(threshold, char_el)
    threshold = cv2.dilate(threshold, char_el)

    try:
        __, contours, __ = cv2.findContours(threshold, cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
    except ValueError:
        contours, __ = cv2.findContours(threshold, cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)

    contours = [cv2.boundingRect(c) for c in contours]
    y_cuts = [(c[1], c[1] + c[3]) for c in contours]
    y_cuts = list(merge_tuples(sorted(y_cuts)))
    y_cuts = [(y_cuts[i][0] + y_cuts[i - 1][1]) / 2 for i in range(1, len(y_cuts))]
    return sorted(y_cuts, reverse=True)