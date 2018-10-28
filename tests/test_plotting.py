# -*- coding: utf-8 -*-

import camelot
import os
import pytest

import matplotlib.pyplot as plt

from camelot.plotting import *


testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, "files")


@pytest.mark.mpl_image_compare(baseline_dir="files/baseline_plots")
def test_text_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    text = tables[0]._text
    fig = plot_text(text)
    ax = fig.axes[0]
    xs, ys = [], []
    for t in text:
        xs.extend([t[0], t[2]])
        ys.extend([t[1], t[3]])
    assert ax.get_xlim() == (min(xs) - 10, max(xs) + 10)
    assert ax.get_ylim() == (min(ys) - 10, max(ys) + 10)
    assert len(ax.patches) == len(text)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="files/baseline_plots")
def test_contour_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    _, table_bbox = tables[0]._image
    fig = plot_contour(tables[0]._image)
    ax = fig.axes[0]
    assert len(ax.patches) == len(table_bbox.keys())
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="files/baseline_plots")
def test_table_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    cells = [cell for row in tables[0].cells for cell in row]
    num_lines = sum([sum([cell.left, cell.right, cell.top, cell.bottom]) for cell in cells])
    fig = plot_table(tables[0])
    ax = fig.axes[0]
    assert len(ax.lines) == num_lines
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="files/baseline_plots")
def test_line_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    vertical, horizontal = tables[0]._segments
    fig = plot_line(tables[0]._segments)
    ax = fig.axes[0]
    assert len(ax.lines) == len(vertical + horizontal)
    return fig


@pytest.mark.mpl_image_compare(baseline_dir="files/baseline_plots")
def test_joint_plot():
    filename = os.path.join(testdir, "foo.pdf")
    tables = camelot.read_pdf(filename)
    _, table_bbox = tables[0]._image
    fig = plot_joint(tables[0]._image)
    ax = fig.axes[0]
    assert len(ax.lines) == len(table_bbox.keys())
    return fig
