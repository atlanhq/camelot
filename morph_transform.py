import cv2
import sys
import subprocess
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar

def transform(x, y, img_x, img_y, pdf_x, pdf_y):
	x *= pdf_x / float(img_x)
	y = abs(y - img_y)
	y *= pdf_y / float(img_y)
	return x, y

# http://answers.opencv.org/question/63847/how-to-extract-tables-from-an-image/
def morph(imagename, p_x, p_y, s):
	img = cv2.imread(imagename)
	img_x, img_y = img.shape[1], img.shape[0]
	pdf_x, pdf_y = p_x, p_y
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	th1 = cv2.adaptiveThreshold(np.invert(gray), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
	vertical = th1
	horizontal = th1

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
	_, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

	tables = {}
	for c in contours:
		x, y, w, h = cv2.boundingRect(c)
		jmask = joints[y:y+h, x:x+w]
		_, jc, _ = cv2.findContours(jmask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
		
		if len(jc) <= 4: # remove contours with less than <=4 joints
			continue
		x1, y1 = transform(x, y, img_x, img_y, pdf_x, pdf_y)
		x2, y2 = transform(x + w, y + h, img_x, img_y, pdf_x, pdf_y)
		tables[(x1, y2)] = (x2, y1)

	v_segments, h_segments = [], []
	_, vcontours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	for vc in vcontours:
		x, y, w, h = cv2.boundingRect(vc)
		x1, y1 = transform(x, y, img_x, img_y, pdf_x, pdf_y)
		x2, y2 = transform(x + w, y + h, img_x, img_y, pdf_x, pdf_y)
		v_segments.append(((x1 + x2) / 2, y2, (x1 + x2) / 2, y1))
		
	_, hcontours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	for hc in hcontours:
		x, y, w, h = cv2.boundingRect(hc)
		x1, y1 = transform(x, y, img_x, img_y, pdf_x, pdf_y)
		x2, y2 = transform(x + w, y + h, img_x, img_y, pdf_x, pdf_y)
		h_segments.append((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2))

	return tables, v_segments, h_segments