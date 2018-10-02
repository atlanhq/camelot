# -*- coding: utf-8 -*-

import os

from click.testing import CliRunner

from camelot.cli import cli
from camelot.utils import TemporaryDirectory


testdir = os.path.dirname(os.path.abspath(__file__))
testdir = os.path.join(testdir, 'files')


def test_cli_lattice():
    with TemporaryDirectory() as tempdir:
        infile = os.path.join(testdir, 'foo.pdf')
        outfile = os.path.join(tempdir, 'foo.csv')
        runner = CliRunner()
        result = runner.invoke(cli, ['--format', 'csv', '--output', outfile,
                                     'lattice', infile])
        assert result.exit_code == 0
        assert result.output == 'Found 1 tables\n'


def test_cli_stream():
    with TemporaryDirectory() as tempdir:
        infile = os.path.join(testdir, 'budget.pdf')
        outfile = os.path.join(tempdir, 'budget.csv')
        runner = CliRunner()
        result = runner.invoke(cli, ['--format', 'csv', '--output', outfile,
                                     'stream', infile])
        assert result.exit_code == 0
        assert result.output == 'Found 1 tables\n'