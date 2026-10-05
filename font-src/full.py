"""The complete WASM.RIP character set.

Every glyph is built from the measurements fitted to the logo (glyphs.P):
stem weight, bar weight, curve radii/tension, diagonal width, overshoot,
dot size, terminal cut angles. Upright, font units, baseline 0.
"""
import math
from kit import *
import glyphs
from glyphs import P, bowl, dot as _dot

# ---------------------------------------------------------------- metrics
C = P["C"]                      # cap height (700)
V = P["V"]                      # cap stem
H = (P["P_ht"] + P["P_hb"] + P["R_ht"] + P["R_hb"]) / 4   # cap bar
VS = P["S_vs"]                  # vertical weight on rounds
HS = (P["S_ht"] + P["S_hb"]) / 2  # horizontal weight on rounds
K = P["k"]
RO = (P["P_ro"] + P["R_ro"]) / 2  # outer curve radius
RI = (P["P_ri"] + P["R_ri"]) / 2  # inner curve radius
OS = P["S_os"]                  # overshoot
DG = (P["A_d"] + P["M_d"] + P["W_d1"]) / 3  # diagonal (horizontal width)
DOT = P["dot"]
ST = P["S_st"]                  # top terminal cut slope (dx per dy)
SB = P["S_sb"]                  # bottom terminal cut slope

X = 530                         # x-height
ASC = 740                       # ascender
DESC = -200                     # descender
v = V * 0.93                    # lowercase stem
h = H * 0.94                    # lowercase bar
vs = VS * 0.93
hs = HS * 0.93
ro = RO * 0.86
ri = RI * 0.80
dg = DG * 0.93
os_ = OS * 0.9
MATH_Y = 330                    # centre line for + = - etc.

BIG = 4000


def ring(x0, y0, x1, y1, tx, ty, r_out, r_in, k=K, corners=None, icorners=None):
    """Closed rounded ring (O, 0, o...). tx/ty = side / top-bottom weights."""
    co = corners if corners is not None else r_out
    ci = icorners if icorners is not None else r_in
    return diff(rrect(x0, y0, x1, y1, co, k), rrect(x0 + tx, y0 + ty, x1 - tx, y1 - ty, ci, k))


def aperture_right(x_top, y_top, x_bot, y_bot, y_mid_hi, y_mid_lo, st=ST, sb=SB):
    """Chevron-shaped cut opening a round on its right (C, c, G, e...).
    The terminal faces use the logo S's cut angles."""
    return polygon([
        (x_top, y_top), (BIG, y_top), (BIG, y_bot), (x_bot, y_bot),
        (x_bot - (y_mid_lo - y_bot) * sb, y_mid_lo),
        (x_top - (y_top - y_mid_hi) * st, y_mid_hi),
    ])


def aperture_left(x_top, y_top, x_bot, y_bot, y_mid_hi, y_mid_lo, st=ST, sb=SB):
    return mirror_x(aperture_right(-x_top, y_top, -x_bot, y_bot, y_mid_hi, y_mid_lo, st, sb), 0)


def open_round(x0, y0, x1, y1, tx, ty, r_out, r_in, side="right", top_term=True, bot_term=True,
               keep_from=None, st=ST, sb=SB, inset=10):
    """A round opened on one side, built like the logo's S: the counter is
    square on the open side, the side wall is removed between the bars, and
    each bar ends in an angled cut (logo S cut slopes)."""
    if side == "left":
        w = x1 - x0
        q = open_round(0, y0, w, y1, tx, ty, r_out, r_in, "right", top_term, bot_term, keep_from, st, sb, inset)
        return shift(mirror_x(q, w / 2), x0)
    o = rrect(x0, y0, x1, y1, r_out, K)
    i = rrect(x0 + tx, y0 + ty, x1 - tx, y1 - ty, (r_in, 0, 0, r_in), K)
    shape = diff(o, i)
    lo = y0 + ty if keep_from is None else keep_from
    shape = diff(shape, rect(x1 - tx - 1, lo, BIG, y1 - ty))
    if top_term:
        xt = x1 - inset
        shape = diff(shape, polygon([(xt, y1 + 5), (BIG, y1 + 5), (BIG, y1 - ty - 5), (xt - (ty + 10) * st, y1 - ty - 5)]))
    else:
        shape = diff(shape, rect(x1 - tx - 1, y1 - ty - 1, BIG, BIG))
    if bot_term and keep_from is None:
        xb = x1 - inset
        shape = diff(shape, polygon([(xb, y0 - 5), (BIG, y0 - 5), (BIG, y0 + ty + 5), (xb - (ty + 10) * sb, y0 + ty + 5)]))
    elif keep_from is None:
        shape = diff(shape, rect(x1 - tx - 1, -BIG, BIG, y0 + ty + 1))
    return shape


