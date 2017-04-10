"""
usage:  python plot_geo.py file.pdf
        python plot_geo.py file.pdf file.png

print lines and rectangles present in a pdf file.
"""

import sys
import time

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.layout import LAParams, LTLine, LTRect
from pdfminer.pdfpage import PDFTextExtractionNotAllowed


MIN_LENGTH = 1
pdf_x, pdf_y, image_x, image_y = [0] * 4


def timeit(func):
    def timed(*args, **kw):
        start = time.time()
        result = func(*args, **kw)
        end = time.time()
        print 'Function: %r took: %2.4f seconds' % (func.__name__, end - start)
        return result
    return timed


def remove_coords(coords):
    merged = []
    for coord in coords:
        if not merged:
            merged.append(coord)
        else:
            last = merged[-1]
            if np.isclose(last, coord, atol=2):
                pass
            else:
                merged.append(coord)
    return merged


def parse_layout(pdfname):
    global pdf_x, pdf_y
    def is_horizontal(line):
        if line[0] == line[2]:
            return True
        return False

    def is_vertical(line):
        if line[1] == line[3]:
            return True
        return False

    vertical, horizontal = [], []
    with open(pdfname, 'rb') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        laparams = LAParams()
        rsrcmgr = PDFResourceManager()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            pdf_x, pdf_y = layout.bbox[2], layout.bbox[3]
            for obj in layout._objs:
                if isinstance(obj, LTLine):
                    line = (obj.x0, obj.y0, obj.x1, obj.y1)
                    if is_vertical(line):
                        vertical.append(line)
                    elif is_horizontal(line):
                        horizontal.append(line)
                elif isinstance(obj, LTRect):
                    vertical.append((obj.x0, obj.y1, obj.x0, obj.y0))
                    vertical.append((obj.x1, obj.y1, obj.x1, obj.y0))
                    horizontal.append((obj.x0, obj.y1, obj.x1, obj.y1))
                    horizontal.append((obj.x0, obj.y0, obj.x1, obj.y0))
    return vertical, horizontal


def hough_transform(imagename):
    global pdf_x, pdf_y, image_x, image_y
    img = cv2.imread(imagename)
    image_x, image_y = img.shape[1], img.shape[0]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 1000)
    x = []
    for line in lines:
        r, theta = line[0]
        x0 = r * np.cos(theta)
        x0 *= pdf_x / float(image_x)
        x.append(x0)
    y = []
    for line in lines:
        r, theta = line[0]
        y0 = r * np.sin(theta)
        y0 = abs(y0 - image_y)
        y0 *= pdf_y / float(image_y)
        y.append(y0)
    x = remove_coords(sorted(set([x0 for x0 in x if x0 > 0])))
    y = remove_coords(sorted(set(y), reverse=True))
    return x, y


def plot_lines1(vertical, horizontal):
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 1000)

    vertical = filter(lambda x: abs(x[1] - x[3]) > MIN_LENGTH, vertical)
    horizontal = filter(lambda x: abs(x[0] - x[2]) > MIN_LENGTH, horizontal)
    for v in vertical:
        ax.plot([v[0], v[2]], [v[1], v[3]])
    for h in horizontal:
        ax.plot([h[0], h[2]], [h[1], h[3]])
    plt.show()


def plot_lines2(imagename, vertical, horizontal):
    x, y = hough_transform(imagename)
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 1000)

    for x0 in x:
        for v in vertical:
            if np.isclose(x0, v[0], atol=2):
                ax.plot([v[0], v[2]], [v[1], v[3]])
    for y0 in y:
        for h in horizontal:
            if np.isclose(y0, h[1], atol=2):
                ax.plot([h[0], h[2]], [h[1], h[3]])
    plt.show()


@timeit
def main():
    vertical, horizontal = parse_layout(sys.argv[1])
    if len(sys.argv) == 2:
        plot_lines1(vertical, horizontal)
    elif len(sys.argv) == 3:
        plot_lines1(vertical, horizontal)
        plot_lines2(sys.argv[2], vertical, horizontal)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print __doc__
    else:
        main()