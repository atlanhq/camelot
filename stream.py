import os
import numpy as np

from pdf import get_pdf_info


def overlap(l):
    """Groups overlapping columns and returns list with updated
    columns boundaries.

    Parameters
    ----------
    l : list
        List of column x-coordinates.

    Returns
    -------
    merged : list
        List of merged column x-coordinates.
    """
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


def stream(filepath, ncolumns=0, columns=None, char_margin=2.0,
           line_margin=0.5, word_margin=0.1, debug=False):
    """Stream algorithm

    Groups data returned by PDFMiner into rows and finds mode of the
    number of elements in each row to guess number of columns.

    Parameters
    ----------
    filepath : string

    ncolumns : int, default: 0, optional
        Number of columns.

    columns : string, default: None, optional
        Comma-separated list of column x-coordinates.

    char_margin : float, default: 2.0, optional
        Char margin. Chars closer than cmargin are grouped together
        to form a word.

    line_margin : float, default: 0.5, optional
        Line margin. Lines closer than lmargin are grouped together
        to form a textbox.

    word_margin : float, default: 0.1, optional
        Word margin. Insert blank spaces between chars if distance
        between words is greater than word margin.

    debug : bool, default: False, optional
        Debug by visualizing textboxes.

    Returns
    -------
    output : list
    """
    filename = os.path.basename(filepath)
    text, __, __ = get_pdf_info(filepath, method='stream', char_margin=char_margin,
                                line_margin=line_margin, word_margin=word_margin)
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

    if debug:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal')
        xs, ys = [], []
        for d in data:
            for t in d:
                xs.extend([t.x0, t.x1])
                ys.extend([t.y0, t.y1])
                ax.add_patch(
                    patches.Rectangle(
                        (t.x0, t.y0),
                        t.x1 - t.x0,
                        t.y1 - t.y0
                    )
                )
        ax.set_xlim(min(xs) - 10, max(xs) + 10)
        ax.set_ylim(min(ys) - 10, max(ys) + 10)
        plt.show()
        return None

    if columns:
        columns = columns.split(',')
        cols = [(float(columns[i]), float(columns[i + 1]))
                for i in range(0, len(columns) - 1)]
        cols = [(c[0] + c[1]) / 2.0 for c in cols]
    else:
        # a table can't have just 1 column, can it?
        elements = filter(lambda x: x != 1, elements)
        mode = ncolumns if ncolumns else max(set(elements), key=elements.count)
        cols = [(t.x0, t.x1) for d in data for t in d if len(d) == mode]
        cols = overlap(sorted(cols))
        cols = [(c[0] + c[1]) / 2.0 for c in cols]

    output = [['' for c in cols] for d in data]
    for row, d in enumerate(data):
        for t in d:
            cog = (t.x0 + t.x1) / 2.0
            diff = [(i, abs(cog - c)) for i, c in enumerate(cols)]
            if diff:
                idx = min(diff, key=lambda x: x[1])
            else:
                print "couldn't find a table on this page"
                return None
            if output[row][idx[0]]:
                output[row][idx[0]] += ' ' + t.get_text().strip()
            else:
                output[row][idx[0]] = t.get_text().strip()

    return output