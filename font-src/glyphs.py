"""WASM.RIP glyph constructions. All upright, font units, baseline 0."""
import json, os
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))

# starting point, refined by fit.py against the logo and stored in params.json
P = dict(
    C=700, V=168, k=0.66,
    # P
    P_w=610, P_b=245, P_ht=140, P_hb=140, P_vb=165, P_ro=190, P_ri=60,
    # R
    R_w=600, R_b=285, R_ht=140, R_hb=135, R_vb=160, R_ro=170, R_ri=55,
    R_lx=330, R_ltx=250, R_ld=190,
    # A
    A_w=735, A_d=200, A_t=120, A_c0=170, A_c1=280,
    # M
    M_w=775, M_d=170, M_x0=0, M_f=150, M_vb=170,
    # W
    W_w=1015, W_d1=185, W_d2=175, W_bl=95, W_f1=150, W_ma=700, W_mt=90,
    # S
    S_xu0=20, S_xu1=570, S_xl0=0, S_xl1=600, S_vs=170, S_ht=160, S_hm=150, S_hb=150,
    S_ym=370, S_rou=210, S_riu=70, S_rol=220, S_ril=70, S_xt=560, S_st=0.25, S_xb=50, S_sb=0.25,
    # dot
    dot=190, dot_e=1.0, dot_y=-8,
    S_os=12, S_rt=200, S_tL=120, S_td=30, S_bL=120, S_bd=30,
    slant=0.1705,
)

_pf = os.path.join(HERE, "params.json")
if os.path.exists(_pf):
    P.update(json.load(open(_pf)))


def g_I(p=P):
    return rect(0, 0, p["V"], p["C"])


def dot(cx, cy, d, p=P):
    """Round dot. Pre-sheared backwards so it is a true circle once the
    whole font is slanted (the logo's dot is round, not leaning)."""
    e = ellipse(cx, cy, d / 2, d / 2 * p["dot_e"])
    return transform(e, c=-p["slant"], e=p["slant"] * cy)


def g_period(p=P):
    d = p["dot"]
    return dot(d / 2, p["dot_y"] + d / 2 * p["dot_e"], d)


def bowl(x0, w, yb, yt, ht, hb, vb, ro, ri, k, stem):
    """D-shaped bowl attached to a stem on its left (P, R, B, D...)."""
    outer = rrect(x0, yb, x0 + w, yt, (0, ro, ro, 0), k)
    inner = rrect(x0 + stem, yb + hb, x0 + w - vb, yt - ht, (0, ri, ri, 0), k)
    return diff(outer, inner)


def g_P(p=P):
    C, V = p["C"], p["V"]
    return union(rect(0, 0, V, C), bowl(0, p["P_w"], p["P_b"], C, p["P_ht"], p["P_hb"], p["P_vb"], p["P_ro"], p["P_ri"], p["k"], V))


def g_R(p=P):
    C, V = p["C"], p["V"]
    b = bowl(0, p["R_w"], p["R_b"], C, p["R_ht"], p["R_hb"], p["R_vb"], p["R_ro"], p["R_ri"], p["k"], V)
    yl = p["R_b"] + p["R_hb"] * 0.5
    leg = para(p["R_lx"], p["R_lx"] + p["R_ld"], 0, p["R_ltx"], p["R_ltx"] + p["R_ld"], yl)
    return union(rect(0, 0, V, C), b, leg)


def g_A(p=P):
    C, w, d, t = p["C"], p["A_w"], p["A_d"], p["A_t"]
    cx = w / 2
    left = para(0, d, 0, cx - t / 2, cx - t / 2 + d, C)
    right = para(w - d, w, 0, cx + t / 2 - d, cx + t / 2, C)
    hull = polygon([(0, 0), (w, 0), (cx + t / 2, C), (cx - t / 2, C)])
    bar = inter(rect(0, p["A_c0"], w, p["A_c1"]), hull)
    return clip_y(union(left, right, bar), 0, C)


def g_M(p=P):
    C, V, w, d = p["C"], p["V"], p["M_w"], p["M_d"]
    cx, f, vb, x0 = w / 2, p["M_f"], p["M_vb"], p["M_x0"]
    left = para(cx - f / 2, cx - f / 2 + d, vb, x0, x0 + d, C)
    right = para(cx + f / 2 - d, cx + f / 2, vb, w - x0 - d, w - x0, C)
    # clip to the outer hull so the vertex is clean whatever the flat width
    hull = polygon([(x0, C), (cx - f / 2, vb), (cx + f / 2, vb), (w - x0, C)])
    return union(rect(0, 0, V, C), rect(w - V, 0, w, C), inter(clip_y(union(left, right), vb, C), hull))


