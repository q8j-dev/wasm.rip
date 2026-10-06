#!/usr/bin/env python3
"""Render the WASM.RIP logo from its model, at any size.

    pip install numpy pillow
    python3 render.py                    # 4096px: background.png, wasm-rip-logo.svg, wasm-rip-logo.png
    python3 render.py --size 8192        # any size

Nothing here is a copy of the original image. Every layer is drawn from the
files in model/:

  stars.csv     every star: position, brightness, width
  streaks.json  the faint diagonal streaks: a line and a brightness profile each
  flare.json    the big star on the left: radial glow plus eight spikes
  nebula.npz    the clouds: elliptical gaussian brush strokes in two sizes
  text.json     where each letter of WASM.RIP sits, its size, and the grey gradient
  meta.json     the blur the original 512px image has (source_blur, in its pixels)

Positions and sizes are in units of the original 512px logo, so changing a
number in model/ moves things the same way at every output size.
"""
import argparse, base64, csv, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "model")
FONT = os.path.join(HERE, "..", "fonts", "WasmRip-BlackItalic.otf")
FONT_WOFF2 = os.path.join(HERE, "..", "fonts", "WasmRip-BlackItalic.woff2")
BASE = 512  # the original logo's size; model units are its pixels


def load_model():
    stars = np.array([[float(r["x"]), float(r["y"]), float(r["flux"]), float(r["sigma"])]
                      for r in csv.DictReader(open(os.path.join(MODEL, "stars.csv")))])
    streaks = json.load(open(os.path.join(MODEL, "streaks.json")))
    flare = json.load(open(os.path.join(MODEL, "flare.json")))
    nebula = np.load(os.path.join(MODEL, "nebula.npz"))
    text = json.load(open(os.path.join(MODEL, "text.json")))
    meta = json.load(open(os.path.join(MODEL, "meta.json")))
    return stars, streaks, flare, nebula, text, meta


def add_gaussian(out, hx, hy, sig, flux):
    rad = int(np.ceil(4 * sig)) + 1
    H, W = out.shape
    x0, y0 = int(round(hx)), int(round(hy))
    xa, xb, ya, yb = max(x0 - rad, 0), min(x0 + rad + 1, W), max(y0 - rad, 0), min(y0 + rad + 1, H)
    if xa >= xb or ya >= yb:
        return
    gx = np.exp(-0.5 * ((np.arange(xa, xb) - hx) / sig) ** 2)
    gy = np.exp(-0.5 * ((np.arange(ya, yb) - hy) / sig) ** 2)
    out[ya:yb, xa:xb] += flux / (2 * np.pi * sig * sig) * np.outer(gy, gx)


