"""Typographic extras built from the same parts as the core set."""
import math
from kit import *
import full
from full import P, C, X, DOT, MATH_Y, _dot

NAMES, BUILDERS, FIXED, ZONE, SB_ADJ = {}, {}, {}, {}, {}


def add(ch, name, fn, fixed=None, zone=None, adj=None):
    NAMES[ch] = name
    BUILDERS[ch] = fn
    if fixed:
        FIXED[ch] = fixed
    if zone:
        ZONE[ch] = zone
    if adj:
        SB_ADJ[ch] = adj


def _comma():
    return full.p_comma()


def quoteright():
    c = _comma()
    x0, y0, x1, y1 = c.bounds
    return shift(c, 0, C - y1)


def quoteleft():
    q = quoteright()
    x0, y0, x1, y1 = q.bounds
    return transform(q, a=-1, d=-1, e=x0 + x1, f=y0 + y1)


def quotedblright():
    q = quoteright()
    return union(q, shift(q, DOT + 50))


def quotedblleft():
    q = quoteleft()
    return union(q, shift(q, DOT + 50))


def quotesinglbase():
    return _comma()


def quotedblbase():
    c = _comma()
    return union(c, shift(c, DOT + 50))


def ellipsis():
    d = full.p_period()
    return union(d, shift(d, DOT + 90), shift(d, 2 * (DOT + 90)))


def bullet():
    d = DOT * 1.25
    return _dot(d / 2, MATH_Y, d)


def periodcentered():
    return _dot(DOT / 2, MATH_Y, DOT)


add("’", "quoteright", quoteright, fixed=(45, 45))
add("‘", "quoteleft", quoteleft, fixed=(45, 45))
add("”", "quotedblright", quotedblright, fixed=(45, 45))
add("“", "quotedblleft", quotedblleft, fixed=(45, 45))
add("‚", "quotesinglbase", quotesinglbase, fixed=(40, 40))
add("„", "quotedblbase", quotedblbase, fixed=(40, 40))
add("…", "ellipsis", ellipsis, fixed=(40, 40))
add("•", "bullet", bullet, fixed=(60, 60))
add("·", "periodcentered", periodcentered, fixed=(50, 50))


# ================================================================ LATIN-1
from full import (V, H, VS, HS, RO, RI, OS, DG, K, ASC, DESC, v, h, vs, hs, ro, ri, dg, os_,
                  open_round, hook_left, cstroke, vee, ring, bowl_with_stem, rot, BIG)

CAP_MARK = (C + 70, C + 215)      # vertical zone for accents on capitals
LC_MARK = (X + 95, X + 265)       # ... and on lowercase


def m_acute(z):
    y0, y1 = z
    return polygon([(140, y1), (320, y1), (140, y0), (0, y0)])


def m_grave(z):
    y0, y1 = z
    return polygon([(0, y1), (180, y1), (320, y0), (180, y0)])


def m_circumflex(z):
    y0, y1 = z
    vv = vee(400, y1 - y0, DG * 0.78, DG * 0.78)
    return transform(vv, d=-1, f=y1)


def m_caron(z):
    y0, y1 = z
    return shift(vee(400, y1 - y0, DG * 0.78, DG * 0.78), 0, y0)


def m_dieresis(z):
    y0, y1 = z
    d = DOT * 0.85
    cy = y0 + d / 2 * P["dot_e"]
    return union(full._dot(d / 2, cy, d), full._dot(d / 2 + d + 70, cy, d))


def m_tilde(z):
    y0, y1 = z
    w, amp, t = 400, 32, H * 0.78
    n = 60
    pts_u, pts_l = [], []
    for i in range(n + 1):
        x = w * i / n
        yc = (y0 + y1) / 2 + amp * math.sin(math.pi * (2 * x / w - 0.5))
        pts_u.append((x, yc + t / 2))
        pts_l.append((x, yc - t / 2))
    return polygon(pts_u + pts_l[::-1])


def m_ring(z):
    y0, y1 = z
    d = 235
    return ring(0, y0 - 10, d, y0 - 10 + d, 62, 58, d / 2, (d - 124) / 2, k=K_CIRCLE)


def m_macron(z):
    y0, y1 = z
    return rect(0, y0 + 30, 380, y0 + 30 + H * 0.8)


