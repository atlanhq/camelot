Camelot
-------

usage: python2 camelot.py [options] pdf_file

Parse yo pdf!

positional arguments:
  file

optional arguments:
  -h, --help            show this help message and exit

  -p PAGES [PAGES ...]  Specify the page numbers and/or page ranges to be
                        parsed. Example: -p="1 3-5 9", -p="all" (default:
                        -p="1")

  -f FORMAT             Output format (csv/xlsx). Example: -f="xlsx" (default:
                        -f="csv")

  -spreadsheet          Extract data stored in pdfs with ruling lines.
                        (default: False)

  -F ORIENTATION        Fill the values in empty cells. Example: -F="h",
                        -F="v", -F="hv" (default: None)

  -s [SCALE]            Scaling factor. Large scaling factor leads to smaller
                        lines being detected. (default: 15)

Under construction...