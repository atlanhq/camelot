"""
usage: python hough_skimage.py file.png

find lines present in an image using scikit-image's hough transform.
"""

import sys
import time

import cv2
import numpy as np
from scipy.misc import imread
import matplotlib.pyplot as plt
from skimage.transform import hough_line, hough_line_peaks


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
    ret, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
    binary = np.min(binary, axis=2)
    binary = np.where(binary == 255, 0, 255)
    rows, cols = binary.shape
    pixel = np.zeros(binary.shape)

    fig, ax = plt.subplots(1, 1, figsize=(8,4))
    ax.imshow(image, cmap=plt.cm.gray)

    theta_in = np.linspace(0, np.pi / 2, 10)
    h, theta, d = hough_line(binary, theta_in)
    for _, angle, dist in zip(*hough_line_peaks(h, theta, d)):
        x0 = dist * np.cos(angle)
        y0 = dist * np.sin(angle)
        x1 = int(x0 + 1000 * (-np.sin(angle)))
        y1 = int(y0 + 1000 * (np.cos(angle)))
        x2 = int(x0 - 1000 * (-np.sin(angle)))
        y2 = int(y0 - 1000 * (np.cos(angle)))
        ax.plot((x1, x2), (y1, y2), '-r')
        a = np.cos(angle)
        b = np.sin(angle)
        x = np.arange(binary.shape[1])
        y = np.arange(binary.shape[0])
        x = a * x
        y = b * y
        R = np.round(np.add(y.reshape((binary.shape[0], 1)), x.reshape((1, binary.shape[1]))))
        pixel += np.isclose(R, np.round(dist))

    pixel = np.clip(pixel, 0, 1)
    pixel = np.where(pixel == 1, 0, 1)
    binary = np.where(binary == 0, 255, 0)
    binary *= pixel.astype(np.int64)
    ax.imshow(binary, cmap=plt.cm.gray)
    ax.axis((0, cols, rows, 0))
    ax.set_title('Detected lines')
    ax.set_axis_off()
    ax.set_adjustable('box-forced')
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()