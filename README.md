# camelot

Camelot is a Python 2.7 library and command-line tool for getting tables out of PDF files.

## Usage

<pre>
from camelot.pdf import Pdf
from camelot.lattice import Lattice

extractor = Lattice(Pdf("/path/to/pdf", pagenos=[{'start': 2, 'end': 4}]))
tables = extractor.get_tables()
</pre>

Camelot comes with a command-line tool in which you can specify the output format (csv, tsv, html, json, and xlsx), page numbers you want to parse and the output directory in which you want the output files to be placed. By default, the output files are placed in the same directory as the PDF.

<pre>
camelot parses tables from PDFs!

usage:
 camelot.py [options] <method> [<args>...]

options:
 -h, --help                      Show this screen.
 -v, --version                   Show version.
 -p, --pages &lt;pageno&gt;            Comma-separated list of page numbers.
                                 Example: -p 1,3-6,10  [default: 1]
 -f, --format &lt;format&gt;           Output format. (csv,tsv,html,json,xlsx) [default: csv]
 -l, --log                       Print log to file.
 -o, --output &lt;directory&gt;        Output directory.

camelot methods:
 lattice  Looks for lines between data.
 stream   Looks for spaces between data.

See 'camelot <method> -h' for more information on a specific method.
</pre>

## Dependencies

Currently, camelot works under Python 2.7.

The required dependencies include [numpy](http://www.numpy.org/), [OpenCV](http://opencv.org/) and [ImageMagick](http://www.imagemagick.org/script/index.php).

## Installation

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them by

<pre>
pip install -U pip, setuptools
</pre>

We strongly recommend that you use a [virtual environment](http://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation) to install Camelot. If you don't want to use a virtual environment, then skip the next section.

### Installing virtualenvwrapper

You'll need to install [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/).

<pre>
pip install virtualenvwrapper
</pre>

or
<pre>
sudo pip install virtualenvwrapper
</pre>

After installing virtualenvwrapper, add the following lines to your `.bashrc` and source it.

<pre>
export WORKON_HOME=$HOME/.virtualenvs
source /usr/bin/virtualenvwrapper.sh
</pre>

The path to `virtualenvwrapper.sh` could be different on your system.

Finally make a virtual environment using

<pre>
mkvirtualenv camelot
</pre>

### Installing dependencies

numpy can be install using pip.

<pre>
pip install numpy
</pre>

OpenCV and imagemagick can be installed using your system's default package manager.

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

If you're working in a virtualenv, you'll need to create a symbolic link for the OpenCV shared object file

<pre>
sudo ln -s /path/to/system/site-packages/cv2.so ~/path/to/virtualenv/site-packages/cv2.so
</pre>

Finally, `cd` into the project directory and install by doing

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