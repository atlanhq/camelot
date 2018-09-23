# -*- coding: utf-8 -*-
from pprint import pprint

import click

from . import __version__
from .io import read_pdf
from .utils import validate_input, remove_extra


@click.command()
@click.version_option(version=__version__)
@click.option("-p", "--pages", default="1", help="Comma-separated page numbers"
              " to parse. Example: 1,3,4 or 1,4-end")
@click.option("-o", "--output", help="Output filepath.")
@click.option("-f", "--format",
              type=click.Choice(["csv", "json", "excel", "html"]),
              help="Output file format.")
@click.option("-z", "--zip", is_flag=True, help="Whether or not to create a ZIP"
              " archive.")
@click.option("-T", "--table_area", default=[], multiple=True,
              help="Table areas (x1,y1,x2,y2) to process.\n"
              " x1, y1 -> left-top and x2, y2 -> right-bottom")
@click.option("-split", "--split_text", is_flag=True, help="Whether or not to"
              " split text if it spans across multiple cells.")
@click.option("-flag", "--flag_size", is_flag=True, help="(inactive) Whether or"
              " not to flag text which has uncommon size. (Useful to detect"
              " super/subscripts)")
@click.option("-M", "--margins", nargs=3, default=(1.0, 0.5, 0.1),
              help="char_margin, line_margin, word_margin for PDFMiner.")
@click.option("-G", "--geometry_type",
              type=click.Choice(["text", "table", "contour", "joint", "line"]),
              help="Plot geometry found on pdf page for debugging.\n\n"
              "text: Plot text objects. (Useful to get table_area and"
              " columns coordinates)\ntable: Plot parsed table.\n"
              "contour (with --mesh): Plot detected rectangles.\njoint (with --mesh): Plot detected line"
              " intersections.\nline (with --mesh): Plot detected lines.")
@click.argument("filepath", type=click.Path(exists=True))
def cli(*args, **kwargs):
    pages = kwargs.pop("pages")
    output = kwargs.pop("output")
    f = kwargs.pop("format")
    compress = kwargs.pop("zip")
    mesh = kwargs.pop("mesh")
    geometry_type = kwargs.pop("geometry_type")
    filepath = kwargs.pop("filepath")

    table_area = list(kwargs['table_area'])
    kwargs['table_area'] = None if not table_area else table_area
    columns = list(kwargs['columns'])
    kwargs['columns'] = None if not columns else columns
    copy_text = list(kwargs['copy_text'])
    kwargs['copy_text'] = None if not copy_text else copy_text
    kwargs['shift_text'] = list(kwargs['shift_text'])

    kwargs = remove_extra(kwargs, mesh=mesh)
    tables = read_pdf(filepath, pages=pages, mesh=mesh, **kwargs)
    click.echo(tables)
    if output is None:
        raise click.UsageError("Please specify an output filepath using --output")
    if f is None:
        raise click.UsageError("Please specify an output format using --format")
    tables.export(output, f=f, compress=compress)


@click.option("-T", "--table_area", default=[], multiple=True,
              help="Table areas (x1,y1,x2,y2) to process.\n"
              " x1, y1 -> left-top and x2, y2 -> right-bottom")
@click.option("-back", "--process_background", is_flag=True, cls=Mutex,
              help="(with --mesh) Whether or not to process lines that are in"
              " background.")
@click.option("-scale", "--line_size_scaling", default=15, cls=Mutex,
              help="(with --mesh) Factor by which the page dimensions will be"
              " divided to get smallest length of detected lines.")
@click.option("-copy", "--copy_text", default=[], type=click.Choice(["h", "v"]),
              multiple=True, cls=Mutex, help="(with --mesh) Specify direction"
              " in which text will be copied over in a spanning cell.")
@click.option("-shift", "--shift_text", default=["l", "t"],
              type=click.Choice(["", "l", "r", "t", "b"]), multiple=True, cls=Mutex,
              help="(with --mesh) Specify direction in which text in a spanning"
              " cell should flow.")
@click.option("-l", "--line_close_tol", default=2, cls=Mutex,
              help="(with --mesh) Tolerance parameter used to merge close vertical"
              " lines and close horizontal lines.")
@click.option("-j", "--joint_close_tol", default=2, cls=Mutex,
              help="(with --mesh) Tolerance parameter used to decide whether"
              " the detected lines and points lie close to each other.")
@click.option("-block", "--threshold_blocksize", default=15, cls=Mutex,
              help="(with --mesh) For adaptive thresholding, size of a pixel"
              " neighborhood that is used to calculate a threshold value for"
              " the pixel: 3, 5, 7, and so on.")
@click.option("-const", "--threshold_constant", default=-2, cls=Mutex,
              help="(with --mesh) For adaptive thresholding, constant subtracted"
              " from the mean or weighted mean.\nNormally, it is positive but"
              " may be zero or negative as well.")
@click.option("-I", "--iterations", default=0, cls=Mutex,
              help="(with --mesh) Number of times for erosion/dilation is"
              " applied.")
def lattice(*args, **kwargs):
    pass


@click.option("-T", "--table_area", default=[], multiple=True,
              help="Table areas (x1,y1,x2,y2) to process.\n"
              " x1, y1 -> left-top and x2, y2 -> right-bottom")
@click.option("-C", "--columns", default=[], multiple=True, cls=Mutex,
              help="x-coordinates of column separators.")
@click.option("-r", "--row_close_tol", default=2, cls=Mutex, help="Rows will be"
              " formed by combining text vertically within this tolerance.")
@click.option("-c", "--col_close_tol", default=0, cls=Mutex, help="Columns will"
              " be formed by combining text horizontally within this tolerance.")
def stream(*args, **kwargs):
    pass