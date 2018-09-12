# Camelot: PDF Table Parsing for Humans

Camelot is a Python library and command-line tool for extracting tables from PDF files.

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
>>> tables[0].df # get a pandas dataframe!
</pre>

There's a [command-line tool]() too!

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