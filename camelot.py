#!/usr/bin/env python2
import os
import re
import csv
import sys
import glob
import time
import shutil
import logging
import zipfile
import tempfile
import subprocess
from docopt import docopt
from werkzeug.utils import secure_filename

from lattice import lattice
from stream import stream


doc = """
camelot parses tables from PDFs!

usage:
 camelot.py [options] <method> [<args>...]

options:
 -h, --help                Show this screen.
 -v, --version             Show version.
 -p, --pages <pageno>      Comma-separated list of page numbers.
                           Example: -p 1,3-6,10  [default: 1]
 -f, --format <format>     Output format. (csv,xlsx) [default: csv]
 -l, --log                 Print log to file.
 -o, --output <directory>  Output directory.

camelot methods:
 lattice  Looks for lines between data.
 stream   Looks for spaces between data.

See 'camelot <method> -h' for more information on a specific method.
"""

lattice_doc = """
Lattice method looks for lines between data to form a table.

usage:
 camelot.py lattice [options] [--] <file>

options:
 -F, --fill <fill>      Fill data in horizontal and/or vertical spanning
                        cells. Example: -F h, -F v, -F hv
 -s, --scale <scale>    Scaling factor. Large scaling factor leads to
                        smaller lines being detected. [default: 15]
 -j, --jtol <jtol>      Tolerance to account for when comparing joint
                        and line coordinates. [default: 2]
 -m, --mtol <mtol>      Tolerance to account for when merging lines
                        which are very close. [default: 2]
 -i, --invert           Invert pdf image to make sure that lines are
                        in foreground.
 -d, --debug <debug>    Debug by visualizing pdf geometry.
                        (contour,line,joint,table) Example: -d table
"""

stream_doc = """
Stream method looks for spaces between data to form a table.

usage:
 camelot.py stream [options] [--] <file>

options:
 -n, --ncols <ncols>      Number of columns. [default: 0]
 -c, --columns <columns>  Comma-separated list of column x-coordinates.
                          Example: -c 10.1,20.2,30.3
 -M, --cmargin <cmargin>  Char margin. Chars closer than cmargin are
                          grouped together to form a word. [default: 2.0]
 -L, --lmargin <lmargin>  Line margin. Lines closer than lmargin are
                          grouped together to form a textbox. [default: 0.5]
 -W, --wmargin <wmargin>  Word margin. Insert blank spaces between chars
                          if distance between words is greater than word
                          margin. [default: 0.1]
 -d, --debug              Debug by visualizing textboxes.
"""

pno = re.compile(r'\d+')


def filesort(filepath):
    filename = os.path.basename(filepath)
    num = pno.findall(filename)
    if len(num) == 2:
        return (int(num[0]), int(num[1]))
    else:
        return (int(num[0]), 0)


