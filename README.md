# Camelot: PDF Table Parsing for Humans

![license](https://img.shields.io/badge/license-MIT-lightgrey.svg) ![python-version](https://img.shields.io/badge/python-2.7-blue.svg)

**Camelot** is a Python library which makes it easy for *anyone* to extract tables from PDF files!

## Usage

<pre>
>>> import camelot
>>> tables = camelot.read_pdf('foo.pdf')
>>> tables
&lt;TableList n=2&gt;
>>> tables.export('foo.csv', f='csv', compress=True) # json, excel, html
>>> tables[0]
&lt;Table shape=(3,4)&gt;
>>> tables[0].parsing_report
{
    'accuracy': 96,
    'whitespace': 80,
    'order': 1,
    'page': 1
}
>>> tables[0].to_csv('foo.csv') # to_json, to_excel, to_html
>>> tables[0].df # get a pandas DataFrame!
</pre>

There's a [command-line interface]() too!

## Why Camelot?

- **You are in control**: Unlike other libraries and tools which either give a nice output or fail miserably (with no in-between), Camelot gives you the power to tweak table extraction. (Since everything in the real world, including PDF table extraction, is fuzzy.)
- **Metrics**: *Bad* tables can be discarded based on metrics like accuracy and whitespace, without ever having to manually look at each table.
- Each table is a pandas DataFrame, which enables seamless integration into data analysis workflows.
- Export to multiple formats, including json, excel and html.
- Simple and Elegant API, written in Python!

## Installation

After [installing dependencies](), you can simply use pip:

<pre>
$ pip install camelot-py
</pre>

## Documentation

Th documentation is available at [link]().

## Development

The [Contributor's Guide]() has detailed information about contributing code, documentation, tests and more. We've included some basic information in this README.

### Source code

You can check the latest sources with the command:

<pre>
$ git clone https://www.github.com/socialcopsdev/camelot.git
</pre>

### Setting up development environment

You can install the development dependencies with the command:

<pre>
$ pip install camelot-py[dev]
</pre>

### Testing

After installation, you can run tests using:

<pre>
$ python setup.py test
</pre>

## License

This project is licensed under the [MIT License](LICENSE).