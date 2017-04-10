"""
usage: python threshold.py file.png blocksize threshold_constant

shows thresholded image.
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
    img = cv2.imread(sys.argv[1])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blocksize = int(sys.argv[2])
    threshold_constant = float(sys.argv[3])
    threshold = cv2.adaptiveThreshold(np.invert(gray), 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blocksize, threshold_constant)
    plt.imshow(img)
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()