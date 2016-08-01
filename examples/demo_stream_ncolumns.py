from camelot import Pdf
from camelot import Stream


extractor = Stream(Pdf("files/missing_values.pdf",
                       char_margin=1.0, clean=True), ncolumns=5)
tables = extractor.get_tables()
print tables
