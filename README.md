# camelot

Camelot is a Python 2.7 library and command-line tool for getting tables out of PDF files.

## Usage

<pre>
from camelot.pdf import Pdf
from camelot.lattice import Lattice

manager = Pdf(Lattice(), "/path/to/pdf", pagenos=[{'start': 2, 'end': 4}], clean=True)
data = manager.extract()
</pre>

Camelot comes with a command-line tool in which you can specify the output format (csv, tsv, html, json, and xlsx), page numbers you want to parse and the output directory in which you want the output files to be placed. By default, the output files are placed in the same directory as the PDF.

<pre>
camelot: PDF parsing made simpler!

usage:
 camelot [options] <method> [<args>...]

options:
 -h, --help                Show this screen.
 -v, --version             Show version.
 -V, --verbose             Verbose.
 -p, --pages &lt;pageno&gt;      Comma-separated list of page numbers.
                           Example: -p 1,3-6,10  [default: 1]
 -P, --parallel            Parallelize the parsing process.
 -f, --format &lt;format&gt;     Output format. (csv,tsv,html,json,xlsx) [default: csv]
 -l, --log                 Log to file.
 -o, --output &lt;directory&gt;  Output directory.
 -M, --cmargin &lt;cmargin&gt;   Char margin. Chars closer than cmargin are
                           grouped together to form a word. [default: 2.0]
 -L, --lmargin &lt;lmargin&gt;   Line margin. Lines closer than lmargin are
                           grouped together to form a textbox. [default: 0.5]
 -W, --wmargin &lt;wmargin&gt;   Word margin. Insert blank spaces between chars
                           if distance between words is greater than word
                           margin. [default: 0.1]
 -S, --with-info           Save parsing info for each page to a file.
 -X, --plot &lt;dist&gt;         Plot distributions. (page,all,rc)
 -Z, --with-stats          Show stats.

camelot methods:
 lattice  Looks for lines between data.
 stream   Looks for spaces between data.

See 'camelot <method> -h' for more information on a specific method.
</pre>

## Dependencies

Currently, camelot works under Python 2.7.

The required dependencies include [numpy](http://www.numpy.org/), [OpenCV](http://opencv.org/) and [ImageMagick](http://www.imagemagick.org/script/index.php).

## Installation

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them with

<pre>
pip install -U pip, setuptools
</pre>

### Installing dependencies

numpy can be install using pip.

<pre>
pip install numpy
</pre>

OpenCV and imagemagick can be installed using your system's package manager.

#### Linux

* Arch Linux

<pre>
sudo pacman -S opencv imagemagick
</pre>

* Ubuntu

<pre>
sudo apt-get install libopencv-dev python-opencv imagemagick
</pre>

#### OS X

<pre>
brew install homebrew/science/opencv imagemagick
</pre>

Finally, `cd` into the project directory and install with

<pre>
make install
</pre>

## Development

### Code

You can check the latest sources with the command:

<pre>
git clone https://github.com/socialcopsdev/camelot.git
</pre>

### Contributing

See [Contributing doc]().

### Testing

<pre>
make test
</pre>

## License

BSD License