"""Build the WASM.RIP font: spacing, slant, kerning, OTF + WOFF2."""
import json, math, sys
import numpy as np
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont
import pathops
import full, space, extra
from kit import transform, bounds

SLANT = full.P["slant"]
SHEAR_Y = full.X / 2          # skew around mid x-height, the usual italic origin

# ------------------------------------------------------------------ glyphs
NAMES = {
    " ": "space", " ": "uni00A0", ".": "period", ",": "comma", ":": "colon", ";": "semicolon",
    "!": "exclam", "?": "question", "'": "quotesingle", '"': "quotedbl", "-": "hyphen",
    "–": "endash", "—": "emdash", "_": "underscore", "/": "slash", "\\": "backslash",
    "|": "bar", "(": "parenleft", ")": "parenright", "[": "bracketleft", "]": "bracketright",
    "{": "braceleft", "}": "braceright", "+": "plus", "−": "minus", "=": "equal", "<": "less",
    ">": "greater", "*": "asterisk", "^": "asciicircum", "~": "asciitilde", "`": "grave",
    "#": "numbersign", "$": "dollar", "%": "percent", "&": "ampersand", "@": "at",
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
    "7": "seven", "8": "eight", "9": "nine",
}
NAMES.update(extra.NAMES)
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
    NAMES[c] = c

BUILDERS = dict(full.ALL)
BUILDERS.update(extra.BUILDERS)

# fixed sidebearings (left, right) for marks whose spacing isn't about a zone
FIXED = {
    ".": (40, 40), ",": (40, 40), ":": (45, 45), ";": (45, 45), "!": (50, 50), "?": (40, 45),
    "'": (50, 50), '"': (50, 50), "-": (35, 35), "–": (25, 25), "—": (0, 0),
    "_": (0, 0), "/": (10, 10), "\\": (10, 10), "|": (70, 70), "(": (60, 20), ")": (20, 60),
    "[": (65, 20), "]": (20, 65), "{": (45, 20), "}": (20, 45), "+": (45, 45), "−": (45, 45),
    "=": (45, 45), "<": (45, 45), ">": (45, 45), "*": (40, 40), "^": (40, 40), "~": (45, 45),
    "`": (60, 60), "#": (30, 30), "%": (40, 40), "&": (35, 15), "@": (45, 45),
}
FIXED.update(extra.FIXED)
SPACE_W = 240

CAP_BASE, LC_BASE, FIG_BASE = 54, 50, 50
DEPTH, FACTOR, MINSB = 140, 0.40, 8


def zone_for(ch):
    if ch in extra.ZONE:
        return extra.ZONE[ch]
    if ch.isupper() or ch.isdigit() or ch in "$":
        return (0, full.C), (FIG_BASE if ch.isdigit() else CAP_BASE)
    return (0, full.X), LC_BASE


def make_glyphs(chars):
    out = {}
    for ch in chars:
        if ch in (" ", " "):
            out[ch] = (None, SPACE_W)
            continue
        p = BUILDERS[ch]()
        p = union_clean(p)
        x0, y0, x1, y1 = bounds(p)
        if ch in FIXED:
            lsb, rsb = FIXED[ch]
        else:
            (zone, base) = zone_for(ch)
            lsb, rsb, _, _ = space.sidebearings(p, zone, base, DEPTH, FACTOR, MINSB)
            if ch in extra.SB_ADJ:
                dl, dr = extra.SB_ADJ[ch]
                lsb += dl; rsb += dr
        p = transform(p, e=lsb - x0)
        adv = round(lsb + (x1 - x0) + rsb)
        out[ch] = (p, adv)
    return out


def union_clean(p):
    q = pathops.Path()
    q = pathops.op(q, p, pathops.PathOp.UNION)
    return q


def slanted(p):
    return transform(p, c=SLANT, e=-SLANT * SHEAR_Y)


# ----------------------------------------------------------------- kerning
KERN_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;-'\")]}!?&/"


def kern_profiles(glyphs, chars):
    """Horizontal margins of each upright glyph (already spaced) per scanline."""
    prof = {}
    ys = np.arange(full.DESC, full.ASC + 1, 10)
    for ch in chars:
        p, adv = glyphs[ch]
        if p is None:
            continue
        (gx0, gx1), L, R = space.profile(p, ys[0], ys[-1])
        x0, y0, x1, y1 = bounds(p)
        left = [None if v is None else x0 + v for v in L]          # ink start from origin
        right = [None if v is None else (adv - x1) + v for v in R]   # ink end to advance
        prof[ch] = (left, right)
    return ys, prof


