from camelot import Pdf
from camelot import Lattice


extractor = Lattice(Pdf("files/left_rotated_table.pdf", clean=True), scale=30)
tables = extractor.get_tables()
print tables

extractor = Lattice(Pdf("files/right_rotated_table.pdf", clean=True), scale=30)
tables = extractor.get_tables()
print tables