def hook_left(x0, x1, yb, yt, tx, ty, r_out, r_in, sb=SB, inset=10, stem=None):
    """Bottom hook curving left from a right-hand stem (J, j, g). The right
    wall matches the stem exactly so there is no step at the join."""
    sw = stem if stem is not None else tx
    o = rrect(x0, yb, x1, yt, (0, 0, r_out, r_out), K)
    i = rrect(x0 + tx, yb + ty, x1 - sw, yt + 50, (0, 0, r_in, 0), K)
    shape = diff(o, i)
    shape = diff(shape, rect(-BIG, yb + ty, x0 + tx + 1, BIG))
    xb = x0 - inset + 22
    shape = diff(shape, polygon([(xb, yb - 5), (-BIG, yb - 5), (-BIG, yb + ty + 5), (xb + (ty + 10) * sb, yb + ty + 5)]))
    return shape

def cstroke(c0, c1, w):
    """Stroke between two centre points, horizontal width w, flat ends."""
    return para(c0[0] - w / 2, c0[0] + w / 2, c0[1], c1[0] - w / 2, c1[0] + w / 2, c1[1])


def rot(p, ang, cx, cy):
    c, s = math.cos(ang), math.sin(ang)
    return transform(p, a=c, b=s, c=-s, d=c, e=cx - c * cx + s * cy, f=cy - s * cx - c * cy)


def vee(w, top, d, f, bottom=0):
    """Two diagonals meeting at the bottom with a flat of width f (V, v, Y)."""
    cx = w / 2
    left = para(cx - f / 2, cx - f / 2 + d, bottom, 0, d, top)
    right = para(cx + f / 2 - d, cx + f / 2, bottom, w - d, w, top)
    hull = polygon([(0, top), (cx - f / 2, bottom), (cx + f / 2, bottom), (w, top)])
    return inter(clip_y(union(left, right), bottom, top), hull)


# =============================================================== CAPITALS
G = {}   # name -> (path, advance-independent; spacing applied later)


def cap_A():
    return glyphs.g_A()


def cap_B():
    ym = 372
    up = bowl(0, 600, ym - H / 2, C, H, H * 0.96, VS * 0.95, min(RO, (C - ym + H / 2) / 2), RI * 0.9, K, V)
    lo = bowl(0, 640, 0, ym + H / 2, H * 0.96, H, VS, RO, RI, K, V)
    return union(rect(0, 0, V, C), up, lo)


def cap_C():
    w = 680
    return open_round(0, -OS, w, C + OS, VS, HS, RO * 1.08, RI * 1.05)

def cap_D():
    return union(rect(0, 0, V, C), bowl(0, 690, 0, C, H, H, VS, RO * 1.12, RI * 1.15, K, V))


def cap_E():
    ym = 365
    return union(rect(0, 0, V, C), rect(0, C - H, 560, C), rect(0, ym - H * 0.48, 520, ym + H * 0.48), rect(0, 0, 570, H))


def cap_F():
    ym = 345
    return union(rect(0, 0, V, C), rect(0, C - H, 550, C), rect(0, ym - H * 0.48, 505, ym + H * 0.48))


def cap_G():
    w = 715
    ybar = 360
    g = open_round(0, -OS, w, C + OS, VS, HS, RO * 1.08, RI * 1.05, keep_from=ybar)
    # lower right wall stays, a bar steps in from it
    g = union(g, rect(w * 0.48, ybar - H, w, ybar))
    return g

def cap_H():
    w = 690
    return union(rect(0, 0, V, C), rect(w - V, 0, w, C), rect(0, 360 - H / 2, w, 360 + H / 2))


def cap_I():
    return glyphs.g_I()


def cap_J():
    w = 580
    hook = hook_left(0, w, -OS, 360, VS, HS, RO * 1.05, RI, stem=V)
    return union(hook, rect(w - V, 200, w, C))

def cap_K():
    w = 690
    d = DG * 1.05
    a0, a1 = (V - 1 - d / 2, 110), (w - d / 2, C)
    arm = inter(cstroke(a0, a1, d), rect(0, -BIG, BIG, BIG))
    yl = 335
    xl = a0[0] + (yl - a0[1]) / (a1[1] - a0[1]) * (a1[0] - a0[0])
    leg = cstroke((w - d * 0.53, 0), (xl, yl), d * 1.06)
    return union(rect(0, 0, V, C), clip_y(arm, 0, C), clip_y(leg, 0, C))

