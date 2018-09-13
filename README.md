# Camelot: PDF Table Parsing for Humans

![license](https://img.shields.io/badge/license-MIT-lightgrey.svg) ![python-version](https://img.shields.io/badge/python-2.7-blue.svg)

**Camelot** is a Python library which makes it easy for *anyone* to extract tables from PDF files!

---

**Here's how you can extract tables from PDF files.** Check out the PDF used in this example, [here](docs/_static/pdf/foo.pdf).

<pre>
>>> import camelot
>>> tables = camelot.read_pdf('foo.pdf', mesh=True)
>>> tables
&lt;TableList tables=1&gt;
>>> tables.export('foo.csv', f='csv', compress=True) # json, excel, html
>>> tables[0]
&lt;Table shape=(7, 7)&gt;
>>> tables[0].parsing_report
{
    'accuracy': 99.02,
    'whitespace': 12.24,
    'order': 1,
    'page': 1
}
>>> tables[0].to_csv('foo.csv') # to_json, to_excel, to_html
>>> tables[0].df # get a pandas DataFrame!
</pre>

| Cycle Name | KI (1/km) | Distance (mi) | Percent Fuel Savings |                 |                 |                |
|------------|-----------|---------------|----------------------|-----------------|-----------------|----------------|
|            |           |               | Improved Speed       | Decreased Accel | Eliminate Stops | Decreased Idle |
| 2012_2     | 3.30      | 1.3           | 5.9%                 | 9.5%            | 29.2%           | 17.4%          |
| 2145_1     | 0.68      | 11.2          | 2.4%                 | 0.1%            | 9.5%            | 2.7%           |
| 4234_1     | 0.59      | 58.7          | 8.5%                 | 1.3%            | 8.5%            | 3.3%           |
| 2032_2     | 0.17      | 57.8          | 21.7%                | 0.3%            | 2.7%            | 1.2%           |
| 4171_1     | 0.07      | 173.9         | 58.1%                | 1.6%            | 2.1%            | 0.5%           |

There's a [command-line interface]() too!

## Why Camelot?

- **You are in control**: Unlike other libraries and tools which either give a nice output or fail miserably (with no in-between), Camelot gives you the power to tweak table extraction. (Since everything in the real world, including PDF table extraction, is fuzzy.)
- **Metrics**: *Bad* tables can be discarded based on metrics like accuracy and whitespace, without ever having to manually look at each table.
- Each table is a **pandas DataFrame**, which enables seamless integration into data analysis workflows.
- **Export** to multiple formats, including json, excel and html.
- Simple and Elegant API, written in **Python**!

## Installation

After [installing the dependencies](), you can simply use pip to install Camelot:

<pre>
$ pip install camelot-py
</pre>

## Documentation

The documentation is available at [link]().

## Development

The [contribution guidelines](CONTRIBUTING.md) has detailed information about contributing code, documentation, tests and more. We've included some basic information in this README.

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