def m_cedilla():
    t = 72
    stem = rect(150, -70, 150 + t, 15)
    hk = hook_left(0, 150 + t, -255, -40, 60, 58, 95, 25, stem=t)
    return union(stem, hk)


MARKS = {"acute": m_acute, "grave": m_grave, "circumflex": m_circumflex, "caron": m_caron,
         "dieresis": m_dieresis, "tilde": m_tilde, "ring": m_ring, "macron": m_macron}


def centered(mark, cx):
    x0, y0, x1, y1 = mark.bounds
    return shift(mark, cx - (x0 + x1) / 2)


def top_center(base, ch):
    x0, y0, x1, y1 = base.bounds
    cx = (x0 + x1) / 2
    # optical centres that differ from the bounding box
    if ch in "a":
        cx = x0 + (x1 - x0) * 0.47
    if ch in "y":
        cx = x0 + (x1 - x0) * 0.55
    return cx


def dotless_i():
    return rect(0, 0, v, X)


def dotless_j():
    x0 = 150
    stem = rect(x0, DESC + ro * 0.5, x0 + v, X)
    hook = hook_left(x0 + v - 330, x0 + v, DESC - os_ * 0.5, DESC + ro, v, h, ro * 0.9, ri * 0.8, stem=v)
    return union(stem, hook)


def accented(base_ch, mark):
    def fn():
        if base_ch == "i":
            base = dotless_i()
        else:
            base = full.ALL[base_ch]()
        z = CAP_MARK if base_ch.isupper() else LC_MARK
        m = MARKS[mark](z)
        if base_ch.isupper() and mark == "ring":
            m = MARKS[mark]((C + 40, C + 40))
        return union(base, centered(m, top_center(base, base_ch)))
    return fn


def cedilla_on(base_ch):
    def fn():
        base = full.ALL[base_ch]()
        x0, y0, x1, y1 = base.bounds
        c = m_cedilla()
        cx0, _, cx1, _ = c.bounds
        return union(base, shift(c, (x0 + x1) / 2 - 150 - 36))
    return fn


ACC = {
    "À": ("A", "grave"), "Á": ("A", "acute"), "Â": ("A", "circumflex"), "Ã": ("A", "tilde"),
    "Ä": ("A", "dieresis"), "Å": ("A", "ring"), "È": ("E", "grave"), "É": ("E", "acute"),
    "Ê": ("E", "circumflex"), "Ë": ("E", "dieresis"), "Ì": ("I", "grave"), "Í": ("I", "acute"),
    "Î": ("I", "circumflex"), "Ï": ("I", "dieresis"), "Ñ": ("N", "tilde"), "Ò": ("O", "grave"),
    "Ó": ("O", "acute"), "Ô": ("O", "circumflex"), "Õ": ("O", "tilde"), "Ö": ("O", "dieresis"),
    "Ù": ("U", "grave"), "Ú": ("U", "acute"), "Û": ("U", "circumflex"), "Ü": ("U", "dieresis"),
    "Ý": ("Y", "acute"), "Ÿ": ("Y", "dieresis"), "Š": ("S", "caron"), "Ž": ("Z", "caron"),
    "à": ("a", "grave"), "á": ("a", "acute"), "â": ("a", "circumflex"), "ã": ("a", "tilde"),
    "ä": ("a", "dieresis"), "å": ("a", "ring"), "è": ("e", "grave"), "é": ("e", "acute"),
    "ê": ("e", "circumflex"), "ë": ("e", "dieresis"), "ì": ("i", "grave"), "í": ("i", "acute"),
    "î": ("i", "circumflex"), "ï": ("i", "dieresis"), "ñ": ("n", "tilde"), "ò": ("o", "grave"),
    "ó": ("o", "acute"), "ô": ("o", "circumflex"), "õ": ("o", "tilde"), "ö": ("o", "dieresis"),
    "ù": ("u", "grave"), "ú": ("u", "acute"), "û": ("u", "circumflex"), "ü": ("u", "dieresis"),
    "ý": ("y", "acute"), "ÿ": ("y", "dieresis"), "š": ("s", "caron"), "ž": ("z", "caron"),
}
import unicodedata
for ch, (b, m) in ACC.items():
    nm = unicodedata.name(ch)
    glyph_name = {"Ÿ": "Ydieresis", "Š": "Scaron", "Ž": "Zcaron", "š": "scaron", "ž": "zcaron"}.get(ch, b + m)
    add(ch, glyph_name, accented(b, m), zone=((0, C), 54) if b.isupper() else ((0, X), 50))