def cap_L():
    return union(rect(0, 0, V, C), rect(0, 0, 545, H))


def cap_M():
    return glyphs.g_M()


def cap_N():
    w = 700
    d = DG * 1.1
    diag = para(w - V - d * 0.3, w - V + d * 0.7, 0, V - d * 0.7, V + d * 0.3, C)
    return union(rect(0, 0, V, C), rect(w - V, 0, w, C), clip_y(diag, 0, C))


def cap_O():
    w = 760
    return ring(0, -OS, w, C + OS, VS, HS, RO * 1.12, RI * 1.12)


def cap_P():
    return glyphs.g_P()


def cap_Q():
    w = 760
    d = DG * 0.95
    top_y = HS - OS - 10                     # just under the inside of the bottom bar
    tail = clip_y(cstroke((w * 0.60, top_y), (w * 0.86, -95), d), -95, top_y)
    return union(cap_O(), tail)

def cap_R():
    return glyphs.g_R()


def cap_S():
    return glyphs.g_S()


def cap_T():
    w = 640
    return union(rect(0, C - H, w, C), rect(w / 2 - V / 2, 0, w / 2 + V / 2, C))


def cap_U():
    w = 690
    u = ring(0, -OS, w, C + 400, VS * 0.97, HS, 0, 0, corners=(0, 0, RO * 1.08, RO * 1.08), icorners=(0, 0, RI * 1.1, RI * 1.1))
    return clip_y(u, -OS - 5, C)


def cap_V():
    return vee(735, C, DG * 1.02, DG * 1.0)

def cap_W():
    return glyphs.g_W()


def cap_X():
    w = 720
    d = DG * 1.06
    a = para(w - d, w, 0, 0, d, C)
    b = para(0, d, 0, w - d, w, C)
    return clip_y(union(a, b), 0, C)


def cap_Y():
    w = 725
    d = DG * 1.02
    yj = 300
    cx = w / 2
    top = vee(w, C, d, V * 1.0, yj - 10)
    stem = rect(cx - V / 2, 0, cx + V / 2, yj + 40)
    return union(top, stem)


def cap_Z():
    w = 625
    d = DG * 1.12
    diag = para(0, d, H - 5, w - d, w, C - H + 5)
    return union(rect(0, C - H, w - 10, C), rect(0, 0, w, H), diag)


# ============================================================== LOWERCASE


def lc_bowl_closed(w, y0=0, y1=X):
    return ring(0, y0 - os_, w, y1 + os_, vs, hs, ro, ri)


def lc_o():
    return lc_bowl_closed(600)


def bowl_with_stem(w, right_stem, y0, y1, stem_y0, stem_y1):
    """Bowl fused with a straight stem (a b d p q g). The corners on the stem
    side are square, like the bowl of the logo's P."""
    if right_stem:
        co, ci = (ro, 0, 0, ro), (ri, 0, 0, ri)
    else:
        co, ci = (0, ro, ro, 0), (0, ri, ri, 0)
    b = diff(rrect(0, y0 - os_ * 0.6, w, y1 + os_ * 0.6, co, K),
             rrect(vs if right_stem else v, y0 + hs - os_ * 0.6, w - (v if right_stem else vs), y1 - hs + os_ * 0.6, ci, K))
    stem = rect(w - v, stem_y0, w, stem_y1) if right_stem else rect(0, stem_y0, v, stem_y1)
    return union(b, stem)


def lc_a():
    return bowl_with_stem(600, True, 0, X, 0, X)


def lc_b():
    return bowl_with_stem(605, False, 0, X, 0, ASC)


def lc_c():
    w = 555
    return open_round(0, -os_, w, X + os_, vs, hs, ro, ri)

def lc_d():
    return bowl_with_stem(605, True, 0, X, 0, ASC)


def lc_e():
    w = 590
    ybar = X * 0.50
    o = rrect(0, -os_, w, X + os_, ro, K)
    i = rrect(vs, hs - os_, w - vs, X + os_ - hs, (ri, ri, 0, ri), K)
    e = diff(o, i)
    e = union(e, rect(vs - 1, ybar - h / 2, w - vs + 1, ybar + h / 2))
    e = diff(e, rect(w - vs - 1, hs - os_, BIG, ybar - h / 2))
    xb = w - 10
    e = diff(e, polygon([(xb, -os_ - 5), (BIG, -os_ - 5), (BIG, hs - os_ + 5), (xb - (hs + 10) * SB, hs - os_ + 5)]))
    return e

