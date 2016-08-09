from camelot import Pdf
from camelot import Lattice


extractor = Lattice(Pdf("files/column_span_1.pdf", clean=True), scale=30)
tables = extractor.get_tables()
print tables

extractor = Lattice(Pdf("files/column_span_2.pdf"), clean=True, scale=30)
tables = extractor.get_tables()
print tables
