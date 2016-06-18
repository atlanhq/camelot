from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTChar, LTTextLineHorizontal

text = []

def parse_text_basic(layout):
	global text
	try:
		for obj in layout._objs:
			if type(obj) is LTTextLineHorizontal:
				text.append(obj)
			parse_text_basic(obj)
	except AttributeError:
		pass

def parse_text_spreadsheet(layout):
	global text
	try:
		for obj in layout._objs:
			if type(obj) is LTChar:
				text.append(obj)
			parse_text_spreadsheet(obj)
	except AttributeError:
		pass

def get_pdf_info(pdfname, method):
	global text
	with open(pdfname, 'r') as f:
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
			text = []
			if method == 'basic':
				parse_text_basic(layout)
			elif method == 'spreadsheet':
				parse_text_spreadsheet(layout)
			pdf_x, pdf_y = layout.bbox[2], layout.bbox[3]
		text.sort(key=lambda x: (-x.y0, x.x0))
	return text, pdf_x, pdf_y