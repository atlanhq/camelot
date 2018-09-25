<p align="center">
   <img src="https://raw.githubusercontent.com/socialcopsdev/camelot/master/docs/_static/camelot.png" width="200">
</p>

# Camelot: PDF Table Extraction for Humans

![license](https://img.shields.io/badge/license-MIT-lightgrey.svg) ![python-version](https://img.shields.io/badge/python-2.7-blue.svg)

**Camelot** is a Python library which makes it easy for *anyone* to extract tables from PDF files!

---

**Here's how you can extract tables from PDF files.** Check out the PDF used in this example, [here](https://github.com/socialcopsdev/camelot/blob/master/docs/_static/pdf/foo.pdf).

<pre>
>>> import camelot
>>> tables = camelot.read_pdf('foo.pdf')
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

There's a [command-line interface](https://camelot-py.readthedocs.io/en/latest/user/cli.html) too!

## Why Camelot?

- **You are in control**: Unlike other libraries and tools which either give a nice output or fail miserably (with no in-between), Camelot gives you the power to tweak table extraction. (Since everything in the real world, including PDF table extraction, is fuzzy.)
- **Metrics**: *Bad* tables can be discarded based on metrics like accuracy and whitespace, without ever having to manually look at each table.
- Each table is a **pandas DataFrame**, which enables seamless integration into [ETL and data analysis workflows](https://gist.github.com/vinayak-mehta/e5949f7c2410a0e12f25d3682dc9e873).
- **Export** to multiple formats, including json, excel and html.

See [comparison with other PDF table extraction libraries and tools](https://github.com/socialcopsdev/camelot/wiki/Comparison-with-other-PDF-Table-Extraction-libraries-and-tools).

## Installation

After [installing the dependencies](https://camelot-py.readthedocs.io/en/latest/user/install.html) ([tk](https://packages.ubuntu.com/trusty/python-tk) and [ghostscript](https://www.ghostscript.com/)), you can simply use pip to install Camelot:

<pre>
$ pip install camelot-py
</pre>

### Alternatively

After [installing the dependencies](https://camelot-py.readthedocs.io/en/latest/user/install.html), clone the repo using:

<pre>
$ git clone https://www.github.com/socialcopsdev/camelot
</pre>

and install Camelot using pip:

<pre>
$ cd camelot
$ pip install .
</pre>

Note: Use a [virtualenv](https://virtualenv.pypa.io/en/stable/) if you don't want to affect your global Python installation.

## Documentation

Great documentation is available at [http://camelot-py.readthedocs.io/](http://camelot-py.readthedocs.io/).

## Development

The [Contributor's Guide](https://camelot-py.readthedocs.io/en/latest/dev/contributing.html) has detailed information about contributing code, documentation, tests and more. We've included some basic information in this README.

### Source code

You can check the latest sources with:

<pre>
$ git clone https://www.github.com/socialcopsdev/camelot
</pre>

### Setting up a development environment

You can install the development dependencies easily, using pip:

<pre>
$ pip install camelot-py[dev]
</pre>

### Testing

After installation, you can run tests using:

<pre>
$ python setup.py test
</pre>

## Versioning

Camelot uses [Semantic Versioning](https://semver.org/). For the available versions, see the tags on this repository.

## License

This project is licensed under the MIT License, see the [LICENSE](https://github.com/socialcopsdev/camelot/blob/master/LICENSE) file for details.