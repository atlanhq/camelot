# -*- coding: utf-8 -*-

import os

from click import UsageError
from click.testing import CliRunner
import pytest

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

        result = runner.invoke(cli, ['--format', 'csv', 'lattice', infile])
        assert 'Error: Please specify output file path using --output' in result.output

        result = runner.invoke(cli, ['--output', outfile, 'lattice', infile])
        assert 'Please specify output file format using --format' in result.output


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
        assert 'Error: Please specify output file path using --output' in result.output

        result = runner.invoke(cli, ['--output', outfile, 'stream', infile])
        assert 'Please specify output file format using --format' in result.output