def render_strokes(cx, cy, s1, s2, th, F, f, size):
    """Elliptical gaussians on a size x size canvas (f output px per model px).
    Each pixel gets the gaussian's average over its area."""
    out = np.zeros(size * size)
    R = int(np.ceil(3 * max(s1.max(), s2.max()) * f)) + 1
    o = np.arange(-R, R + 1)
    oy, ox = [a.ravel() for a in np.meshgrid(o, o, indexing="ij")]
    chunk = max(1, int(4e7 // len(ox)))
    pix = 1.0 / (12 * f * f)
    for i in range(0, len(F), chunk):
        sl = slice(i, i + chunk)
        ax = np.round((cx[sl] + 0.5) * f - 0.5).astype(np.int64)
        ay = np.round((cy[sl] + 0.5) * f - 0.5).astype(np.int64)
        px = ax[:, None] + ox[None]; py = ay[:, None] + oy[None]
        dx = (px + 0.5) / f - 0.5 - cx[sl, None]; dy = (py + 0.5) / f - 0.5 - cy[sl, None]
        c, s = np.cos(th[sl])[:, None], np.sin(th[sl])[:, None]
        v1, v2 = (s1[sl] ** 2)[:, None], (s2[sl] ** 2)[:, None]
        a = v1 * c * c + v2 * s * s + pix; b = (v1 - v2) * c * s; d = v1 * s * s + v2 * c * c + pix
        det = a * d - b * b
        val = F[sl, None] / (2 * np.pi * np.sqrt(det)) * np.exp(-0.5 * (d * dx * dx - 2 * b * dx * dy + a * dy * dy) / det)
        ok = (px >= 0) & (px < size) & (py >= 0) & (py < size)
        out += np.bincount((py * size + px)[ok], weights=val[ok], minlength=size * size)
    return out.reshape(size, size)


def gaussian_blur(img, sigma):
    """gaussian blur through the FFT (wraps at the edges; fine for these widths)"""
    H, W = img.shape
    ky = np.fft.fftfreq(H)[:, None]; kx = np.fft.rfftfreq(W)[None, :]
    G = np.exp(-2 * np.pi ** 2 * sigma ** 2 * (kx ** 2 + ky ** 2))
    return np.fft.irfft2(np.fft.rfft2(img) * G, s=img.shape)


def sharpen_clouds(neb, f, amount):
    """Firmer cloud edges at high resolution. Whatever the sharpening would change
    at the original's 512px scale is taken back out, so it only adds crispness."""
    if amount <= 0:
        return neb
    d = amount * (neb - gaussian_blur(neb, 1.2 * f))
    return neb + d - gaussian_blur(d, 0.6 * f)


def upscale(img, size):
    if img.shape[0] == size:
        return img
    return np.asarray(Image.fromarray(img.astype(np.float32), mode="F").resize((size, size), Image.BICUBIC))


def render_background(size=4096, parts=("nebula", "stars", "streaks", "flare")):
    stars, streaks, flare, nebula, _, meta = load_model()
    blur = meta["source_blur"]
    f = size / BASE
    to_px = lambda v: (np.asarray(v) + 0.5) * f - 0.5
    out = np.zeros((size, size), np.float32)

    # nebula: each stroke layer is drawn at the resolution where its narrowest
    # stroke is still smooth, then scaled up (the same as supersampling)
    if "nebula" in parts:
        neb = np.zeros((size, size), np.float32)
        for layer in sorted({k.split("_")[0] for k in nebula.files}):
            p = {k[len(layer) + 1:]: nebula[k] for k in nebula.files if k.startswith(layer + "_")}
            fl = int(min(f, max(1, np.ceil(1.2 / max(p["s2"].min(), p["s1"].min(), 0.3)))))
            neb += upscale(render_strokes(p["cx"], p["cy"], p["s1"], p["s2"], p["th"], p["F"], fl, BASE * fl), size)
        out += sharpen_clouds(neb, f, meta.get("cloud_sharpen", 0.0)).astype(np.float32)

    # stars: small ones at their real width (the measured width with the original's
    # blur taken out); bigger ones as a crisp core inside a soft halo, sized so that
    # with the original's blur they look exactly as measured
    shapes = np.array(meta["star_shapes"]); core = meta["star_core_sigma"]
    for x, y, F, s in (stars if "stars" in parts else []):
        hx, hy = to_px(x), to_px(y)
        if s < shapes[0, 0]:
            add_gaussian(out, hx, hy, max(f * np.sqrt(max(s * s - blur * blur, 0.0)), 0.12 * f, 0.7), F * f * f)
        else:
            a = np.interp(s, shapes[:, 0], shapes[:, 1]); halo = np.interp(s, shapes[:, 0], shapes[:, 2])
            add_gaussian(out, hx, hy, max(core * f, 0.7), a * F * f * f)
            add_gaussian(out, hx, hy, halo * f, (1 - a) * F * f * f)

    # streaks: straight lines with a measured brightness profile along them
    width = flare["streak_width"] * f
    for d in (streaks if "streaks" in parts else []):
        (cx, cy), (ux, uy) = d["c"], d["u"]
        ts, I = np.array(d["ts"]), np.array(d["I"])
        nz = np.nonzero(I > 0)[0]
        if len(nz) == 0:
            continue
        ends = to_px([[cx + ux * ts[nz[0]], cy + uy * ts[nz[0]]], [cx + ux * ts[nz[-1]], cy + uy * ts[nz[-1]]]])
        pad = int(6 * width) + 4
        xa, xb = int(max(ends[:, 0].min() - pad, 0)), int(min(ends[:, 0].max() + pad, size))
        ya, yb = int(max(ends[:, 1].min() - pad, 0)), int(min(ends[:, 1].max() + pad, size))
        if xa >= xb or ya >= yb:
            continue
        Y, X = np.mgrid[ya:yb, xa:xb].astype(np.float32)
        Xl, Yl = (X + 0.5) / f - 0.5, (Y + 0.5) / f - 0.5
        t = (Xl - cx) * ux + (Yl - cy) * uy
        dn = (-(Xl - cx) * uy + (Yl - cy) * ux) * f
        A = np.interp(t, ts, I, left=0, right=0) * f / (np.sqrt(2 * np.pi) * width)
        out[ya:yb, xa:xb] += A * np.exp(-0.5 * (dn / width) ** 2)

    # flare: a radial glow and eight spikes
    if "flare" not in parts:
        return np.clip(out, 0, 255)
    hx, hy = to_px(flare["x"]), to_px(flare["y"])
    R0 = int(64 * f)
    ya, yb, xa, xb = max(int(hy - R0), 0), min(int(hy + R0), size), max(int(hx - R0), 0), min(int(hx + R0), size)
    Yh, Xh = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    out[ya:yb, xa:xb] += np.interp(np.hypot(Xh - hx, Yh - hy) / f, flare["glow_r"], flare["glow"], right=0)
    sw = flare["spike_width"] * f
    for sp in flare["spikes"]:
        a = np.deg2rad(sp["angle"]); ux, uy = np.cos(a), np.sin(a)
        t = ((Xh - hx) * ux + (Yh - hy) * uy) / f
        dn = -(Xh - hx) * uy + (Yh - hy) * ux
        sig = sw * (1 + 0.6 * np.clip(t, 0, None) / 40)
        out[ya:yb, xa:xb] += np.where(t > 0, np.interp(t, sp["r"], sp["amp"]) * np.exp(-0.5 * (dn / sig) ** 2) * sw / sig, 0)

    return np.clip(out, 0, 255)


def gradient(text, y_model):
    t = np.clip((y_model - text["gradient_top"]) / (text["gradient_bottom"] - text["gradient_top"]), 0, 1)
    c0, c1, c2 = text["stops"]
    # straight lines between the three stops, the same as the SVG gradient
    return np.where(t < 0.5, c0 + (c1 - c0) * t * 2, c1 + (c2 - c1) * (t - 0.5) * 2)


def write_svg(path, background_name, size):
    _, _, _, _, text, _ = load_model()
    f = size / BASE
    font = base64.b64encode(open(FONT_WOFF2, "rb").read()).decode()
    c = [round(v) for v in text["stops"]]
    spans = "".join(
        f'<tspan x="{L["x"] * f:.1f}" y="{L["baseline"] * f:.1f}" font-size="{L["size"] * f:.1f}">{L["ch"]}</tspan>'
        for L in text["letters"])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <style>
    @font-face {{ font-family: "WASM.RIP"; font-weight: 900; src: url(data:font/woff2;base64,{font}) format("woff2"); }}
    .mark {{ font-family: "WASM.RIP"; font-weight: 900; font-kerning: none; text-rendering: geometricPrecision; }}
  </style>
  <defs>
    <!-- near-white at the top of the capitals, a little greyer at the baseline -->
    <linearGradient id="shade" gradientUnits="userSpaceOnUse" x1="0" y1="{text["gradient_top"] * f:.1f}" x2="0" y2="{text["gradient_bottom"] * f:.1f}">
      <stop offset="0" stop-color="rgb({c[0]},{c[0]},{c[0]})"/>
      <stop offset="0.5" stop-color="rgb({c[1]},{c[1]},{c[1]})"/>
      <stop offset="1" stop-color="rgb({c[2]},{c[2]},{c[2]})"/>
    </linearGradient>
  </defs>
  <!-- layer 1: the starfield, rendered by render.py from model/ -->
  <image href="{background_name}" x="0" y="0" width="{size}" height="{size}"/>
  <!-- layer 2: the lettering, live text; each tspan is one letter -->
  <text class="mark" fill="url(#shade)">{spans}</text>
</svg>
'''
    open(path, "w").write(svg)


def flatten(bg, size):
    """Background plus lettering in one image (FreeType text, for a quick PNG)."""
    _, _, _, _, text, _ = load_model()
    f = size / BASE
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    for L in text["letters"]:
        d.text((L["x"] * f, L["baseline"] * f), L["ch"], font=ImageFont.truetype(FONT, int(round(L["size"] * f))),
               fill=255, anchor="ls")
    a = np.asarray(mask, np.float32) / 255
    shade = gradient(text, (np.arange(size)[:, None] + 0.5) / f - 0.5)
    return bg * (1 - a) + shade * a


def to_8bit(img):
    """Quantise with a little triangular dither so smooth dark gradients don't band."""
    rng = np.random.default_rng(0)
    return np.clip(img + rng.random(img.shape) - rng.random(img.shape) + 0.5, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=4096)
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--parts", default="nebula,stars,streaks,flare", help="render only some layers, e.g. --parts stars")
    args = ap.parse_args()
    bg = render_background(args.size, tuple(args.parts.split(",")))
    Image.fromarray(to_8bit(bg)).save(os.path.join(args.out, "background.png"), optimize=True)
    write_svg(os.path.join(args.out, "wasm-rip-logo.svg"), "background.png", args.size)
    Image.fromarray(to_8bit(flatten(bg, args.size))).save(os.path.join(args.out, "wasm-rip-logo.png"), optimize=True)
    print("wrote background.png, wasm-rip-logo.svg, wasm-rip-logo.png at", args.size)