add("Ç", "Ccedilla", cedilla_on("C"), zone=((0, C), 54))
add("ç", "ccedilla", cedilla_on("c"), zone=((0, X), 50))
add("ı", "dotlessi", dotless_i, zone=((0, X), 50))
add("ȷ", "dotlessj", dotless_j, zone=((0, X), 50))


def AE():
    d = DG * 1.02
    xt = 330
    leg = para(0, d, 0, xt - 40, xt - 40 + d, C)
    stem = rect(xt, 0, xt + V, C)
    bars = union(rect(xt - 40, C - H, xt + 520, C), rect(xt, 365 - H * 0.48, xt + 470, 365 + H * 0.48), rect(xt, 0, xt + 530, H))
    cross = rect(100, P["A_c0"], xt + 1, P["A_c1"])
    cross = inter(cross, polygon([(0, 0), (xt + V, 0), (xt + V, C), (xt - 40, C)]))
    return clip_y(union(leg, stem, bars, cross), 0, C)


def ae():
    a = full.lc_a()
    e = full.lc_e()
    return union(a, shift(e, 600 - vs - 25))


def OE():
    o = full.cap_O()
    o = diff(o, rect(560, -BIG, BIG, BIG))
    xs = 560 - V
    e = union(rect(xs, 0, xs + V, C), rect(xs, C - H, xs + 470, C), rect(xs, 365 - H * 0.48, xs + 430, 365 + H * 0.48), rect(xs, 0, xs + 480, H))
    return union(o, e)


def oe():
    o = full.lc_o()
    e = full.lc_e()
    return union(o, shift(e, 600 - vs - 25))


def Oslash():
    o = full.cap_O()
    sl = cstroke((60, -OS), (700, C + OS), DG * 0.8)
    return union(o, inter(sl, full.rrect(0, -OS, 760, C + OS, RO * 1.12, K)))


def oslash():
    o = full.lc_o()
    sl = cstroke((50, -os_), (550, X + os_), dg * 0.78)
    return union(o, inter(sl, full.rrect(0, -os_, 600, X + os_, ro, K)))


def Eth():
    return union(full.cap_D(), rect(-45, 360 - H * 0.45, V + 140, 360 + H * 0.45))


def eth():
    """Bowl a little smaller than o (a heavy eth has no room otherwise), the
    right wall runs straight up then leans back into the ascender, which ends
    flat on the ascender line; a light bar crosses it."""
    w = 575
    bt = X * 0.86
    sw = v
    lean = -0.30
    hb = hs * 0.9
    lo = ring(0, -os_, w, bt + os_, vs, hb, ro * 0.95, ri * 0.9,
              corners=(ro * 0.95, 0, ro * 0.95, ro * 0.95), icorners=(ri * 0.9, 0, ri * 0.9, ri * 0.9))
    yj = bt + os_ - hb - 40                 # where the wall starts to lean
    xr = lambda y: w + lean * (y - yj)      # right edge of wall + ascender
    lo = diff(lo, polygon([(w + 1, yj), (BIG, yj), (BIG, BIG), (xr(BIG), BIG)]))
    lo = diff(lo, polygon([(xr(yj), yj), (w + 50, yj), (w + 50, ASC + 50), (xr(ASC + 50), ASC + 50)]))
    st = polygon([(xr(yj) - sw, yj), (xr(yj), yj), (xr(ASC), ASC), (xr(ASC) - sw, ASC)])
    st = diff(st, rect(-BIG, -BIG, BIG, bt + os_ - hb + 2))
    yb = (bt + os_ + ASC) / 2 + 8
    xc = xr(yb) - sw / 2
    t = h * 0.56
    bar = rect(xc - 115, yb - t / 2, xc + 115, yb + t / 2)
    return union(lo, st, bar)


def Thorn():
    return union(rect(0, 0, V, C), bowl(0, P["P_w"], 120, C - 110, H, H, P["P_vb"], P["P_ro"], P["P_ri"], K, V))


def thorn():
    return union(full.lc_p(), rect(0, X - 10, v, ASC))


