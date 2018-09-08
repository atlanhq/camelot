from itertools import groupby
from operator import itemgetter

import cv2
import numpy as np

from .utils import merge_tuples


def adaptive_threshold(imagename, process_background=False, blocksize=15, c=-2):
    """

    Parameters
    ----------
    imagename
    process_background
    blocksize
    c

    Returns
    -------

    """
    img = cv2.imread(imagename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if process_background:
        threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blocksize, c)
    else:
        threshold = cv2.adaptiveThreshold(np.invert(gray), 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blocksize, c)
    return img, threshold


def find_lines(threshold, direction='horizontal', line_size_scaling=15, iterations=0):
    """

    Parameters
    ----------
    threshold
    direction
    line_size_scaling
    iterations

    Returns
    -------

    """
    lines = []

    if direction == 'vertical':
        size = threshold.shape[0] // line_size_scaling
        el = cv2.getStructuringElement(cv2.MORPH_RECT, (1, size))
    elif direction == 'horizontal':
        size = threshold.shape[1] // line_size_scaling
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
    """

    Parameters
    ----------
    vertical
    horizontal

    Returns
    -------

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
    """

    Parameters
    ----------
    contours
    vertical
    horizontal

    Returns
    -------

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


def remove_lines(threshold, line_size_scaling=15):
    """

    Parameters
    ----------
    threshold
    line_size_scaling

    Returns
    -------

    """
    size = threshold.shape[0] // line_size_scaling
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


def find_cuts(threshold, char_size_scaling=200):
    """

    Parameters
    ----------
    threshold
    char_size_scaling

    Returns
    -------

    """
    size = threshold.shape[0] // char_size_scaling
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