"""
usage: python hough_opencv.py file.png

find lines present in an image using opencv's hough transform.
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


@timeit
def main():
    image = cv2.imread(sys.argv[1])
    print "image dimensions -> {0}".format(image.shape)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    print "found {0} lines".format(len(lines))
    for line in lines:
        r, theta = line[0]
        # filter horizontal and vertical lines
        if theta == 0 or np.isclose(theta, np.pi / 2):
            x0 = r * np.cos(theta)
            y0 = r * np.sin(theta)
            x1 = int(x0 + 10000 * (-np.sin(theta)))
            y1 = int(y0 + 10000 * (np.cos(theta)))
            x2 = int(x0 - 10000 * (-np.sin(theta)))
            y2 = int(y0 - 10000 * (np.cos(theta)))
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 5)
    plt.imshow(image)
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()