def germandbls():
    w = 560
    top = ASC
    stem = rect(0, 0, v, top - ro)
    arc = rrect(0, 420, w - 20, top + os_ * 0.6, (ro, ro, ro * 0.8, 0), K)
    arc = diff(arc, rrect(v, 420 + h, w - 20 - vs, top + os_ * 0.6 - h, (ri, ri, ri * 0.6, 0), K))
    arc = diff(arc, rect(v, 410, w * 0.42, 420 + h + 1))
    lo = open_round(w * 0.30, -os_, w + 40, 420 + h, vs, h, ro * 0.9, ri, side="left", top_term=False)
    lo = diff(lo, rect(-BIG, 420 + h - h - 1, w * 0.42, BIG))
    return union(stem, arc, lo)


from glyphs import bowl
add("Æ", "AE", AE, zone=((0, C), 54))
add("æ", "ae", ae, zone=((0, X), 50))
add("Œ", "OE", OE, zone=((0, C), 54))
add("œ", "oe", oe, zone=((0, X), 50))
add("Ø", "Oslash", Oslash, zone=((0, C), 54))
add("ø", "oslash", oslash, zone=((0, X), 50))
add("Ð", "Eth", Eth, zone=((0, C), 54))
add("ð", "eth", eth, zone=((0, X), 50))
add("Þ", "Thorn", Thorn, zone=((0, C), 54))
add("þ", "thorn", thorn, zone=((0, X), 50))
add("ß", "germandbls", germandbls, zone=((0, X), 50))


# ----------------------------------------------------- punctuation & symbols
def exclamdown():
    e = full.p_exclam()
    x0, y0, x1, y1 = e.bounds
    return transform(e, a=-1, d=-1, e=x0 + x1, f=y0 + y1 - 170 + 0)


def questiondown():
    q = full.p_question()
    x0, y0, x1, y1 = q.bounds
    return transform(q, a=-1, d=-1, e=x0 + x1, f=y0 + y1 - 170)


def guill(single, right):
    w, hh = 270, 380
    t = H * 0.80
    ang = math.atan2(hh / 2, w)
    dx, dy = t / math.sin(ang), t / math.cos(ang)
    y = MATH_Y - 20
    c = polygon([(0, y + 14), (w, y + hh / 2), (w, y + hh / 2 - dy), (dx, y), (w, y - hh / 2 + dy), (w, y - hh / 2), (0, y - 14)])
    g = c if single else union(c, shift(c, dx + 95))
    if right:
        x0, y0, x1, y1 = g.bounds
        g = mirror_x(g, (x0 + x1) / 2)
    return g


def circled(inner_fn, scale):
    def fn():
        d = 860
        ringp = ring(0, -60, d, d - 60, 78, 78, d / 2, d / 2 - 78, k=K_CIRCLE)
        inner = inner_fn()
        x0, y0, x1, y1 = inner.bounds
        inner = transform(inner, a=scale, d=scale)
        x0, y0, x1, y1 = inner.bounds
        inner = shift(inner, d / 2 - (x0 + x1) / 2, (d - 120) / 2 - (y0 + y1) / 2)
        return union(ringp, inner)
    return fn


def degree():
    d = 300
    return ring(0, C - d, d, C, 80, 80, d / 2, d / 2 - 80, k=K_CIRCLE)


def multiply():
    t = H * 0.95
    a = rect(-t / 2, -230, t / 2, 230)
    cx, cy = 230, MATH_Y
    return union(rot(shift(a, cx, cy), math.radians(45), cx, cy), rot(shift(a, cx, cy), math.radians(-45), cx, cy))


def divide():
    d = DOT * 0.9
    return union(full.p_minus(), full._dot(280, MATH_Y + 150, d), full._dot(280, MATH_Y - 150 - 0, d))


def plusminus():
    t = H * 0.9
    w = 540
    return union(rect(0, MATH_Y + 30 - t / 2, w, MATH_Y + 30 + t / 2),
                 rect(w / 2 - t / 2, MATH_Y + 30 - 230, w / 2 + t / 2, MATH_Y + 30 + 230),
                 rect(0, -10, w, -10 + t))


def euro():
    c = full.cap_C()
    t = H * 0.8
    return union(c, rect(-60, 400, 470, 400 + t), rect(-60, 230, 430, 230 + t))


