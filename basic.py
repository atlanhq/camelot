import os
import csv
import numpy as np

from pdf import get_pdf_info


def overlap(l):
    merged = []
    for higher in l:
        if not merged:
            merged.append(higher)
        else:
            lower = merged[-1]
            if higher[0] <= lower[1]:
                upper_bound = max(lower[1], higher[1])
                lower_bound = min(lower[0], higher[0])
                merged[-1] = (lower_bound, upper_bound)
            else:
                merged.append(higher)
    return merged


def get_row_idx(t, rows):
    for r in range(len(rows)):
        if t.y1 <= rows[r][0] and t.y0 >= rows[r][1]:
            return r


def get_column_idx(t, columns):
    for c in range(len(columns)):
        if t.x0 >= columns[c][0] and t.x1 <= columns[c][1]:
            return c


def basic(pdf_dir, filename):
    print "working on", filename
    text, _, _ = get_pdf_info(os.path.join(pdf_dir, filename), 'basic')
    text.sort(key=lambda x: (-x.y0, x.x0))
    y_last = 0
    data = []
    temp = []
    elements = []
    for t in text:
        # is checking for upright necessary?
        # if t.get_text().strip() and all([obj.upright for obj in t._objs if
        # type(obj) is LTChar]):
        if t.get_text().strip():
            if not np.isclose(y_last, t.y0, atol=2):
                y_last = t.y0
                elements.append(len(temp))
                data.append(temp)
                temp = []
            temp.append(t)
    # a table can't have just 1 column, can it?
    elements = filter(lambda x: x != 1, elements)
    # mode = int(sys.argv[2]) if sys.argv[2] else max(set(elements), key=elements.count)
    mode = max(set(elements), key=elements.count)
    columns = [(t.x0, t.x1) for d in data for t in d if len(d) == mode]
    columns = overlap(sorted(columns))
    columns = [(c[0] + c[1]) / 2.0 for c in columns]

    output = [['' for c in columns] for d in data]
    for row, d in enumerate(data):
        for t in d:
            cog = (t.x0 + t.x1) / 2.0
            diff = [(i, abs(cog - c)) for i, c in enumerate(columns)]
            idx = min(diff, key=lambda x: x[1])
            if output[row][idx[0]]:
                output[row][idx[0]] += ' ' + t.get_text().strip()
            else:
                output[row][idx[0]] = t.get_text().strip()

    csvname = filename.split('.')[0] + '.csv'
    csvpath = os.path.join(pdf_dir, csvname)
    with open(csvpath, 'w') as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_ALL)
        for row in output:
            writer.writerow([cell.encode('utf-8') for cell in row])