def kerning(glyphs):
    chars = [c for c in KERN_CHARS if c in glyphs]
    ys, prof = kern_profiles(glyphs, chars)
    pairs = {}
    for a in chars:
        ra = prof[a][1]
        for b in chars:
            lb = prof[b][0]
            gaps = [x + y for x, y in zip(ra, lb) if x is not None and y is not None]
            if not gaps:
                continue
            g = np.array(gaps)
            near = np.percentile(g, 15)
            tgt = 128 if (a.isupper() or b.isupper()) else 112
            k = 0.78 * (tgt - near)
            k = max(-185, min(0, k))
            # never let shapes get closer than 22 units
            k = max(k, 22 - g.min())
            k = int(round(k / 5) * 5)
            if abs(k) >= 15:
                pairs[(a, b)] = k
    return pairs


# ------------------------------------------------------------------- build
def build(chars, out_base, family="WASM.RIP", style="Black Italic"):
    glyphs = make_glyphs(chars)
    order = [".notdef"] + [NAMES[c] for c in chars]
    cmap = {ord(c): NAMES[c] for c in chars}
    charstrings, metrics = {}, {}
    upm = 1000

    def draw(path, adv):
        pen = T2CharStringPen(adv, None)
        if path is not None:
            rec = RecordingPen()
            path.draw(rec)
            # CFF wants counter-clockwise outer contours; pathops gives clockwise
            rec.replay(ReverseContourPen(pen))
        return pen.getCharString()

    nd = pathops.Path()
    nd = pathops.op(full.rect(60, 0, 440, 700), full.rect(120, 60, 380, 640), pathops.PathOp.DIFFERENCE)
    charstrings[".notdef"] = draw(nd, 500)
    metrics[".notdef"] = (500, 60)
    for c in chars:
        p, adv = glyphs[c]
        name = NAMES[c]
        if p is not None:
            sp = slanted(p)
            b = bounds(sp)
            lsb = int(math.floor(b[0]))
        else:
            sp, lsb = None, 0
        charstrings[name] = draw(sp, adv)
        metrics[name] = (adv, lsb)

    fb = FontBuilder(upm, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    ps = family.replace(".", "").replace(" ", "") + "-" + style.replace(" ", "")
    fb.setupCFF(ps, {"FullName": f"{family} {style}"}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    asc, desc = 960, -270
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0, caretSlopeRise=1000, caretSlopeRun=round(SLANT * 1000))
    fb.setupNameTable({
        "familyName": family,
        "styleName": "Italic",
        "typographicFamily": family,
        "typographicSubfamily": style,
        "uniqueFontIdentifier": f"{ps};1.000",
        "fullName": f"{family} {style}",
        "psName": ps,
        "version": "Version 1.000",
        "copyright": "Copyright 2026 wasm.rip",
        "designer": "wasm.rip",
        "description": "Display face drawn from the WASM.RIP logo lettering.",
    })
    fb.setupOS2(version=4,
        sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
        usWinAscent=asc + 40, usWinDescent=-desc + 40,
        sxHeight=full.X, sCapHeight=full.C, usWeightClass=900,
        fsSelection=0b0000001 | (1 << 7),  # italic, use typo metrics
        achVendID="WRIP", usFirstCharIndex=32, usLastCharIndex=max(cmap),
    )
    fb.setupPost(italicAngle=-math.degrees(math.atan(SLANT)), underlinePosition=-150, underlineThickness=90)
    fb.font["head"].macStyle = 0b11  # bold + italic
    pairs = kerning(glyphs)
    fea = "languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nfeature kern {\n"
    for (a, b), k in sorted(pairs.items()):
        fea += f"  pos {NAMES[a]} {NAMES[b]} {k};\n"
    fea += "} kern;\n"
    addOpenTypeFeaturesFromString(fb.font, fea)
    fb.save(out_base + ".otf")
    f = TTFont(out_base + ".otf")
    f.flavor = "woff2"
    f.save(out_base + ".woff2")
    json.dump({f"{a}{b}": k for (a, b), k in pairs.items()}, open("kern-pairs.json", "w"), indent=0)
    return glyphs, pairs


if __name__ == "__main__":
    chars = [" ", " "] + list(full.ALL.keys()) + list(extra.BUILDERS.keys())
    g, k = build(chars, "../fonts/WasmRip-BlackItalic")
    print(len(chars), "glyphs,", len(k), "kern pairs")
