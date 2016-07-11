import numpy as np


def translate(x1, x2):
    x2 += x1
    return x2


def scale(x, s):
    x *= s
    return x


def rotate(x1, y1, x2, y2, angle):
    s = np.sin(angle)
    c = np.cos(angle)
    x2 = translate(-x1, x2)
    y2 = translate(-y1, y2)
    xnew = c * x2 - s * y2
    ynew = s * x2 + c * y2
    xnew = translate(x1, xnew)
    ynew = translate(y1, ynew)
    return xnew, ynew


def remove_close_values(ar, mtol):
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


def merge_close_values(ar, mtol):
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
    for r in range(len(rows)):
        if (t.y0 + t.y1) / 2.0 < rows[r][0] and (t.y0 + t.y1) / 2.0 > rows[r][1]:
            return r


def get_column_idx(t, columns):
    for c in range(len(columns)):
        if (t.x0 + t.x1) / 2.0 > columns[c][0] and (t.x0 + t.x1) / 2.0 < columns[c][1]:
            return c


def reduce_index(t, rotated, r_idx, c_idx):
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
    for i in range(len(t.cells)):
        t.cells[i][0].left = True
        t.cells[i][len(t.cells[i]) - 1].right = True
    for i in range(len(t.cells[0])):
        t.cells[0][i].top = True
        t.cells[len(t.cells) - 1][i].bottom = True
    return t


def fill(t, f):
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
    for i, row in enumerate(d):
        if row == [''] * len(row):
            d.pop(i)
    d = zip(*d)
    d = [list(row) for row in d if any(row)]
    d = zip(*d)
    return d
