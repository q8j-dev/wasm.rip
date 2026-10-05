"""Optical sidebearings (area method) for the upright outlines."""
import numpy as np
import full
from kit import raster, bounds

RES = 0.25          # px per unit for measuring
def profile(path, y0, y1, step=10):
    x0, yb0, x1, yb1 = bounds(path)
    W = int((x1 - x0) * RES) + 4
    Hh = int((max(yb1, y1) - min(yb0, y0)) * RES) + 4
    top = max(yb1, y1)
    img = raster(path, RES, W, Hh, ox=2 - x0 * RES, oy=2 + top * RES, ss=2) > 127
    L, R = [], []
    for y in np.arange(y0, y1 + 1, step):
        row = int(round(2 + (top - y) * RES))
        if 0 <= row < Hh and img[row].any():
            xs = np.where(img[row])[0]
            L.append((xs.min() - 2) / RES)
            R.append((W - 1 - 2 - xs.max()) / RES)
        else:
            L.append(None); R.append(None)
    return (x0, x1), L, R

def side_white(m, depth):
    vals = [depth if v is None else min(v, depth) for v in m]
    return float(np.mean(vals))

def sidebearings(path, zone, base, depth, factor, minsb):
    (x0, x1), L, R = profile(path, *zone)
    lw, rw = side_white(L, depth), side_white(R, depth)
    return max(minsb, base - factor * lw), max(minsb, base - factor * rw), x0, x1
