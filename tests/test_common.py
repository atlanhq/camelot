# -*- coding: utf-8 -*-

import os

import pandas as pd

import camelot

from .data import *

testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, "files")


def test_parsing_report():
    parsing_report = {
        'accuracy': 99.02,
        'whitespace': 12.24,
        'order': 1,
        'page': 1
    }

    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    assert tables[0].parsing_report == parsing_report


def test_stream():
    df = pd.DataFrame(data_stream)

    filename = os.path.join(testdir, "health.pdf")
    tables = camelot.read_pdf(filename, flavor="stream")
    assert df.equals(tables[0].df)


def test_stream_table_rotated():
    df = pd.DataFrame(data_stream_table_rotated)

    filename = os.path.join(testdir, "clockwise_table_2.pdf")
    tables = camelot.read_pdf(filename, flavor="stream")
    assert df.equals(tables[0].df)

    filename = os.path.join(testdir, "anticlockwise_table_2.pdf")
    tables = camelot.read_pdf(filename, flavor="stream")
    assert df.equals(tables[0].df)


def test_stream_table_area():
    df = pd.DataFrame(data_stream_table_area)

    filename = os.path.join(testdir, "tabula/us-007.pdf")
    tables = camelot.read_pdf(filename, flavor="stream", table_area=["320,500,573,335"])
    assert df.equals(tables[0].df)


def test_stream_columns():
    df = pd.DataFrame(data_stream_columns)

    filename = os.path.join(testdir, "mexican_towns.pdf")
    tables = camelot.read_pdf(
        filename, flavor="stream", columns=["67,180,230,425,475"], row_close_tol=10)
    assert df.equals(tables[0].df)


def test_stream_split_text():
    df = pd.DataFrame(data_stream_split_text)

    filename = os.path.join(testdir, "tabula/m27.pdf")
    tables = camelot.read_pdf(
        filename, flavor="stream", columns=["72,95,209,327,442,529,566,606,683"], split_text=True)
    assert df.equals(tables[0].df)


def test_stream_flag_size():
    df = pd.DataFrame(data_stream_flag_size)

    filename = os.path.join(testdir, "superscript.pdf")
    tables = camelot.read_pdf(filename, flavor="stream", flag_size=True)
    assert df.equals(tables[0].df)


def test_lattice():
    df = pd.DataFrame(data_lattice)

    filename = os.path.join(testdir,
        "tabula/icdar2013-dataset/competition-dataset-us/us-030.pdf")
    tables = camelot.read_pdf(filename, pages="2")
    assert df.equals(tables[0].df)


def test_lattice_table_rotated():
    df = pd.DataFrame(data_lattice_table_rotated)

    filename = os.path.join(testdir, "clockwise_table_1.pdf")
    tables = camelot.read_pdf(filename)
    assert df.equals(tables[0].df)

    filename = os.path.join(testdir, "anticlockwise_table_1.pdf")
    tables = camelot.read_pdf(filename)
    assert df.equals(tables[0].df)


def test_lattice_table_area():
    df = pd.DataFrame(data_lattice_table_area)

    filename = os.path.join(testdir, "twotables_2.pdf")
    tables = camelot.read_pdf(filename, table_area=["80,693,535,448"])
    assert df.equals(tables[0].df)


def test_lattice_process_background():
    df = pd.DataFrame(data_lattice_process_background)

    filename = os.path.join(testdir, "background_lines_1.pdf")
    tables = camelot.read_pdf(filename, process_background=True)
    assert df.equals(tables[1].df)


def test_lattice_copy_text():
    df = pd.DataFrame(data_lattice_copy_text)

    filename = os.path.join(testdir, "row_span_1.pdf")
    tables = camelot.read_pdf(filename, line_size_scaling=60, copy_text="v")
    assert df.equals(tables[0].df)


def test_lattice_shift_text():
    df_lt = pd.DataFrame(data_lattice_shift_text_left_top)
    df_disable = pd.DataFrame(data_lattice_shift_text_disable)
    df_rb = pd.DataFrame(data_lattice_shift_text_right_bottom)

    filename = os.path.join(testdir, "column_span_2.pdf")
    tables = camelot.read_pdf(filename, line_size_scaling=40)
    assert df_lt.equals(tables[0].df)

    tables = camelot.read_pdf(filename, line_size_scaling=40, shift_text=[''])
    assert df_disable.equals(tables[0].df)

    tables = camelot.read_pdf(filename, line_size_scaling=40, shift_text=['r', 'b'])
    assert df_rb.equals(tables[0].df)


def test_repr():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    assert repr(tables) == "<TableList n=1>"
    assert repr(tables[0]) == "<Table shape=(7, 7)>"
    assert repr(tables[0].cells[0][0]) == "<Cell x1=120.478125 y1=218.415 x2=164.64 y2=233.89125>"
