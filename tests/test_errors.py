# -*- coding: utf-8 -*-

import os

import pytest

import camelot


testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, "files")


def test_unknown_flavor():
    message = ("Unknown flavor specified."
               " Use either 'lattice' or 'stream'")
    with pytest.raises(NotImplementedError, message=message):
        filename = os.path.join(testdir, "assam.pdf")
        tables = camelot.read_pdf(filename, flavor="chocolate")