def lc_f():
    w = 400
    x0 = 50
    top = ASC
    arc = ring(x0, top - 2 * ro, x0 + 2 * ro + 40, top + os_ * 0.5, v, h, ro, ri)
    arc = inter(arc, rect(x0 - 5, top - ro, BIG, top + 50))
    cut = polygon([(x0 + ro + 150, top + 60), (BIG, top + 60), (BIG, top - ro - 5), (x0 + ro + 150 - (ro + 65) * ST, top - ro - 5)])
    arc = diff(arc, cut)
    stem = rect(x0, 0, x0 + v, top - ro + 5)
    bar = rect(0, X - h, w - 20, X)
    return union(arc, stem, bar)


def lc_g():
    w = 605
    b = bowl_with_stem(w, True, 0, X, DESC + ro, X)
    hook = hook_left(0, w, DESC - os_, DESC + ro + 40, vs * 0.98, hs, ro, ri, stem=v)
    return union(b, hook)

def arch(w, top, stem_x=0, stem_w=None):
    """n-shaped arch: left stem, rounded right shoulder."""
    sw = stem_w or v
    outer = rrect(stem_x, 0, stem_x + w, top + os_ * 0.6, (0, ro, 0, 0), K)
    inner = rrect(stem_x + sw, -10, stem_x + w - v, top + os_ * 0.6 - h, (0, ri, 0, 0), K)
    return diff(outer, inner)


def lc_h():
    return union(rect(0, 0, v, ASC), arch(570, X))


def lc_i():
    d = DOT * 0.92
    return union(rect(0, 0, v, X), _dot(v / 2, X + 80 + d / 2 * P["dot_e"], d))


def lc_j():
    d = DOT * 0.92
    x0 = 150
    stem = rect(x0, DESC + ro * 0.5, x0 + v, X)
    hook = hook_left(x0 + v - 330, x0 + v, DESC - os_ * 0.5, DESC + ro, v, h, ro * 0.9, ri * 0.8, stem=v)
    return union(stem, hook, _dot(x0 + v / 2, X + 80 + d / 2 * P["dot_e"], d))

def lc_k():
    w = 565
    d = dg * 1.02
    a0, a1 = (v - 1 - d / 2, 70), (w - d / 2, X)
    arm = inter(cstroke(a0, a1, d), rect(0, -BIG, BIG, BIG))
    yl = 255
    xl = a0[0] + (yl - a0[1]) / (a1[1] - a0[1]) * (a1[0] - a0[0])
    leg = cstroke((w - d * 0.53, 0), (xl, yl), d * 1.06)
    return union(rect(0, 0, v, ASC), clip_y(arm, 0, X), clip_y(leg, 0, X))

def lc_l():
    return rect(0, 0, v, ASC)


def lc_m():
    w1 = 470
    a1 = arch(w1, X)
    a2 = arch(w1, X, stem_x=w1 - v, stem_w=v)
    return union(a1, a2)


def lc_n():
    return arch(570, X)


def lc_p():
    return bowl_with_stem(605, False, 0, X, DESC, X)


def lc_q():
    return bowl_with_stem(605, True, 0, X, DESC, X)


def lc_r():
    w = 390
    a = arch(560, X)
    cut = polygon([(w, X + 60), (BIG, X + 60), (BIG, -100), (w - (X + 160) * ST * 0.5, -100)])
    a = diff(a, cut)
    a = diff(a, rect(v, -50, BIG, X - h - 2))
    return a


def lc_s():
    q = dict(P)
    sx = 0.80
    for kk in ("S_xu0", "S_xu1", "S_xl0", "S_xl1", "S_xt", "S_xb"):
        q[kk] = P[kk] * sx
    sy = X / C
    q["S_ym"] = P["S_ym"] * sy
    q["S_vs"] = vs
    q["S_ht"] = P["S_ht"] * 0.88
    q["S_hb"] = P["S_hb"] * 0.88
    q["S_hm"] = P["S_hm"] * 0.86
    q["S_rou"] = P["S_rou"] * 0.70
    q["S_rol"] = P["S_rol"] * 0.70
    q["S_riu"] = P["S_riu"] * 0.75
    q["S_ril"] = P["S_ril"] * 0.75
    return shift(glyphs._S(q, X + 2 * os_, K), 0, -os_)


