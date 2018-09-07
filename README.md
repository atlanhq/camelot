# Camelot: PDF Table Parsing for Humans

Camelot is a Python 2.7 library and command-line tool for getting tables out of PDF files.

## Usage

<pre>
>>> import camelot
>>> tables = camelot.read_pdf("foo.pdf")
>>> tables
&lt;TableList n=2&gt;
>>> tables.export("foo.csv", f="csv", compress=True) # json, excel, html
>>> tables[0]
&lt;Table shape=(3,4)&gt;
>>> tables[0].to_csv("foo.csv") # to_json, to_excel, to_html
>>> tables[0].parsing_report
{
    "accuracy": 96,
    "whitespace": 80,
    "order": 1,
    "page": 1
}
>>> df = tables[0].df
</pre>

Camelot comes with a CLI where you can specify page numbers, output format, output directory etc. By default, the output files are placed in the same directory as the PDF.

<pre>
Camelot: PDF parsing made simpler!

usage:
 camelot [options] &lt;method&gt; [&lt;args&gt;...]

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
 -J, --split_text          Split text lines if they span across multiple cells.
 -K, --flag_size           Flag substring if its size differs from the whole string.
                           Useful for super and subscripts.
 -X, --print-stats         List stats on the parsing process.
 -Y, --save-stats          Save stats to a file.
 -Z, --plot &lt;dist&gt;         Plot distributions. (page,all,rc)

camelot methods:
 lattice  Looks for lines between data.
 stream   Looks for spaces between data.

See 'camelot &lt;method&gt; -h' for more information on a specific method.
</pre>

## Dependencies

Currently, camelot works under Python 2.7.

The required dependencies include [numpy](http://www.numpy.org/), [OpenCV](http://opencv.org/) and [ghostscript](https://www.ghostscript.com/).

## Installation

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them by

<pre>
pip install -U pip setuptools
</pre>

### Installing dependencies

numpy can be install using `pip`. OpenCV and ghostscript can be installed using your system's default package manager.

#### Linux

* Arch Linux

<pre>
sudo pacman -S opencv tk ghostscript
</pre>

* Ubuntu

<pre>
sudo apt-get install python-opencv python-tk ghostscript
</pre>

#### OS X

<pre>
brew install homebrew/science/opencv ghostscript
</pre>

Finally, `cd` into the project directory and install by

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
