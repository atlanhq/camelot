from camelot import Pdf
from camelot import Lattice


extractor = Lattice(Pdf("files/lines_in_background_1.pdf",
                        clean=True), scale=30, invert=True)
tables = extractor.get_tables()
print tables

extractor = Lattice(Pdf("files/lines_in_background_2.pdf",
                        clean=True), scale=30, invert=True)
tables = extractor.get_tables()
print tables