def lc_t():
    x0 = 55
    return union(rect(x0, 0, x0 + v, 680), rect(0, X - h, 335, X))

def lc_u():
    a = arch(570, X)
    return transform(a, a=-1, d=-1, e=570, f=X)


def lc_v():
    return vee(580, X, dg, dg * 0.95)

def lc_w():
    q = dict(P)
    s = X / C
    q["C"] = X
    q["W_w"] = P["W_w"] * 0.84
    q["W_d1"] = dg
    q["W_d2"] = dg * 0.92
    q["W_bl"] = P["W_bl"] * 0.8
    q["W_f1"] = P["W_f1"] * 0.82
    q["W_mt"] = P["W_mt"] * 0.82
    return glyphs.g_W(q)


def lc_x():
    w = 580
    a = para(w - dg, w, 0, 0, dg, X)
    b = para(0, dg, 0, w - dg, w, X)
    return clip_y(union(a, b), 0, X)


def lc_y():
    w = 590
    d = dg
    xL = 60
    top_r = (w - d / 2, X)
    bot = (xL, DESC)
    long = cstroke(bot, top_r, d)
    x0 = top_r[0] - (X / (X - DESC)) * (top_r[0] - xL)
    short = cstroke((x0, 0), (d / 2, X), d)
    return union(clip_y(long, DESC, X), clip_y(short, 0, X))

def lc_z():
    w = 520
    d = dg * 1.12
    diag = para(0, d, h - 5, w - d, w, X - h + 5)
    return union(rect(0, X - h, w - 10, X), rect(0, 0, w, h), diag)


# ================================================================= DIGITS
FIG = C


def d_zero():
    return ring(0, -OS, 620, FIG + OS, VS, HS, RO, RI * 1.05)


def d_one():
    w = 430
    stem = rect(w - V, 0, w, FIG)
    flag = para(0, 0, FIG - 250, w - V, w - V, FIG)
    # top edge lands exactly on the stem's top-left corner; body runs into the stem
    flag = polygon([(w - V, FIG), (w, FIG), (w, FIG - 200), (40, FIG - 330), (40, FIG - 175)])
    return union(stem, flag)


def d_two():
    w = 600
    yd = 455
    # (corner order is pre-mirror: the last one ends up bottom-right)
    top = open_round(0, 300, w, C + OS, VS, HS, (RO, RO, RO, 0), RI, side="left", bot_term=False, keep_from=-BIG)
    top = diff(top, rect(-BIG, -BIG, BIG, yd))
    top = diff(top, rect(-BIG, -BIG, w - VS, C + OS - HS))
    diag = polygon([(w - VS, yd + 1), (w, yd + 1), (w, yd - 40), (DG * 1.2, H - 1), (0, H - 1), (0, H + 40)])
    return union(top, diag, rect(0, 0, w + 10, H))

def d_three():
    w = 600
    ym = 385
    up = open_round(35, ym - H / 2, w - 20, C + OS, VS * 0.96, HS, min(RO, 175), RI * 0.9, side="left", bot_term=False)
    lo = open_round(0, -OS, w, ym + H / 2, VS, HS, RO, RI, side="left", top_term=False)
    mid = rect(w * 0.30, ym - H / 2, w - 100, ym + H / 2)
    up = diff(up, rect(-BIG, ym - H, w * 0.30, ym - H / 2 + HS + 1))
    lo = diff(lo, rect(-BIG, ym + H / 2 - HS - 1, w * 0.30, ym + H))
    mid = rect(w * 0.30, ym + H / 2 - HS, w - 100, ym - H / 2 + HS)
    return union(up, lo, mid)

def d_four():
    w = 650
    stem = rect(w - 140 - V, 0, w - 140, FIG)
    bar = rect(0, 150, w, 150 + H)
    diag = polygon([(w - 140 - V, FIG), (w - 140 - V + 40, FIG), (DG * 1.05, 150 + H - 1), (0, 150 + H - 1), (0, 150 + H + 70)])
    diag = polygon([(w - 140 - V + 30, FIG), (w - 140 - V + 30 - DG * 1.15 * 0 + 0, FIG - 200), (DG * 1.2, 150), (0, 150), (0, 150 + H + 40)])
    diag = polygon([(w - 140 - V - 10, FIG), (w - 140, FIG), (w - 140, FIG - 150), (DG * 1.25, 150 + H - 2), (0, 150 + H - 2)])
    return union(stem, bar, diag)