def sterling():
    w = 600
    x0 = 70
    arc = open_round(x0, 330, x0 + 470, C + OS, VS * 0.95, HS * 0.95, RO, RI, bot_term=False, keep_from=-BIG)
    arc = diff(arc, rect(-BIG, -BIG, BIG, 360))
    arc = diff(arc, rect(x0 + VS * 0.95, -BIG, BIG, C + OS - HS * 0.95))
    arc = union(arc, rect(x0, 0, x0 + VS * 0.95, 420))
    # top terminal on the right
    stem = rect(x0, 0, x0 + V, 470)
    bar = rect(0, 300, 430, 300 + H * 0.9)
    base = rect(0, 0, w, H)
    top = open_round(x0, 200, x0 + 470, C + OS, VS * 0.95, HS * 0.95, RO, RI, keep_from=-BIG, bot_term=False)
    top = diff(top, rect(-BIG, -BIG, BIG, 420))
    top = diff(top, rect(x0 + VS * 0.95, -BIG, BIG, C + OS - HS * 0.95))
    return union(top, rect(x0, 0, x0 + VS * 0.95, 430), bar, base)


def yen():
    y = full.cap_Y()
    t = H * 0.8
    return union(y, rect(90, 230, 635, 230 + t), rect(90, 60, 635, 60 + t))


def cent():
    c = full.lc_c()
    t = v * 0.62
    return union(c, rect(290 - t / 2, -110, 290 + t / 2, X + 110))


def logicalnot():
    t = H * 0.95
    return union(rect(0, MATH_Y, 540, MATH_Y + t), rect(540 - t * 1.05, MATH_Y - 170, 540, MATH_Y + t))


def brokenbar():
    return union(rect(0, -170, V * 0.9, 240), rect(0, 360, V * 0.9, C + 110))


def micro():
    u = full.lc_u()
    return union(u, rect(0, DESC, v, 100))


def spacing_mark(name, z=None):
    def fn():
        return MARKS[name](z or (C + 30, C + 200))
    return fn


add("¡", "exclamdown", exclamdown, fixed=(50, 50))
add("¿", "questiondown", questiondown, fixed=(45, 40))
add("«", "guillemotleft", lambda: guill(False, False), fixed=(40, 40))
add("»", "guillemotright", lambda: guill(False, True), fixed=(40, 40))
add("‹", "guilsinglleft", lambda: guill(True, False), fixed=(40, 40))
add("›", "guilsinglright", lambda: guill(True, True), fixed=(40, 40))
add("©", "copyright", circled(full.cap_C, 0.55), fixed=(50, 50))
add("®", "registered", circled(full.cap_R, 0.55), fixed=(50, 50))
add("°", "degree", degree, fixed=(50, 50))
add("×", "multiply", multiply, fixed=(50, 50))
add("÷", "divide", divide, fixed=(45, 45))
add("±", "plusminus", plusminus, fixed=(45, 45))
add("€", "Euro", euro, fixed=(30, 40))
add("£", "sterling", sterling, fixed=(35, 35))
add("¥", "yen", yen, fixed=(15, 15))
add("¢", "cent", cent, fixed=(45, 35))
add("¬", "logicalnot", logicalnot, fixed=(45, 45))
add("¦", "brokenbar", brokenbar, fixed=(70, 70))
add("µ", "mu", micro, zone=((0, X), 50))
add("´", "acute", spacing_mark("acute"), fixed=(50, 50))
add("¨", "dieresis", spacing_mark("dieresis"), fixed=(50, 50))
add("¯", "macron", spacing_mark("macron"), fixed=(40, 40))
add("¸", "cedilla", m_cedilla, fixed=(50, 50))
add("ˆ", "circumflex", spacing_mark("circumflex"), fixed=(40, 40))
add("˜", "tilde", spacing_mark("tilde"), fixed=(40, 40))
add("ˇ", "caron", spacing_mark("caron"), fixed=(40, 40))
add("˚", "ring", spacing_mark("ring"), fixed=(50, 50))


def arrow_up_right():
    """↗ for links that leave the site: a diagonal shaft into a corner head,
    bars at cap-bar weight."""
    s0, s1 = 90, 610                      # box bottom/top
    w = s1 - s0
    t = H * 0.95
    head_top = rect(w * 0.32, s1 - t, w, s1)
    head_side = rect(w - V * 0.95, s1 - w * 0.68, w, s1)
    shaft = cstroke((t * 0.75, s0), (w - t * 0.6, s1 - t * 0.6), t * 1.38)
    shaft = inter(shaft, rect(-BIG, s0, w, s1))   # tip stays inside the head
    return union(head_top, head_side, shaft)


add("↗", "arrowupright", arrow_up_right, fixed=(40, 40))
