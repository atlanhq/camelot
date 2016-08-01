from camelot import Pdf
from camelot import Stream


extractor = Stream(Pdf("files/inconsistent_rows.pdf", char_margin=1.0),
                   columns="65,95,285,640,715,780", ytol=10)
tables = extractor.get_tables()
print tables

extractor = Stream(Pdf("files/consistent_rows.pdf", char_margin=1.0),
                   columns="28,67,180,230,425,475,700", ytol=5)
tables = extractor.get_tables()
print tables