def d_five():
    w = 600
    bt = 450
    sx = 30
    b = open_round(0, -OS, w, bt, VS, HS, RO, RI, side="left", top_term=False)
    # the bowl's top bar runs into the stem on the left
    b = union(b, rect(sx, bt - HS, w - RO * 0.9, bt))
    b = diff(b, rect(-BIG, bt - HS - 1, sx, BIG))
    stem = rect(sx, bt - HS, sx + V, C)
    top = rect(sx, C - H, w - 20, C)
    return union(b, stem, top)

def d_six():
    w = 620
    yb = 450
    lo = ring(0, -OS, w, yb, VS, HS, RO * 0.95, RI)
    tall = open_round(0, -OS, w, C + OS, VS, HS, RO * 1.05, RI, keep_from=-BIG)
    tall = diff(tall, rect(VS, -BIG, BIG, C + OS - HS))
    tall = inter(tall, rect(-BIG, yb * 0.5, BIG, BIG))
    return union(lo, tall)

def d_seven():
    w = 590
    top = rect(0, FIG - H, w, FIG)
    diag = polygon([(w - DG * 1.18, FIG - H + 2), (w, FIG - H + 2), (w, FIG - H - 60), (90 + DG * 1.15, 0), (90, 0)])
    return union(top, diag)


def d_eight():
    w = 620
    ym = 395
    up = ring(30, ym - H / 2, w - 30, FIG + OS, VS * 0.95, HS * 0.95, 165, RI * 0.9)
    lo = ring(0, -OS, w, ym + H / 2, VS, HS, RO, RI)
    return union(up, lo)


def d_nine():
    s = d_six()
    return transform(s, a=-1, d=-1, e=620, f=FIG)


# ============================================================ PUNCTUATION


def p_period():
    return glyphs.g_period()


def p_comma():
    """Teardrop comma: convex hull of the round dot and a short tip, so the
    tail leaves the dot tangentially on both sides (no neck, no notch)."""
    from scipy.spatial import ConvexHull
    d = DOT
    e = P["dot_e"]
    body = _dot(d / 2, P["dot_y"] + d / 2 * e, d)
    pts = [q for c in contours(body, 24) for q in c]
    tip_y = -170
    sl = P["slant"]
    # tip placed so that, once slanted, the tail drops down and slightly left
    for xf in (d * 0.08, d * 0.30):
        pts.append((xf - sl * tip_y * 0.35, tip_y))
    hull = ConvexHull(pts)
    return polygon([pts[i] for i in hull.vertices])

def rrect_tip(p):
    return p

def p_colon():
    d = DOT
    e = P["dot_e"]
    return union(_dot(d / 2, P["dot_y"] + d / 2 * e, d), _dot(d / 2, X - d / 2 * e, d))


def p_semicolon():
    d = DOT
    e = P["dot_e"]
    return union(p_comma(), _dot(d / 2, X - d / 2 * e, d))


def p_exclam():
    d = DOT
    e = P["dot_e"]
    w = d
    stem = para(w / 2 - V * 0.38, w / 2 + V * 0.38, 270, w / 2 - V * 0.55, w / 2 + V * 0.55, C)
    return union(stem, _dot(w / 2, P["dot_y"] + d / 2 * e, d))


def p_question():
    w = 560
    d = DOT
    e = P["dot_e"]
    top = open_round(0, 290, w, C + OS, VS, HS, RO * 0.95, RI, side="left", bot_term=False, keep_from=-BIG)
    # stem sits where the hook's underside is still flat, so the join is clean
    r_eff = min(RO * 0.95, (C + OS - 290) / 2)
    sx = min(w / 2, w - r_eff - V / 2 - 2)
    top = diff(top, rect(-BIG, -BIG, sx + V / 2, 290 + HS))
    stem = rect(sx - V / 2, 235, sx + V / 2, 290 + HS)
    return union(top, stem, _dot(sx, P["dot_y"] + d / 2 * e, d))

def p_quotesingle():
    return para(V * 0.12, V * 0.88, C - 260, 0, V, C)


def p_quotedbl():
    q = p_quotesingle()
    return union(q, shift(q, V + 70))


def p_hyphen():
    return rect(0, MATH_Y - 20 - H / 2, 330, MATH_Y - 20 + H / 2)


def p_endash():
    return rect(0, MATH_Y - 20 - H / 2, 520, MATH_Y - 20 + H / 2)


def p_emdash():
    return rect(0, MATH_Y - 20 - H / 2, 1000, MATH_Y - 20 + H / 2)


