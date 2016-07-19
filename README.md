# camelot

## Dependencies

Currently, camelot works under Python 2.7.

The required dependencies include pdfminer, numpy, opencv.

For debugging, matplotlib is required. For runnings tests in the future, nose may be required.

camelot also uses poppler-utils, more specifically `pdfseparate` to separate a pdf into pages, with ImageMagick's `convert` to convert each page into an image.

## Install

## Usage

<pre>
camelot.py [options] <method> [<args>...]

options:
 -h, --help                Show this screen.
 -v, --version             Show version.
 -p, --pages &lt;pageno&gt;      Comma-separated list of page numbers.
                           Example: -p 1,3-6,10  [default: 1]
 -f, --format &lt;format&gt;     Output format. (csv,xlsx) [default: csv]
 -l, --log                 Print log to file.
 -o, --output &lt;directory&gt;  Output directory.

camelot methods:
 lattice  Looks for lines between data.
 stream   Looks for spaces between data.

See 'camelot <method> -h' for more information on a specific method.
</pre>

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
and start making changes. Never work in the `master` branch!
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
