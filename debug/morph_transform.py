"""
usage: python morph_transform.py file.png

find lines present in an image using opencv's morph transform.
"""

import sys
import time

import cv2
import numpy as np
import matplotlib.pyplot as plt


def timeit(func):
    def timed(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print 'Function: %r took: %2.4f seconds' % (func.__name__, end - start)
        return result
    return timed


def mt(imagename, scale=40):
    img = cv2.imread(imagename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    threshold = cv2.adaptiveThreshold(np.invert(gray), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)
    vertical = threshold
    horizontal = threshold

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
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    tables = {}
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        # find number of non-zero values in joints using what boundingRect returns
        roi = joints[y:y+h, x:x+w]
        jc, _ = cv2.findContours(roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        if len(jc) <= 4: # remove contours with less than <=4 joints
            continue
        joint_coords = []
        for j in jc:
            jx, jy, jw, jh = cv2.boundingRect(j)
            c1, c2 = x + (2*jx + jw) / 2, y + (2*jy + jh) / 2
            joint_coords.append((c1, c2))
        tables[(x1, y2, x2, y1)] = joint_coords

    vcontours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for vc in vcontours:
        x, y, w, h = cv2.boundingRect(vc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        plt.plot([(x1 + x2) / 2, (x1 + x2) / 2], [y2, y1])

    hcontours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for hc in hcontours:
        x, y, w, h = cv2.boundingRect(hc)
        x1, x2 = x, x + w
        y1, y2 = y, y + h
        plt.plot([x1, x2], [(y1 + y2) / 2, (y1 + y2) / 2])

    x_coord = []
    y_coord = []
    for k in tables.keys():
        for coord in tables[k]:
            x_coord.append(coord[0])
            y_coord.append(coord[1])
    plt.plot(x_coord, y_coord, 'ro')

    plt.imshow(img)
    plt.show()
    return tables


@timeit
def main():
    t = mt(sys.argv[1])
    print 'tables found: ', len(t.keys())


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()