import cv2
import numpy as np


def morph_transform(imagename, s, invert):
    # http://answers.opencv.org/question/63847/how-to-extract-tables-from-an-image/
    img = cv2.imread(imagename)
    img_x, img_y = img.shape[1], img.shape[0]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # empirical result taken from
    # http://pequan.lip6.fr/~bereziat/pima/2012/seuillage/sezgin04.pdf
    if invert:
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -0.2)
    else:
        threshold = cv2.adaptiveThreshold(np.invert(
            gray), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -0.2)
    vertical = threshold
    horizontal = threshold

    scale = s
    verticalsize = vertical.shape[0] / scale
    horizontalsize = horizontal.shape[1] / scale

    ver = cv2.getStructuringElement(cv2.MORPH_RECT, (1, verticalsize))
    hor = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontalsize, 1))

    vertical = cv2.erode(vertical, ver, (-1, -1))
    vertical = cv2.dilate(vertical, ver, (-1, -1))

    horizontal = cv2.erode(horizontal, hor, (-1, -1))
    horizontal = cv2.dilate(horizontal, hor, (-1, -1))

    mask = vertical + horizontal
    joints = np.bitwise_and(vertical, horizontal)
    _, contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    tables = {}
    for c in contours:
        c_poly = cv2.approxPolyDP(c, 3, True)
        x, y, w, h = cv2.boundingRect(c_poly)
        # find number of non-zero values in joints using what boundingRect
        # returns
        roi = joints[y:y + h, x:x + w]
        _, jc, _ = cv2.findContours(
            roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if len(jc) <= 4:  # remove contours with less than <=4 joints
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2 * jx + jw) / 2, y + (2 * jy + jh) / 2
            joint_coords.append((c1, c2))
        tables[(x, y + h, x + w, y)] = joint_coords

    v_segments, h_segments = [], []
    _, vcontours, _ = cv2.findContours(
        vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for vc in vcontours:
        x, y, w, h = cv2.boundingRect(vc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        v_segments.append(((x1 + x2) / 2, y2, (x1 + x2) / 2, y1))

    _, hcontours, _ = cv2.findContours(
        horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for hc in hcontours:
        x, y, w, h = cv2.boundingRect(hc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        h_segments.append((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2))

    return tables, v_segments, h_segments
