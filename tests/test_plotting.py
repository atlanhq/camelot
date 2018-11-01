# -*- coding: utf-8 -*-

import camelot
import os
import pytest

from camelot.plotting import *


testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, "files")


@pytest.mark.mpl_image_compare(
    baseline_dir="files/baseline_plots", tolerance=15)
def test_text_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    return plot_text(tables[0]._text)


@pytest.mark.mpl_image_compare(
    baseline_dir="files/baseline_plots", tolerance=15)
def test_contour_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    return plot_contour(tables[0]._image)


@pytest.mark.mpl_image_compare(
    baseline_dir="files/baseline_plots", tolerance=15)
def test_table_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    return plot_table(tables[0])


@pytest.mark.mpl_image_compare(
    baseline_dir="files/baseline_plots", tolerance=15)
def test_line_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    return plot_line(tables[0]._segments)


@pytest.mark.mpl_image_compare(
    baseline_dir="files/baseline_plots", tolerance=15)
def test_joint_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    return plot_joint(tables[0]._image)
