# Camelot: PDF Table Parsing for Humans

Camelot is a Python 2.7 library and command-line tool for extracting tabular data from PDF files.

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

## Dependencies

The dependencies include [tk](https://wiki.tcl.tk/3743) and [ghostscript](https://www.ghostscript.com/).

## Installation

Make sure you have the most updated versions for `pip` and `setuptools`. You can update them by

<pre>
pip install -U pip setuptools
</pre>

### Installing dependencies

tk and ghostscript can be installed using your system's default package manager.

#### Linux

* Ubuntu

<pre>
sudo apt-get install python-tk ghostscript
</pre>

* Arch Linux

<pre>
sudo pacman -S tk ghostscript
</pre>

#### OS X

<pre>
brew install tcl-tk ghostscript
</pre>

Finally, `cd` into the project directory and install by

<pre>
python setup.py install
</pre>

## Development

### Code

You can check the latest sources with the command:

<pre>
git clone https://github.com/socialcopsdev/camelot.git
</pre>

### Contributing

See [Contributing guidelines]().

### Testing

<pre>
python setup.py test
</pre>

## License

BSD License
