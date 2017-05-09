from itertools import groupby
from operator import itemgetter
from collections import defaultdict

import cv2
import numpy as np

from .utils import to_wh, find_parent, merge_tuples


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


def cluster_contours(contours, tol=10):
    def isin(x, coords):
        return any(np.isclose(x, coord, atol=tol) for coord in coords)

    def find_cluster(clusters, contour):
        x, y, w, h = contour
        for i, cluster in enumerate(clusters):
            if isin(x, cluster['x1']) or isin(y, cluster['y1']) or \
                    isin(x + w, cluster['x2']) or isin(y + h, cluster['y2']):
                return i
        return None

    def add_cluster(clusters, contour):
        x, y, w, h = contour
        clusters.append({'x1': [x], 'y1': [y], 'x2': [x + w], 'y2': [y + h]})
        return clusters

    def update_cluster(clusters, idx, contour):
        x, y, w, h = contour
        clusters[idx]['x1'].append(x)
        clusters[idx]['y1'].append(y)
        clusters[idx]['x2'].append(x + w)
        clusters[idx]['y2'].append(y + h)
        return clusters

    def collapse_clusters(clusters):
        collapsed = []
        for cluster in clusters:
            collapsed.append((min(cluster['x1']), min(cluster['y1']),
                max(cluster['x2']), max(cluster['y2'])))
        return collapsed

    x, y, w, h = contours[0]
    clusters = [{'x1': [x], 'y1': [y], 'x2': [x + w], 'y2': [y + h]}]
    for i in range(1, len(contours)):
        idx = find_cluster(clusters, contours[i])
        if idx is not None:
            clusters = update_cluster(clusters, idx, contours[i])
        else:
            clusters = add_cluster(clusters, contours[i])

    return collapse_clusters(clusters)



def group_contours(parents, children):
    def find_parent(parents, child_rect):
        x, y, w, h = child_rect
        for parent in parents:
            parent_rect = cv2.boundingRect(parent)
            X, Y, W, H = parent_rect
            if x >= X and y >= Y and x + w <= X + W and y + h <= Y + H:
                return parent_rect
        return None

    children = sorted(children, key=cv2.contourArea, reverse=True)
    grouped = defaultdict(list)
    for child in children:
        child_rect = cv2.boundingRect(child)
        parent_rect = find_parent(parents, child_rect)
        if parent_rect is not None:
            grouped[parent_rect].append(child_rect)

    return grouped


def remove_parent(grouped):
    def distance(a, b):
        return sum(map(lambda x: abs(x[0] - x[1]), zip(a, b)))

    def get_bounding_rect(a, b):
        return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])

    hierarchy = {}
    for parent_rect in grouped.keys():
        closest_rect = min(grouped[parent_rect], key=lambda x: distance(x, parent_rect))
        idx = grouped[parent_rect].index(closest_rect)
        closest_rect = to_wh(get_bounding_rect(parent_rect, closest_rect))
        hierarchy[closest_rect] = []
        grouped[parent_rect].pop(idx)
        for child_rect in grouped[parent_rect]:
            hierarchy[closest_rect].append(to_wh(child_rect))

    return hierarchy


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

    hierarchy : dict
    """
    def flatten(d):
        contours = []
        for k in d.keys():
            contours.append(k)
            for c in d[k]:
                contours.append(c)
        return contours

    mask = vertical + horizontal
    try:
        __, contours, __ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    except ValueError:
        contours, __ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    parents, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    children, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    grouped = group_contours(parents, children)
    for outer_bound in grouped.iterkeys():
        grouped[outer_bound] = cluster_contours(grouped[outer_bound])

    hierarchy = remove_parent(grouped)
    contours = flatten(hierarchy)

    return contours, hierarchy


def find_table_joints(vertical, horizontal, contours, hierarchy=None):
    """Finds joints/intersections present inside each table boundary.

    Parameters
    ----------
    vertical : object
        numpy.ndarray representing pixels where vertical lines lie.

    horizontal : object
        numpy.ndarray representing pixels where horizontal lines lie.

    contours : list
        List of tuples representing table boundaries. Each tuple is of
        the form (x, y, w, h) where (x, y) -> left-top, w -> width and
        h -> height in OpenCV's coordinate space.

    hierarchy : dict

    Returns
    -------
    tables : dict
        Dict with table boundaries as keys and list of intersections
        in that boundary as their value.

        Keys are of the form (x1, y1, x2, y2) where (x1, y1) -> lb
        and (x2, y2) -> rt in OpenCV's coordinate space.
    """
    def remove_contours(hierarchy, unused_contours):
        for c in unused_contours:
            if hierarchy.get(c) is not None:
                hierarchy.pop(c)
            else:
                for k in hierarchy.keys():
                    if c in hierarchy[k]:
                        idx = hierarchy[k].index(c)
                        hierarchy[k].pop(idx)
        return hierarchy

    def modify_hierarchy(h):
        if h is not None:
            hierarchy = {}
            for k, v in h.iteritems():
                x, y, w, h = k
                kpax = (x, y + h, x + w, y)
                hierarchy[kpax] = []
                for value in v:
                    vx, vy, vw, vh = value
                    vpax = (vx, vy + vh, vx + vw, vy)
                    hierarchy[kpax].append(vpax)
            return hierarchy
        return None

    joints = np.bitwise_and(vertical, horizontal)
    tables = {}
    used_contours = []
    for c in contours:
        parent, children = find_parent(hierarchy, c)
        if children is not None:
            px, py, pw, ph = parent
            roi = joints[py : py + ph, px : px + pw]
            try:
                __, jc, __ = cv2.findContours(
                    roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            except ValueError:
                jc, __ = cv2.findContours(
                    roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            if len(jc) <= 4:  # remove contours with less than 4 joints
                continue
            used_contours.append(c)
            joint_coords = []
            for j in jc:
                jx, jy, jw, jh = cv2.boundingRect(j)
                c1, c2 = px + (2 * jx + jw) / 2, py + (2 * jy + jh) / 2
                if isinstance(children, list):
                    for child in children:
                        cx, cy, cw, ch = child
                        if cx - 10 <= c1 <= cx + cw + 10 and cy - 10 <= c2 <= cy + ch + 10:
                            continue
                        joint_coords.append((c1, c2))
                else:
                    joint_coords.append((c1, c2))
            tables[(px, py + ph, px + pw, py)] = joint_coords

    hierarchy = remove_contours(hierarchy, list(set(contours).difference(
        set(used_contours))))
    return tables, modify_hierarchy(hierarchy)


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