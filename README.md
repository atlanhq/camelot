# camelot

## Dependencies

Currently, camelot works under Python 2.7.

The required dependencies include pdfminer, numpy, opencv.

For debugging, matplotlib is required. For runnings tests in the future, nose may be required.

camelot also uses poppler-utils, more specifically `pdfseparate` to separate pdfs into pages, with ImageMagick's `convert` to convert that page into an image.

## Install

## Usage

python2 camelot.py [options] file

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

## Development

### Code

You can check the latest sources with the command:

<pre>
git clone https://github.com/socialcopsdev/camelot.git
</pre>

### Contributing

The preferred way to contribute to camelot is to fork this repository, and then submit a "pull request" (PR):

1. Create an account on GitHub if you don't already have one.
2. Fork the project repository: click on the ‘Fork’ button near the top of the page. This creates a copy of the code under your account on the GitHub server.
3. Clone this copy to your local disk.
4. Create a branch to hold your changes:
<pre>
git checkout -b my-feature
</pre>
5. Work on this copy, on your computer, using Git to do the version control. When you’re done editing, do:
<pre>
$ git add modified_files
$ git commit
</pre>
to record your changes in Git, then push them to GitHub with:
<pre>
$ git push -u origin my-feature
</pre>

Finally, go to the web page of the your fork of the camelot repo, and click ‘Pull request’ to send your changes to the maintainers for review.

### Testing

## License
