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

        result = runner.invoke(cli, ['--format', 'csv',
                                     'lattice', infile])
        output_error = 'Error: Please specify output file path using --output'
        assert output_error in result.output

        result = runner.invoke(cli, ['--output', outfile,
                                     'lattice', infile])
        format_error = 'Please specify output file format using --format'
        assert format_error in result.output


def test_cli_stream():
    with TemporaryDirectory() as tempdir:
        infile = os.path.join(testdir, 'budget.pdf')
        outfile = os.path.join(tempdir, 'budget.csv')
        runner = CliRunner()
        result = runner.invoke(cli, ['--format', 'csv', '--output', outfile,
                                     'stream', infile])
        assert result.exit_code == 0
        assert result.output == 'Found 1 tables\n'

        result = runner.invoke(cli, ['--format', 'csv', 'stream', infile])
        output_error = 'Error: Please specify output file path using --output'
        assert output_error in result.output

        result = runner.invoke(cli, ['--output', outfile, 'stream', infile])
        format_error = 'Please specify output file format using --format'
        assert format_error in result.output
