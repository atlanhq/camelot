.. _cli:

Command-line interface
======================

Camelot comes with a command-line interface.

You can print the help for the interface, by typing ``camelot --help`` in your favorite terminal program, as shown below. Furthermore, you can print the help for each command, by typing ``camelot <command> --help``, try it out!

::

  $ camelot --help
  Usage: camelot [OPTIONS] COMMAND [ARGS]...

  Options:
    --version                       Show the version and exit.
    -p, --pages TEXT                Comma-separated page numbers to parse.
                                    Example: 1,3,4 or 1,4-end
    -o, --output TEXT               Output filepath.
    -f, --format [csv|json|excel|html]
                                    Output file format.
    -z, --zip                       Whether or not to create a ZIP archive.
    -split, --split_text            Whether or not to split text if it spans
                                    across multiple cells.
    -flag, --flag_size              (inactive) Whether or not to flag text which
                                    has uncommon size. (Useful to detect
                                    super/subscripts)
    -M, --margins <FLOAT FLOAT FLOAT>...
                                    char_margin, line_margin, word_margin for
                                    PDFMiner.
    --help                          Show this message and exit.

  Commands:
    lattice  Use lines between text to parse table.
    stream   Use spaces between text to parse table.