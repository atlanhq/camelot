# -*- coding: utf-8 -*-

import logging

from click import HelpFormatter

from .__version__ import __version__
from .io import read_pdf
from .plotting import PlotMethods


def _write_usage(self, prog, args='', prefix='Usage: '):
    return self._write_usage('camelot', args, prefix=prefix)


# monkey patch click.HelpFormatter
HelpFormatter._write_usage = HelpFormatter.write_usage
HelpFormatter.write_usage = _write_usage

# set up logging
logger = logging.getLogger('camelot')

format_string = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(format_string, datefmt='%Y-%m-%dT%H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)

# instantiate plot method
plot = PlotMethods()
