import numpy as np


def translate(x1, x2):
    """Translate coordinate x2 by x1.

    Parameters
    ----------
    x1 : float

    x2 : float

    Returns
    -------
    x2 : float
    """
    x2 += x1
    return x2


def scale(x, s):
    """Scale coordinate x by scaling factor s.

    Parameters
    ----------
    x : float

    s : float

    Returns
    -------
    x : float
    """
    x *= s
    return x


def rotate(x1, y1, x2, y2, angle):
    """Rotate point x2, y2 about point x1, y1 by angle.

    Parameters
    ----------
    x1 : float

    y1 : float

    x2 : float

    y2 : float

    angle : float
        Angle in radians.

    Returns
    -------
    xnew : float

    ynew : float
    """
    s = np.sin(angle)
    c = np.cos(angle)
    x2 = translate(-x1, x2)
    y2 = translate(-y1, y2)
    xnew = c * x2 - s * y2
    ynew = s * x2 + c * y2
    xnew = translate(x1, xnew)
    ynew = translate(y1, ynew)
    return xnew, ynew


def remove_close_values(ar, mtol=2):
    """Remove values which are within a tolerance of mtol of another value
    present in list.

    Parameters
    ----------
    ar : list

    mtol : int, default: 2, optional

    Returns
    -------
    ret : list
    """
    ret = []
    for a in ar:
        if not ret:
            ret.append(a)
        else:
            temp = ret[-1]
            if np.isclose(temp, a, atol=mtol):
                pass
            else:
                ret.append(a)
    return ret


def merge_close_values(ar, mtol=2):
    """Merge values which are within a tolerance of mtol by calculating
    a moving mean.

    Parameters
    ----------
    ar : list

    mtol : int, default: 2, optional

    Returns
    -------
    ret : list
    """
    ret = []
    for a in ar:
        if not ret:
            ret.append(a)
        else:
            temp = ret[-1]
            if np.isclose(temp, a, atol=mtol):
                temp = (temp + a) / 2.0
                ret[-1] = temp
            else:
                ret.append(a)
    return ret


def get_row_idx(t, rows):
    """Get index of the row in which the given object falls by
    comparing their co-ordinates.

    Parameters
    ----------
    t : object

    rows : list

    Returns
    -------
    r : int
    """
    for r in range(len(rows)):
        if (t.y0 + t.y1) / 2.0 < rows[r][0] and (t.y0 + t.y1) / 2.0 > rows[r][1]:
            return r


def get_column_idx(t, columns):
    """Get index of the column in which the given object falls by
    comparing their co-ordinates.

    Parameters
    ----------
    t : object

    columns : list

    Returns
    -------
    c : int
    """
    for c in range(len(columns)):
        if (t.x0 + t.x1) / 2.0 > columns[c][0] and (t.x0 + t.x1) / 2.0 < columns[c][1]:
            return c


def reduce_index(t, rotated, r_idx, c_idx):
    """Shift a text object if it lies within a spanning cell taking
    in account table rotation.

    Parameters
    ----------
    t : object

    rotated : string

    r_idx : int

    c_idx : int

    Returns
    -------
    r_idx : int

    c_idx : int
    """
    if not rotated:
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].left:
                c_idx -= 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].top:
                r_idx -= 1
    elif rotated == 'left':
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].left:
                c_idx -= 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].bottom:
                r_idx += 1
    elif rotated == 'right':
        if t.cells[r_idx][c_idx].spanning_h:
            while not t.cells[r_idx][c_idx].right:
                c_idx += 1
        if t.cells[r_idx][c_idx].spanning_v:
            while not t.cells[r_idx][c_idx].top:
                r_idx -= 1
    return r_idx, c_idx


def outline(t):
    """Light up table boundary.

    Parameters
    ----------
    t : object

    Returns
    -------
    t : object
    """
    for i in range(len(t.cells)):
        t.cells[i][0].left = True
        t.cells[i][len(t.cells[i]) - 1].right = True
    for i in range(len(t.cells[0])):
        t.cells[0][i].top = True
        t.cells[len(t.cells) - 1][i].bottom = True
    return t


def fill(t, f=None):
    """Fill spanning cells.

    Parameters
    ----------
    t : object

    f : string, default: None, optional

    Returns
    -------
    t : object
    """
    if f == "h":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_h:
                        t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
    elif f == "v":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_v:
                        t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    elif f == "hv":
        for i in range(len(t.cells)):
            for j in range(len(t.cells[i])):
                if t.cells[i][j].get_text().strip() == '':
                    if t.cells[i][j].spanning_h:
                        t.cells[i][j].add_text(t.cells[i][j - 1].get_text())
                    elif t.cells[i][j].spanning_v:
                        t.cells[i][j].add_text(t.cells[i - 1][j].get_text())
    return t


def remove_empty(d):
    """Remove empty rows and columns.

    Parameters
    ----------
    d : list

    Returns
    -------
    d : list
    """
    for i, row in enumerate(d):
        if row == [''] * len(row):
            d.pop(i)
    d = zip(*d)
    d = [list(row) for row in d if any(row)]
    d = zip(*d)
    return d
