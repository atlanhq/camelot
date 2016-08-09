from camelot import Pdf
from camelot import Lattice


extractor = Lattice(Pdf("files/twotables_1.pdf", clean=True), scale=40)
tables = extractor.get_tables()
print tables

extractor = Lattice(Pdf("files/twotables_2.pdf", clean=True), scale=30)
tables = extractor.get_tables()
print tables
