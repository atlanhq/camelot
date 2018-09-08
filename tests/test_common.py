import os

import pandas as pd

import camelot

from test_data import *

testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, "files")


def test_stream():
    pass


def test_stream_table_rotated():
    df = pd.DataFrame(data_stream_table_rotated)

    filename = os.path.join(testdir, "clockwise_table_2.pdf")
    tables = camelot.read_pdf(filename)
    assert df.equals(tables[0].df)

    filename = os.path.join(testdir, "anticlockwise_table_2.pdf")
    tables = camelot.read_pdf(filename)
    assert df.equals(tables[0].df)


def test_stream_table_area():
    df = pd.DataFrame(data_stream_table_area_single)

    filename = os.path.join(testdir, "tabula/us-007.pdf")
    tables = camelot.read_pdf(filename, table_area=["320,500,573,335"])
    assert df.equals(tables[0].df)


def test_stream_columns():
    df = pd.DataFrame(data_stream_columns)

    filename = os.path.join(testdir, "mexican_towns.pdf")
    tables = camelot.read_pdf(
        filename, columns=["67,180,230,425,475"], row_close_tol=10)
    assert df.equals(tables[0].df)


def test_lattice():
    df = pd.DataFrame(data_lattice)

    filename = os.path.join(testdir,
        "tabula/icdar2013-dataset/competition-dataset-us/us-030.pdf")
    tables = camelot.read_pdf(filename, pages="2", mesh=True)
    assert df.equals(tables[0].df)


def test_lattice_table_rotated():
    df = pd.DataFrame(data_lattice_table_rotated)

    filename = os.path.join(testdir, "clockwise_table_1.pdf")
    tables = camelot.read_pdf(filename, mesh=True)
    assert df.equals(tables[0].df)

    filename = os.path.join(testdir, "anticlockwise_table_1.pdf")
    tables = camelot.read_pdf(filename, mesh=True)
    assert df.equals(tables[0].df)


def test_lattice_process_background():
    df = pd.DataFrame(data_lattice_process_background)

    filename = os.path.join(testdir, "background_lines_1.pdf")
    tables = camelot.read_pdf(filename, mesh=True, process_background=True)
    assert df.equals(tables[1].df)


def test_lattice_copy_text():
    df = pd.DataFrame(data_lattice_copy_text)

    filename = os.path.join(testdir, "row_span_1.pdf")
    tables = camelot.read_pdf(filename, mesh=True, line_size_scaling=60, copy_text="v")
    assert df.equals(tables[0].df)