def p_underscore():
    return rect(0, -170, 560, -170 + H * 0.9)


def p_slash():
    w = 470
    return para(0, DG, -120, w - DG, w, C + 60)


def p_backslash():
    w = 470
    return para(w - DG, w, -120, 0, DG, C + 60)


def p_bar():
    return rect(0, -170, V * 0.9, C + 110)


def p_parenleft():
    w = 300
    r = ring(0, -170, 560, C + 120, V, H, ((250, 330),) * 4, ((180, 290),) * 4)
    return inter(r, rect(-10, -BIG, w, BIG))


def p_parenright():
    return mirror_x(p_parenleft(), 150)


def p_bracketleft():
    return union(rect(0, -170, V, C + 120), rect(0, C + 120 - H, 290, C + 120), rect(0, -170, 290, -170 + H))


def p_bracketright():
    return mirror_x(p_bracketleft(), 145)


def p_braceleft():
    top, bot = C + 120, -170
    mid = (top + bot) / 2
    sx, t = 95, V * 0.9
    stem = rect(sx, bot, sx + t, top)
    capu = rrect(sx, top - H, 330, top, (min(H, 90), 0, 0, 0), K)
    capd = rrect(sx, bot, 330, bot + H, (0, 0, 0, min(H, 90)), K)
    stem = rrect(sx, bot, sx + t, top, (min(H, 90), 0, 0, min(H, 90)), K)
    nose = rect(0, mid - H * 0.45, sx + 1, mid + H * 0.45)
    return union(stem, capu, capd, nose)

def p_braceright():
    return mirror_x(p_braceleft(), 165)


def p_plus():
    w = 560
    t = H * 0.95
    return union(rect(0, MATH_Y - t / 2, w, MATH_Y + t / 2), rect(w / 2 - t / 2, MATH_Y - w / 2 + 20, w / 2 + t / 2, MATH_Y + w / 2 - 20))


def p_minus():
    t = H * 0.95
    return rect(0, MATH_Y - t / 2, 560, MATH_Y + t / 2)


def p_equal():
    t = H * 0.9
    g = 60
    return union(rect(0, MATH_Y + g / 2, 560, MATH_Y + g / 2 + t), rect(0, MATH_Y - g / 2 - t, 560, MATH_Y - g / 2))


def p_less():
    w, hh = 500, 500
    t = H * 0.95                       # stroke weight, measured square to the stroke
    ang = math.atan2(hh / 2, w)
    dx = t / math.sin(ang)             # horizontal offset between the two edges
    dy = t / math.cos(ang)             # height of the vertical end cuts
    fl = 18                            # small flat on the point
    y = MATH_Y
    return polygon([(0, y + fl), (w, y + hh / 2), (w, y + hh / 2 - dy), (dx, y), (w, y - hh / 2 + dy), (w, y - hh / 2), (0, y - fl)])

def p_greater():
    return mirror_x(p_less(), 250)


def p_asterisk():
    t = H * 0.85
    arm = rect(-t / 2, 0, t / 2, 210)
    cx, cy = 230, C - 190
    arms = [rot(shift(arm, cx, cy), math.radians(a), cx, cy) for a in (0, 72, 144, 216, 288)]
    return union(*arms)


def p_asciicircum():
    w = 520
    vv = vee(w, 270, DG * 0.88, DG * 0.88)
    return transform(vv, d=-1, f=C)

def p_asciitilde():
    w, amp, t = 540, 48, H * 0.92
    n = 80
    xs = [w * i / n for i in range(n + 1)]
    yc = [MATH_Y - 10 + amp * math.sin(2 * math.pi * (x / w) - math.pi / 2 * 0) * -1 for x in xs]
    import math as _m
    yc = [MATH_Y - 10 + amp * _m.sin(_m.pi * (2 * x / w - 0.5)) * 1 for x in xs]
    upper = [(x, y + t / 2) for x, y in zip(xs, yc)]
    lower = [(x, y - t / 2) for x, y in zip(xs, yc)][::-1]
    return polygon(upper + lower)

def p_grave():
    return polygon([(0, C + 200), (170, C + 200), (300, C + 60), (170, C + 60)])


def p_numbersign():
    w = 640
    t = H * 0.9
    s = V * 0.85
    return union(rect(140, 0, 140 + s, C), rect(w - 140 - s, 0, w - 140, C),
                 rect(0, 450, w, 450 + t), rect(0, 250 - t, w, 250))


