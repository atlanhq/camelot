"""
usage: python hough_prob.py file.png

finds lines present in an image using scikit-image's hough transform.
"""

import sys
import time

from scipy.misc import imread
import matplotlib.pyplot as plt
from skimage.feature import canny
from skimage.transform import probabilistic_hough_line


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
    image = imread(sys.argv[1], mode='L')
    edges = canny(image, 2, 1, 25)
    lines = probabilistic_hough_line(edges, threshold=1000)

    fig, ax = plt.subplots(1, 1, figsize=(8,4), sharex=True, sharey=True)
    ax.imshow(edges * 0)

    for line in lines:
        p0, p1 = line
        ax.plot((p0[0], p1[0]), (p0[1], p1[1]))

    ax.set_title('Probabilistic Hough')
    ax.set_axis_off()
    ax.set_adjustable('box-forced')
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()