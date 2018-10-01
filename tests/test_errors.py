# -*- coding: utf-8 -*-

import os

import pytest

import camelot


testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, "files")
filename = os.path.join(testdir, 'foo.pdf')


def test_unknown_flavor():
    message = ("Unknown flavor specified."
               " Use either 'lattice' or 'stream'")
    with pytest.raises(NotImplementedError, message=message):
        tables = camelot.read_pdf(filename, flavor='chocolate')


def test_input_kwargs():
    message = "columns cannot be used with flavor='lattice'"
    with pytest.raises(ValueError, message=message):
        tables = camelot.read_pdf(filename, columns=['10,20,30,40'])


def test_unsupported_format():
    message = 'File format not supported'
    filename = os.path.join(testdir, 'foo.csv')
    with pytest.raises(NotImplementedError, message=message):
        tables = camelot.read_pdf(filename)