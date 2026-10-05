"""Geometry kit for the WASM.RIP typeface.

Everything is drawn upright in font units (y up, baseline 0) and sheared to
the logo's slant at the very end.
"""
import math
import numpy as np
import pathops
import cv2

K_CIRCLE = 0.5523


def _path():
    return pathops.Path()


def polygon(pts):
    p = _path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def rect(x0, y0, x1, y1):
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    return polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def rrect(x0, y0, x1, y1, r, k=0.62):
    """Rounded rectangle. r = radius or (tl, tr, br, bl); each may be (rx, ry).
    k is the bezier handle ratio: 0.5523 = circular, higher = squarer corner."""
    if not isinstance(r, (tuple, list)):
        r = (r, r, r, r)
    rs = []
    w, h = x1 - x0, y1 - y0
    for c in r:
        rx, ry = (c, c) if not isinstance(c, (tuple, list)) else c
        rs.append((max(0.0, min(rx, w / 2)), max(0.0, min(ry, h / 2))))
    (tlx, tly), (trx, try_), (brx, bry), (blx, bly) = rs
    p = _path()
    # start bottom edge, go counter-clockwise (y up)
    p.moveTo(x0 + blx, y0)
    p.lineTo(x1 - brx, y0)
    if brx and bry:
        p.cubicTo(x1 - brx + brx * k, y0, x1, y0 + bry - bry * k, x1, y0 + bry)
    p.lineTo(x1, y1 - try_)
    if trx and try_:
        p.cubicTo(x1, y1 - try_ + try_ * k, x1 - trx + trx * k, y1, x1 - trx, y1)
    p.lineTo(x0 + tlx, y1)
    if tlx and tly:
        p.cubicTo(x0 + tlx - tlx * k, y1, x0, y1 - tly + tly * k, x0, y1 - tly)
    p.lineTo(x0, y0 + bly)
    if blx and bly:
        p.cubicTo(x0, y0 + bly - bly * k, x0 + blx - blx * k, y0, x0 + blx, y0)
    p.close()
    return p


def ellipse(cx, cy, rx, ry):
    return rrect(cx - rx, cy - ry, cx + rx, cy + ry, ((rx, ry),) * 4, K_CIRCLE)


def para(bx0, bx1, by, tx0, tx1, ty):
    """Quad with a horizontal bottom edge [bx0,bx1]@by and top edge [tx0,tx1]@ty."""
    return polygon([(bx0, by), (bx1, by), (tx1, ty), (tx0, ty)])


def stroke(p0, p1, w, cap_y=None):
    """Straight stroke of horizontal width w between two centre points.
    Ends are cut horizontally (that is how the logo's diagonals end)."""
    (x0, y0), (x1, y1) = p0, p1
    return para(x0 - w / 2, x0 + w / 2, y0, x1 - w / 2, x1 + w / 2, y1)


def union(*paths):
    paths = [p for p in paths if p is not None]
    out = _path()
    for p in paths:
        out = pathops.op(out, p, pathops.PathOp.UNION)
    return out


def diff(a, *bs):
    for b in bs:
        if b is not None:
            a = pathops.op(a, b, pathops.PathOp.DIFFERENCE)
    return a


def inter(a, b):
    return pathops.op(a, b, pathops.PathOp.INTERSECTION)


def clip_y(p, y0, y1, x0=-5000, x1=5000):
    return inter(p, rect(x0, y0, x1, y1))


def transform(p, a=1, b=0, c=0, d=1, e=0, f=0):
    """x' = a*x + c*y + e ; y' = b*x + d*y + f"""
    out = _path()
    pen = out.getPen()
    for verb, pts in p.segments:
        tp = [(a * x + c * y + e, b * x + d * y + f) for x, y in pts]
        if verb == "moveTo":
            pen.moveTo(tp[0])
        elif verb == "lineTo":
            pen.lineTo(tp[0])
        elif verb == "curveTo":
            pen.curveTo(*tp)
        elif verb == "qCurveTo":
            pen.qCurveTo(*tp)
        elif verb == "closePath":
            pen.closePath()
        elif verb == "endPath":
            pen.endPath()
    return out


def shift(p, dx=0, dy=0):
    return transform(p, e=dx, f=dy)


def mirror_x(p, axis):
    return reverse(transform(p, a=-1, e=2 * axis))


def mirror_y(p, axis):
    return reverse(transform(p, d=-1, f=2 * axis))


def reverse(p):
    # winding fix after mirroring
    q = union(p)
    return q


def shear(p, t):
    return transform(p, c=t)


def bounds(p):
    try:
        return p.bounds
    except Exception:
        return (0, 0, 0, 0)


# ---------- rasterising (used for fitting + previews) ----------


def contours(p, steps=12):
    polys, cur, last = [], [], None
    for verb, pts in p.segments:
        if verb == "moveTo":
            if cur:
                polys.append(cur)
            cur = [pts[0]]
            last = pts[0]
        elif verb == "lineTo":
            cur.append(pts[0])
            last = pts[0]
        elif verb == "curveTo":
            (x1, y1), (x2, y2), (x3, y3) = pts
            x0, y0 = last
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                cur.append((
                    mt ** 3 * x0 + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t ** 3 * x3,
                    mt ** 3 * y0 + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t ** 3 * y3,
                ))
            last = (x3, y3)
        elif verb == "qCurveTo":
            for q in pts:
                cur.append(q)
                last = q
        elif verb in ("closePath", "endPath"):
            if cur:
                polys.append(cur)
            cur = []
    if cur:
        polys.append(cur)
    return polys


def raster(p, scale, width, height, ox=0, oy=0, ss=4):
    """Rasterise path. scale px/unit; (ox, oy) = pixel position of the origin
    (baseline) in the output image; image y goes down."""
    W, H = width * ss, height * ss
    img = np.zeros((H, W), np.uint8)
    polys = []
    for c in contours(p):
        arr = np.array([[(ox + x * scale) * ss, (oy - y * scale) * ss] for x, y in c], np.float64)
        polys.append(np.round(arr * 16).astype(np.int32))
    if polys:
        cv2.fillPoly(img, polys, 255, lineType=cv2.LINE_8, shift=4)
    if ss > 1:
        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
    return img
