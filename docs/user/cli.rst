.. _cli:

Command-line interface
======================

::

  $ camelot --help
  Usage: camelot [OPTIONS] FILEPATH

  Options:
    -p, --pages TEXT                Comma-separated page numbers to parse.
                                    Example: 1,3,4 or 1,4-end
    -o, --output TEXT               Output filepath.
    -f, --format [csv|json|excel|html]
                                    Output file format.
    -z, --zip                       Whether or not to create a ZIP archive.
    -m, --mesh                      Whether or not to use Lattice method of
                                    parsing. Stream is used by default.
    -T, --table_area TEXT           Table areas (x1,y1,x2,y2) to process.
                                    x1, y1
                                    -> left-top and x2, y2 -> right-bottom
    -split, --split_text            Whether or not to split text if it spans
                                    across multiple cells.
    -flag, --flag_size              (inactive) Whether or not to flag text which
                                    has uncommon size. (Useful to detect
                                    super/subscripts)
    -M, --margins <FLOAT FLOAT FLOAT>...
                                    char_margin, line_margin, word_margin for
                                    PDFMiner.
    -C, --columns TEXT              x-coordinates of column separators.
    -r, --row_close_tol INTEGER     Rows will be formed by combining text
                                    vertically within this tolerance.
    -c, --col_close_tol INTEGER     Columns will be formed by combining text
                                    horizontally within this tolerance.
    -back, --process_background     (with --mesh) Whether or not to process
                                    lines that are in background.
    -scale, --line_size_scaling INTEGER
                                    (with --mesh) Factor by which the page
                                    dimensions will be divided to get smallest
                                    length of detected lines.
    -copy, --copy_text [h|v]        (with --mesh) Specify direction in which
                                    text will be copied over in a spanning cell.
    -shift, --shift_text [l|r|t|b]  (with --mesh) Specify direction in which
                                    text in a spanning cell should flow.
    -l, --line_close_tol INTEGER    (with --mesh) Tolerance parameter used to
                                    merge close vertical lines and close
                                    horizontal lines.
    -j, --joint_close_tol INTEGER   (with --mesh) Tolerance parameter used to
                                    decide whether the detected lines and points
                                    lie close to each other.
    -block, --threshold_blocksize INTEGER
                                    (with --mesh) For adaptive thresholding,
                                    size of a pixel neighborhood that is used to
                                    calculate a threshold value for the pixel:
                                    3, 5, 7, and so on.
    -const, --threshold_constant INTEGER
                                    (with --mesh) For adaptive thresholding,
                                    constant subtracted from the mean or
                                    weighted mean.
                                    Normally, it is positive but
                                    may be zero or negative as well.
    -I, --iterations INTEGER        (with --mesh) Number of times for
                                    erosion/dilation is applied.
    -G, --geometry_type [text|table|contour|joint|line]
                                    Plot geometry found on pdf page for
                                    debugging.
                                    text: Plot text objects. (Useful to get
                                          table_area and columns coordinates)
                                    table: Plot parsed table.
                                    contour (with --mesh): Plot detected rectangles.
                                    joint (with --mesh): Plot detected line intersections.
                                    line (with --mesh): Plot detected lines.
    --help                          Show this message and exit.