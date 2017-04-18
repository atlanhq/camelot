"""
usage: python plot_intensity.py file.png threshold

plots sum of pixel intensities on both axes for an image.
"""
import sys
import time
from itertools import groupby
from operator import itemgetter

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pylab import barh


def timeit(func):
    def timed(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print 'Function: %r took: %2.4f seconds' % (func.__name__, end - start)
        return result
    return timed


def plot_barchart(ar):
    n = len(ar)
    ind = np.arange(n)
    width = 0.35
    plt.bar(ind, ar, width, color='r', zorder=1)
    plt.show()


def merge_lines(lines):
    ranges = []
    for k, g in groupby(enumerate(lines), lambda (i, x): i-x):
        group = map(itemgetter(1), g)
        ranges.append((group[0], group[-1]))
    merged = []
    for r in ranges:
        merged.append((r[0] + r[1]) / 2)
    return merged


def plot_lines(image, lines):
    for y in lines:
        plt.plot([0, image.shape[1]], [y, y])
    plt.imshow(image)
    plt.show()


@timeit
def main():
    image = cv2.imread(sys.argv[1])
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    threshold = cv2.adaptiveThreshold(np.invert(gray), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)
    y_proj = np.sum(threshold, axis=1)
    line_threshold = int(sys.argv[2])
    lines = np.where(y_proj < line_threshold)[0]
    lines = merge_lines(lines)
    plot_lines(image, lines)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()
