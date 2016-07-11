Camelot
-------

Description: Parse tables from pdfs!

Dependencies

Install

Usage: python2 camelot.py [options] file

positional arguments:

  file

optional arguments:

  -h, --help

    show this help message and exit

  -p, --pages PAGES [PAGES ...]

    Specify the page numbers and/or page ranges to be
    parsed. Example: -p="1 3-5 9", -p="all" (default: 1)

  -f, --format FORMAT

    Output format (csv/xlsx). Example: -f="xlsx" (default: csv)

  -m, --spreadsheet

    Extract tables with ruling lines. (default: False)

  -F, --fill FILL

    Fill the values in empty cells horizontally(h) and/or
    vertically(v). Example: -F="h", -F="v", -F="hv" (default: None)

  -s, --scale [SCALE]

    Scaling factor. Large scaling factor leads to smaller
    lines being detected. (default: 15)

  -j, --jtol [JTOL]

    Tolerance to account for when comparing joint and line
    coordinates. (default: 2)

  -M, --mtol [MTOL]

    Tolerance to account for when merging lines which are
    very close. (default: 2)

  -i, --invert

    Make sure lines are in foreground. (default: False)

  -d, --debug DEBUG

    Debug by visualizing contours, lines, joints, tables.
    Example: --debug="contours"

  -o, --output OUTPUT

    Specify output directory.

Development: Code, Contributing, Tests

License
