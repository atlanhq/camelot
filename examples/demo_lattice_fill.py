from camelot import Pdf
from camelot import Lattice


extractor = Lattice(
    Pdf("files/row_span_1.pdf", clean=True), fill='v', scale=40)
tables = extractor.get_tables()
print tables

extractor = Lattice(
    Pdf("files/row_span_2.pdf", clean=True), fill='v', scale=30)
tables = extractor.get_tables()
print tables