def p_dollar():
    s = cap_S()
    x0, y0, x1, y1 = s.bounds
    cx = (x0 + x1) / 2 - 10
    t = V * 0.62
    return union(s, rect(cx - t / 2, y1 - 30, cx + t / 2, y1 + 110), rect(cx - t / 2, y0 - 110, cx + t / 2, y0 + 30))


def p_percent():
    a = ring(0, 330, 300, C + OS, VS * 0.62, HS * 0.62, 120, 40)
    b = ring(470, -OS, 770, 370, VS * 0.62, HS * 0.62, 120, 40)
    sl = para(125, 125 + DG * 0.85, 0, 645 - DG * 0.85, 645, C)
    return union(a, b, sl)


AMP_ARM = "none"


def p_ampersand(arm_style=None):
    """Loop on top, C-shaped bowl below whose right wall is absorbed by the
    leg, leg from inside the loop down to the baseline. No stroke stops in
    mid-air: every end is on a guideline or buried in another stroke."""
    arm_style = arm_style or AMP_ARM
    t, th = VS * 0.92, HS * 0.92
    dl = DG * 0.98
    leg_a, leg_b = (665, 0), (215, 470)        # centre line, bottom -> top

    def leg_x(y):
        return leg_a[0] + (leg_b[0] - leg_a[0]) * y / leg_b[1]

    leg = clip_y(cstroke(leg_a, leg_b, dl), 0, 470)
    loop = ring(70, 375, 485, C + OS, t * 0.84, th * 0.84, 180, 80)
    # bottom-right corner kept tight so the bottom bar runs flat into the leg
    bowl_ = ring(0, 0, 600, 470, t, th, (215, 215, 40, 215), (RI * 0.95, RI * 0.95, 20, RI * 0.95))
    # everything of the bowl to the right of the leg goes, so the bowl's top
    # and bottom bars both run into the leg and its right wall disappears
    right_of_leg = polygon([(leg_x(-50) + dl / 2, -50), (BIG, -50), (BIG, 600), (leg_x(600) + dl / 2, 600)])
    bowl_ = diff(bowl_, right_of_leg)
    parts = [loop, bowl_, leg]
    if arm_style == "bar":
        ya = 250
        parts.append(rect(leg_x(ya + H * 0.88) - dl / 2 + 20, ya, 760, ya + H * 0.88))
    return union(*parts)

def p_at():
    w = 900
    t = VS * 0.78
    th = HS * 0.78
    y0, y1 = -160, C + 30
    yf = 120
    outer = ring(0, y0, w, y1, t, th, 300, 210, icorners=(210, 210, 0, 210))
    # open the lower right: the wall stops at the foot, the bottom bar ends
    # in the same angled terminal as C
    outer = diff(outer, rect(w - t - 1, y0 + th, BIG, yf))
    xb = w * 0.72
    outer = diff(outer, polygon([(xb, y0 - 5), (BIG, y0 - 5), (BIG, y0 + th + 5), (xb - (th + 10) * SB, y0 + th + 5)]))
    inner = shift(bowl_with_stem(400, True, yf, 520, yf, 520), 220, 0)
    foot = rect(220 + 400 - v, yf, w, yf + th)
    return union(outer, inner, foot)

def p_space():
    return None


CAPS = {ch: globals()[f"cap_{ch}"] for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
LOWER = {ch: globals()[f"lc_{ch}"] for ch in "abcdefghijklmnopqrstuvwxyz"}
DIGITS = {"0": d_zero, "1": d_one, "2": d_two, "3": d_three, "4": d_four, "5": d_five,
          "6": d_six, "7": d_seven, "8": d_eight, "9": d_nine}
PUNCT = {
    ".": p_period, ",": p_comma, ":": p_colon, ";": p_semicolon, "!": p_exclam, "?": p_question,
    "'": p_quotesingle, '"': p_quotedbl, "-": p_hyphen, "–": p_endash, "—": p_emdash,
    "_": p_underscore, "/": p_slash, "\\": p_backslash, "|": p_bar, "(": p_parenleft, ")": p_parenright,
    "[": p_bracketleft, "]": p_bracketright, "{": p_braceleft, "}": p_braceright, "+": p_plus,
    "−": p_minus, "=": p_equal, "<": p_less, ">": p_greater, "*": p_asterisk, "^": p_asciicircum,
    "~": p_asciitilde, "`": p_grave, "#": p_numbersign, "$": p_dollar, "%": p_percent, "&": p_ampersand,
    "@": p_at,
}
ALL = {**CAPS, **LOWER, **DIGITS, **PUNCT}
