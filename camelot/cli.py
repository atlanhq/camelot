# -*- coding: utf-8 -*-
from pprint import pprint

import click

from .io import read_pdf
from .plotting import plot_geometry
from .utils import validate_input, remove_extra


class Mutex(click.Option):
    def handle_parse_result(self, ctx, opts, args):
        mesh = opts.get('mesh', False)
        geometry_type = opts.get('geometry_type', False)
        validate_input(opts, mesh=mesh, geometry_type=geometry_type)
        return super(Mutex, self).handle_parse_result(ctx, opts, args)


@click.command()
@click.option("-p", "--pages", default="1", help="")
@click.option("-o", "--output", help="")
@click.option("-f", "--format",
              type=click.Choice(["csv", "json", "excel", "html"]), help="")
@click.option("-z", "--zip", is_flag=True, help="")
@click.option("-m", "--mesh", is_flag=True, help="Whether or not to"
              "use Lattice method of parsing. Stream is used by default.")
@click.option("-G", "--geometry_type",
              type=click.Choice(["text", "table", "contour", "joint", "line"]),
              help="Plot geometry found on pdf page for debugging.")
@click.option("-T", "--table_area", default=[], multiple=True,
              help="")
@click.option("-split", "--split_text", is_flag=True, help="")
@click.option("-flag", "--flag_size", is_flag=True, help="")
@click.option("-M", "--margins", nargs=3, default=(1.0, 0.5, 0.1),
              help="")
@click.option("-C", "--columns", default=[], multiple=True, cls=Mutex,
              help="")
@click.option("-r", "--row_close_tol", default=2, cls=Mutex, help="")
@click.option("-c", "--col_close_tol", default=0, cls=Mutex, help="")
@click.option("-back", "--process_background", is_flag=True, cls=Mutex,
              help="Use with --mesh")
@click.option("-scale", "--line_size_scaling", default=15, cls=Mutex,
              help="Use with --mesh")
@click.option("-copy", "--copy_text", default=[], cls=Mutex,
              help="Use with --mesh")
@click.option("-shift", "--shift_text", default=["l", "t"], cls=Mutex,
              help="Use with --mesh")
@click.option("-l", "--line_close_tol", default=2, cls=Mutex,
              help="Use with --mesh")
@click.option("-j", "--joint_close_tol", default=2, cls=Mutex,
              help="Use with --mesh")
@click.option("-block", "--threshold_blocksize", default=15, cls=Mutex,
              help="Use with --mesh")
@click.option("-const", "--threshold_constant", default=-2, cls=Mutex,
              help="Use with --mesh")
@click.option("-I", "--iterations", default=0, cls=Mutex,
              help="Use with --mesh")
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

    kwargs = remove_extra(kwargs, mesh=mesh)
    if geometry_type is None:
        tables = read_pdf(filepath, pages=pages, mesh=mesh, **kwargs)
        click.echo(tables)
        if output is None:
            raise click.UsageError("Please specify an output filepath using --output")
        if f is None:
            raise click.UsageError("Please specify an output format using --format")
        tables.export(output, f=f, compress=compress)
    else:
        plot_geometry(filepath, pages=pages, mesh=mesh,
                      geometry_type=geometry_type, **kwargs)