if __name__ == '__main__':
    start_time = time.time()
    tmpdir = tempfile.mkdtemp()

    args = docopt(doc, version='0.1', options_first=True)
    argv = [args['<method>']] + args['<args>']
    if args['<method>'] == 'lattice':
        args.update(docopt(lattice_doc, argv=argv))
    elif args['<method>'] == 'stream':
        args.update(docopt(stream_doc, argv=argv))

    if args['--pages']:
        if args['--pages'] == ['all']:
            p = args['--pages']
        else:
            p = []
            for r in args['--pages'].split(','):
                if '-' in r:
                    a, b = r.split('-')
                    a, b = int(a), int(b)
                    p.extend([str(i) for i in range(a, b + 1)])
                else:
                    p.extend([str(r)])
    else:
        p = ['1']
    p = sorted(set(p))

    fname = os.path.basename(args['<file>'])
    fname = secure_filename(fname)
    fdir = os.path.dirname(args['<file>'])
    froot, fext = os.path.splitext(fname)
    if fext.lower() != '.pdf':
        print "camelot can parse only pdfs right now"
        shutil.rmtree(tmpdir)
        sys.exit()

    logfname = os.path.join(tmpdir, froot + '.log')
    logging.basicConfig(filename=logfname, filemode='w', level=logging.DEBUG)

    shutil.copy(args['<file>'], os.path.join(tmpdir, fname))
    print "separating pdf into pages"
    print
    if p == ['all']:
        subprocess.call(['pdfseparate', os.path.join(tmpdir, fname), os.path.join(tmpdir,
                        'pg-%d.pdf')])
    else:
        for page in p:
            subprocess.call(['pdfseparate', '-f', page, '-l', page, os.path.join(tmpdir, fname),
                            os.path.join(tmpdir, 'pg-%s.pdf' % page)])

    glob_pdf = sorted(glob.glob(os.path.join(tmpdir, 'pg-*.pdf')))
    if args['<method>'] == 'lattice':
        print "using the lattice method"
        for g in glob_pdf:
            g_fname = os.path.basename(g)
            print "working on", g_fname
            g_froot, __ = os.path.splitext(g)
            try:
                data = lattice(g, f=args['--fill'], s=int(args['--scale']),
                               jtol=int(args['--jtol']), mtol=int(args['--mtol']),
                               invert=args['--invert'], debug=args['--debug'])
                if data is None:
                    print
                    continue
                for k in sorted(data.keys()):
                    csvfile = g_froot + '_%s.csv' % k
                    with open(csvfile, 'w') as outfile:
                        writer = csv.writer(outfile)
                        for d in data[k]:
                            writer.writerow([c.encode('utf-8') for c in d])
                        print "saved as", os.path.basename(csvfile)
                print
            except Exception:
                logging.exception("")
                print "couldn't parse", g_fname, "see log for more info"
                print
    elif args['<method>'] == 'stream':
        print "using the stream method"
        for g in glob_pdf:
            g_fname = os.path.basename(g)
            print "working on", g_fname
            g_froot, __ = os.path.splitext(g)
            try:
                data = stream(g, ncolumns=int(args['--ncols']), columns=args['--columns'],
                              char_margin=float(args['--cmargin']),
                              line_margin=float(args['--lmargin']),
                              word_margin=float(args['--wmargin']),
                              debug=args['--debug'])
                if data is None:
                    print
                    continue
                csvfile = g_froot + '.csv'
                with open(csvfile, 'w') as outfile:
                    writer = csv.writer(outfile)
                    for d in data:
                        writer.writerow([c.encode('utf-8') for c in d])
                    print "saved as", os.path.basename(csvfile)
                    print
            except Exception:
                logging.exception("")
                print "couldn't parse", g_fname, "see log for more info"
                print

    if args['--log']:
        if args['--output']:
            shutil.copy(logfname, args['--output'])
        else:
            shutil.copy(logfname, fdir)

    if args['--debug'] not in [None, False]:
        print "See 'camelot <method> -h' for various parameters you can tweak."
        shutil.rmtree(tmpdir)
        sys.exit()

    glob_csv = sorted(glob.glob(os.path.join(tmpdir, '*.csv')), key=filesort)
    if args['--format'] == 'csv':
        if len(glob_csv) == 1:
            if args['--output']:
                shutil.copy(glob_csv[0], args['--output'])
            else:
                shutil.copy(glob_csv[0], fdir)
        else:
            zipname = froot + '.zip'
            zippath = os.path.join(tmpdir, zipname)
            print "zipping 'em up"
            with zipfile.ZipFile(zippath, 'a', zipfile.ZIP_DEFLATED) as myzip:
                for g in glob_csv:
                    myzip.write(g, os.path.join(froot, os.path.basename(g)))
            if args['--output']:
                shutil.copy(zippath, args['--output'])
            else:
                shutil.copy(zippath, fdir)
            print
    elif args['--format'] == 'xlsx':
        from pyexcel_xlsx import save_data
        from collections import OrderedDict
        data = OrderedDict()
        for c in glob_csv:
            c_fname = os.path.basename(c)
            c_froot, __ = os.path.splitext(c)
            print "adding", c_fname, "to excel file"
            with open(c, 'r') as csvfile:
                reader = csv.reader(csvfile)
                c_froot, __ = os.path.splitext(c_fname)
                data.update({c_froot: [row for row in reader]})
        xlsxname = froot + '.xlsx'
        xlsxpath = os.path.join(tmpdir, xlsxname)
        save_data(xlsxpath, data)
        if args['--output']:
            shutil.copy(xlsxpath, args['--output'])
        else:
            shutil.copy(xlsxpath, fdir)
        print
        print "saved as", xlsxname

    print "cleaning up..."
    shutil.rmtree(tmpdir)

    print "finished in", time.time() - start_time, "seconds"
    logging.info("Time taken for " + fname + ": " +
                 str(time.time() - start_time) + " seconds")
