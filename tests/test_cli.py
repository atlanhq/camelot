# -*- coding: utf-8 -*-

import os

from click.testing import CliRunner

from camelot.__main__ import cli
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


def test_cli_output_format():
    with TemporaryDirectory() as tempdir:
        infile = os.path.join(testdir, 'health.pdf')
        outfile = os.path.join(tempdir, 'health.{}')
        runner = CliRunner()

        # json
        result = runner.invoke(cli, ['--format', 'json', '--output', outfile.format('json'),
                                     'stream', infile])
        assert result.exit_code == 0

        # excel
        result = runner.invoke(cli, ['--format', 'excel', '--output', outfile.format('xlsx'),
                                     'stream', infile])
        assert result.exit_code == 0

        # html
        result = runner.invoke(cli, ['--format', 'html', '--output', outfile.format('html'),
                                     'stream', infile])
        assert result.exit_code == 0

        # zip
        result = runner.invoke(cli, ['--zip', '--format', 'csv', '--output', outfile.format('csv'),
                                     'stream', infile])
        assert result.exit_code == 0

def test_cli_quiet_flag():
    with TemporaryDirectory() as tempdir:
        infile = os.path.join(testdir, 'blank.pdf')
        outfile = os.path.join(tempdir, 'blank.csv')
        runner = CliRunner()

        result = runner.invoke(cli, ['--format', 'csv', '--output', outfile,
                                     'stream', infile])
        assert 'No tables found on page-1' in result.output

        result = runner.invoke(cli, ['--quiet', '--format', 'csv',
                                     '--output', outfile, 'stream', infile])
        assert 'No tables found on page-1' not in result.output