def g_W(p=P):
    C, w = p["C"], p["W_w"]
    d1, d2, bl, f1, ma, mt = p["W_d1"], p["W_d2"], p["W_bl"], p["W_f1"], p["W_ma"], p["W_mt"]
    cx = w / 2
    ol = para(bl, bl + d1, 0, 0, d1, C)
    il = para(bl + f1 - d2, bl + f1, 0, cx - mt / 2, cx - mt / 2 + d2, ma)
    half = union(ol, il)
    other = mirror_x(half, cx)
    return clip_y(union(half, other), 0, C)


def g_S(p=P):
    k = p["k"]
    os_ = p["S_os"]
    return shift(_S(p, p["C"] + 2 * os_, k), 0, -os_)


def _flare(x_s, y, L, depth, direction, n=24):
    """Material under (direction=+1, going right and down) or over
    (direction=-1, going left and up) a bar's inner edge, easing out of the
    flat edge so there's no kink: depth(u) = depth * u**1.7, u = dist / L."""
    pts = []
    span = 2.6
    for i in range(n + 1):
        u = span * i / n
        pts.append((x_s + direction * u * L, y - direction * depth * u ** 1.7))
    far = x_s + direction * span * L
    pts += [(far, y + direction * 1), (x_s, y + direction * 1)]
    return polygon(pts)


def _S(p, C, k):
    vs, ht, hm, hb, ym = p["S_vs"], p["S_ht"], p["S_hm"], p["S_hb"], p["S_ym"]
    xu0, xu1, xl0, xl1 = p["S_xu0"], p["S_xu1"], p["S_xl0"], p["S_xl1"]
    # the terminal corners (upper top-right, lower bottom-left) get their own
    # small radius: in the logo the bars run straight out to the angled cut
    rt = p["S_rt"]
    up = diff(rrect(xu0, ym - hm / 2, xu1, C, (p["S_rou"], rt, p["S_rou"], p["S_rou"]), k),
              rrect(xu0 + vs, ym + hm / 2, xu1 - vs, C - ht, (p["S_riu"], 0, 0, p["S_riu"]), k))
    lo = diff(rrect(xl0, 0, xl1, ym + hm / 2, (p["S_rol"], p["S_rol"], p["S_rol"], rt), k),
              rrect(xl0 + vs, hb, xl1 - vs, ym - hm / 2, (0, p["S_ril"], p["S_ril"], 0), k))
    big = 3000
    yt0 = ym - hm / 2 - 1
    xt, st = p["S_xt"], p["S_st"]
    # effective corner radii (rrect clamps them to half the box)
    r_u = min(p["S_rou"], (C - (ym - hm / 2)) / 2, (xu1 - xu0) / 2)
    r_l = min(p["S_rol"], (ym + hm / 2) / 2, (xl1 - xl0) / 2)
    # trim each bowl's bar only where the other bowl's edge is already
    # straight, so the spine joins have no steps
    x_cut_u = min(xu1 - vs - p["S_riu"], xl1 - r_l - 2)
    x_cut_l = max(xl0 + vs + p["S_ril"], xu0 + r_u + 2)
    if x_cut_u < x_cut_l + 4:          # flats don't overlap: never leave a gap
        x_cut_u = x_cut_l = (x_cut_u + x_cut_l) / 2
        x_cut_u += 3
    line_t = polygon([(xt, C + 20), (big, C + 20), (big, yt0), (xt - (C + 20 - yt0) * st, yt0)])
    up = diff(up, rect(xu1 - vs - 1, ym + hm / 2, big, C - ht), rect(x_cut_u, yt0, big, ym + hm / 2 + 1))
    # the terminal flares: the bar's underside slopes down into the angled cut
    xl_t = xt - (C + 20 - (C - ht)) * st          # where the cut crosses the bar's inner edge
    L, td = p["S_tL"], p["S_td"]
    x_s = xl_t - L
    up = union(up, inter(_flare(x_s, C - ht, L, td, +1), rect(-big, yt0 + 1, big, big)))
    up = diff(up, line_t)
    yb1 = ym + hm / 2 + 1
    xb, sb = p["S_xb"], p["S_sb"]
    line_b = polygon([(xb, -20), (-big, -20), (-big, yb1), (xb + (yb1 + 20) * sb, yb1)])
    lo = diff(lo, rect(-big, hb, xl0 + vs + 1, ym - hm / 2), rect(-big, ym - hm / 2 - 1, x_cut_l, yb1))
    xl_b = xb + (hb + 20) * sb
    L, bd = p["S_bL"], p["S_bd"]
    x_s = xl_b + L
    lo = union(lo, inter(_flare(x_s, hb, L, bd, -1), rect(-big, -big, big, yb1 - 1)))
    lo = diff(lo, line_b)
    return union(up, lo)


LOGO = {"W": g_W, "A": g_A, "S": g_S, "M": g_M, "period": g_period, "R": g_R, "I": g_I, "P": g_P}
