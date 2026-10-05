"""Fit glyph parameters so each construction, pushed through the same
blur/threshold the logo went through, overlaps the traced logo letter."""
import json, sys
import numpy as np, cv2
from PIL import Image
from scipy.optimize import minimize
import glyphs
from kit import shear, raster

meas = json.load(open("logo-trace/meas.json"))
U, T, BASE = meas["U"], meas["t"], meas["base"]
mask = (np.array(Image.open("logo-trace/trace-mask.png")) > 0).astype(np.uint8)
n, lab, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
order = sorted(range(1, n), key=lambda i: stats[i][0])
NAMES = ["W", "A", "S", "M", "period", "R", "I", "P"]
ROW0, ROW1 = 140, 800  # crop rows (multiple of 10 tall)
targets = {}
for nm, i in zip(NAMES, order):
    x, y, w, h, a = stats[i]
    x0 = (x - 80) // 10 * 10
    x1 = x0 + ((w + 160) // 10 + 1) * 10
    t = (lab[ROW0:ROW1, x0:x1] == i).astype(np.uint8)
    targets[nm] = (t, x0)


def simulate(path, width, height, ox):
    """Render (sheared) path at trace resolution the way the logo was made:
    soft at 512px, upscaled, blurred and thresholded like trace-mask.png."""
    sp = shear(path, T)
    img = raster(sp, 1 / U, width, height, ox, BASE - ROW0, ss=2).astype(np.float32) / 255
    small = cv2.resize(img, (width // 10, height // 10), interpolation=cv2.INTER_AREA)
    lvl = 16 + (250 - 16) * small
    big = np.array(Image.fromarray(lvl.astype(np.float32), mode="F").resize((width, height), Image.LANCZOS))
    big = cv2.GaussianBlur(big, (0, 0), 3.5)
    return (big > 175).astype(np.uint8)


def iou(nm, p, return_img=False):
    t, x0 = targets[nm]
    H, W = t.shape
    try:
        path = glyphs.LOGO[nm](p)
        s = simulate(path, W, H, 80)
    except Exception:
        return 0.0
    if s.sum() == 0:
        return 0.0
    # align horizontally by centroid (the glyph's x origin is arbitrary here)
    cx_s = (s.sum(0) * np.arange(W)).sum() / s.sum()
    cx_t = (t.sum(0) * np.arange(W)).sum() / t.sum()
    dx = int(round(cx_t - cx_s))
    s = np.roll(s, dx, axis=1)
    inter_ = (s & t).sum()
    uni = (s | t).sum()
    v = inter_ / uni
    if return_img:
        return v, s, t
    return v


KEYS = {
    "I": ["V"],
    "period": ["dot", "dot_e", "dot_y"],
    "P": ["P_w", "P_b", "P_ht", "P_hb", "P_vb", "P_ro", "P_ri", "k"],
    "R": ["R_w", "R_b", "R_ht", "R_hb", "R_vb", "R_ro", "R_ri", "R_lx", "R_ltx", "R_ld"],
    "A": ["A_w", "A_d", "A_t", "A_c0", "A_c1"],
    "M": ["M_w", "M_d", "M_x0", "M_f", "M_vb"],
    "W": ["W_w", "W_d1", "W_d2", "W_bl", "W_f1", "W_mt"],
    "S": ["S_xu0", "S_xu1", "S_xl0", "S_xl1", "S_vs", "S_ht", "S_hm", "S_hb", "S_ym",
          "S_rou", "S_riu", "S_rol", "S_ril", "S_xt", "S_st", "S_xb", "S_sb", "S_os", "S_rt", "S_tL", "S_td", "S_bL", "S_bd"],
}


def fit(nm, iters=800, restarts=0, seed=1):
    keys = KEYS[nm]
    p = dict(glyphs.P)
    x0 = np.array([p[k] for k in keys], float)
    scale = np.array([0.05 if k in ("k", "S_st", "S_sb", "dot_e") else 20.0 for k in keys])

    def f(z):
        q = dict(p)
        for k, v in zip(keys, x0 + z * scale):
            q[k] = float(v)
        return 1 - iou(nm, q)

    before = 1 - f(np.zeros(len(keys)))
    best = None
    for start in range(2):
        z0 = np.zeros(len(keys)) if best is None else best.x
        sim = np.vstack([z0] + [z0 + np.eye(len(keys))[i] * (1.0 if start == 0 else 0.4) for i in range(len(keys))])
        r = minimize(f, z0, method="Nelder-Mead", options={"maxiter": iters, "xatol": 0.02, "fatol": 1e-6, "initial_simplex": sim})
        if best is None or r.fun < best.fun:
            best = r
    rng = np.random.default_rng(seed)
    for _ in range(restarts):
        z0 = best.x + rng.normal(0, 0.8, len(keys))
        sim = np.vstack([z0] + [z0 + np.eye(len(keys))[i] * 0.7 for i in range(len(keys))])
        r = minimize(f, z0, method="Nelder-Mead", options={"maxiter": iters, "xatol": 0.02, "fatol": 1e-6, "initial_simplex": sim})
        if r.fun < best.fun:
            best = r
    out = {k: float(v) for k, v in zip(keys, x0 + best.x * scale)}
    print(f"{nm}: IoU {before:.4f} -> {1 - best.fun:.4f}")
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    restarts = 0
    if args and args[0].startswith("-r"):
        restarts = int(args[0][2:]); args = args[1:]
    names = args or NAMES
    try:
        saved = json.load(open("params.json"))
    except FileNotFoundError:
        saved = {}
    for nm in names:
        res = fit(nm, restarts=restarts)
        saved.update(res)
        glyphs.P.update(res)
        json.dump(saved, open("params.json", "w"), indent=1)
