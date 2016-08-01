from camelot import Pdf
from camelot import Stream


extractor = Stream(Pdf("files/budget_2014-15.pdf",
                       char_margin=1.0, clean=True))
tables = extractor.get_tables()
print tables
