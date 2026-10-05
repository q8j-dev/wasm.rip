#!/usr/bin/env python3
"""Turn the source site into the fast version that gets deployed.

    python3 tools/build.py [site-dir]

Runs in place on site-dir (default: the repo root), so only run it on a
throwaway checkout, which is what the deploy workflows do. Locally, the
plain source files work fine as they are; this only makes them faster.

What it does:
  1. Makes small AVIF and WebP thumbnails for every game image (img/t/).
     Ones that are already there and up to date get skipped, so adding a
     game to games.json is all anyone needs to do.
  2. Puts styles.css, script.js, games.json and members.json straight into
     index.html, so the first response has everything needed to draw the
     page and no second round trip is needed.
  3. Inlines a tiny subset of the brand font for the first screen's text.
  4. Shrinks index.html: strips comments and indentation, rounds the logo
     paths to the precision they're actually drawn at, and moves the logos
     into one SVG sprite (img/logos.<hash>.svg) that script.js loads once
     the page has finished loading.

Needs Pillow and fontTools (pip install pillow fonttools brotli).
"""

import base64
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)

# cards are drawn 157 to 286 css px wide; these cover 1x screens up to 3x
# phones without sending much more than is shown
THUMB_WIDTHS = (300, 400, 500, 600)
THUMB_RATIO = 16 / 10  # same as .port .thumb in styles.css
THUMB_DIR = "img/t"


# ---------------------------------------------------------------- thumbnails


def thumb_base(image_url):
    """img/tchamp/img.png -> img/t/tchamp-img"""
    stem = re.sub(r"^img/", "", image_url)
    stem = re.sub(r"\.[a-z0-9]+$", "", stem, flags=re.I)
    return f"{THUMB_DIR}/{re.sub(r'[^A-Za-z0-9_-]+', '-', stem)}"


def make_thumbs(games):
    manifest_path = ROOT / THUMB_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    (ROOT / THUMB_DIR).mkdir(parents=True, exist_ok=True)
    made = 0

    for game in games:
        url = game["imageUrl"].lstrip("/")
        src = ROOT / url
        if re.match(r"^https?://", game["imageUrl"]) or not src.is_file():
            continue
        base = thumb_base(url)
        digest = hashlib.sha1(src.read_bytes()).hexdigest()
        outputs = [ROOT / f"{base}-{w}.{ext}" for w in THUMB_WIDTHS for ext in ("avif", "webp")]
        if manifest.get(url) == digest and all(p.exists() for p in outputs):
            game["thumb"] = base
            continue

        im = Image.open(src)
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        # crop to the card's shape from the centre, like object-fit: cover does
        w, h = im.size
        if w / h > THUMB_RATIO:
            cw = round(h * THUMB_RATIO)
            im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
        else:
            ch = round(w / THUMB_RATIO)
            im = im.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
        # cards have a black background, so flatten any transparency onto it
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (0, 0, 0))
            bg.paste(im, mask=im.getchannel("A"))
            im = bg

        for tw in THUMB_WIDTHS:
            # never upscale; a small source just gets a small file
            th = round(tw / THUMB_RATIO)
            out = im if im.width <= tw else im.resize((tw, th), Image.LANCZOS)
            out.save(ROOT / f"{base}-{tw}.avif", quality=58, speed=4)
            out.save(ROOT / f"{base}-{tw}.webp", quality=78, method=6)
        manifest[url] = digest
        game["thumb"] = base
        made += 1

    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(f"thumbnails: {made} made, {sum('thumb' in g for g in games) - made} already there")


# ---------------------------------------------------------------- minifying


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,>~])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip()


def minify_js(js):
    # comments on their own lines and indentation only; anything cleverer
    # needs a real parser
    out = []
    for line in js.splitlines():
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        out.append(s)
    return "\n".join(out)


NUM = re.compile(r"-?(?:\d+\.\d*|\.\d+|\d+)(?:e-?\d+)?")


def round_path(d, decimals):
    """Round every number in a path, keeping the path valid."""
    out = []
    pos = 0
    prev_has_dot = False
    for m in NUM.finditer(d):
        out.append(d[pos:m.start()])
        v = round(float(m.group()), decimals)
        s = f"{v:.{decimals}f}".rstrip("0").rstrip(".") if decimals else str(int(v))
        if s in ("-0", ""):
            s = "0"
        if s.startswith("0."):
            s = s[1:]
        elif s.startswith("-0."):
            s = "-" + s[2:]
        # a number that directly follows another needs a separator unless it
        # starts with "-", or with "." after a number that already has a dot
        if out and m.start() == pos and pos > 0:
            if not (s.startswith("-") or (s.startswith(".") and prev_has_dot)):
                out.append(" ")
        out.append(s)
        prev_has_dot = "." in s
        pos = m.end()
    out.append(d[pos:])
    return "".join(out)


def round_svgs(html):
    def per_svg(m):
        svg = m.group(0)
        vb = re.search(r'viewBox="([^"]+)"', svg)
        hgt = re.search(r"height:\s*([\d.]+)px", svg)
        if not vb or not hgt:
            return svg
        units = float(vb.group(1).split()[3])
        # aim for 1/40 of a css px, which is under a device pixel even at 3x
        step = units / float(hgt.group(1)) / 40
        decimals = max(0, math.ceil(-math.log10(step)))

        def fix_d(dm):
            d = dm.group(1)
            # arc flags can be written run together ("a1 1 0 011 1"), which
            # rounding would break, so leave paths with arcs alone
            if re.search(r"[aA]", d):
                return dm.group(0)
            return f'd="{round_path(d, decimals)}"'

        svg = re.sub(r'd="([^"]+)"', fix_d, svg)
        # transforms baked as identity matrices add nothing
        svg = svg.replace(' transform="matrix(1 0 0 1 0 0)"', "")
        return svg

    return re.sub(r"<svg\b.*?</svg>", per_svg, html, flags=re.S)


def sprite_logos(html):
    """Move the engine/platform logos into one external SVG sprite.

    They're over half of index.html once compressed but sit below the first
    screen. Without them the first response fits in a single round trip, and
    the sprite loads right after. Returns the new html and the sprite file.
    """
    symbols = []

    def to_use(m):
        svg = m.group(0)
        attrs, body = re.match(r"<svg\b([^>]*)>(.*)</svg>", svg, flags=re.S).groups()
        vb = re.search(r'viewBox="([^"]+)"', attrs).group(1)
        # page styles don't reach inside a sprite, but custom properties do
        body = body.replace('class="cut"', 'style="fill:var(--surface)"')
        sid = f"l{len(symbols)}"
        symbols.append(f'<symbol id="{sid}" viewBox="{vb}">{body}</symbol>')
        # <use> draws the symbol from 0,0 of the outer svg, so the outer box
        # has to start there; the symbol keeps the real viewBox
        w, h = vb.split()[2:]
        attrs = attrs.replace(f'viewBox="{vb}"', f'viewBox="0 0 {w} {h}"')
        # script.js fills in href after the page has loaded
        return f'<svg{attrs}><use data-href="{{sprite}}#{sid}"/></svg>'

    html = re.sub(r"<svg\b.*?</svg>", to_use, html, flags=re.S)
    sprite = '<svg xmlns="http://www.w3.org/2000/svg">' + "".join(symbols) + "</svg>"
    name = f"img/logos.{hashlib.sha1(sprite.encode()).hexdigest()[:10]}.svg"
    return html.replace("{sprite}", name), name, sprite


def minify_html(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r"\s{2,}", " ", html)
    return html.strip()


# ---------------------------------------------------------------- fonts


def hero_font_css(html):
    """A tiny copy of the brand font, inline, for the text on the first screen.

    It sits right behind the real font in --brand, so the big wordmark and the
    line under it are drawn correctly on the very first frame. When the full
    font arrives it swaps in identical glyphs, so nothing visibly changes, and
    nothing has to wait for a font download before painting.
    """
    from fontTools import subset
    from fontTools.ttLib import TTFont

    text = "WASM.RIP"
    claim = re.search(r'class="hero-claim"[^>]*>(.*?)<', html, flags=re.S)
    if claim:
        text += claim.group(1)
    font = TTFont(ROOT / "fonts/WasmRip-BlackItalic.otf")
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.hinting = False
    opts.name_IDs = [1, 2]
    opts.notdef_outline = False
    opts.desubroutinize = True
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return (
        '@font-face{font-family:"WASM.RIP Hero";font-style:normal;font-weight:900;'
        f'src:url(data:font/woff2;base64,{data}) format("woff2")}}'
    )


# ---------------------------------------------------------------- page


def main():
    if 'id="site-data"' in (ROOT / "index.html").read_text():
        sys.exit("index.html has already been built; run this on a fresh checkout")
    games = json.loads((ROOT / "games.json").read_text())
    members = json.loads((ROOT / "members.json").read_text())
    make_thumbs(games)

    # github serves 460px avatars unless asked for less; they're drawn at 44px
    for m in members:
        if re.match(r"^https://github\.com/[^/]+\.png$", m.get("avatar", "")):
            m["avatar"] += "?size=88"

    html = (ROOT / "index.html").read_text()
    css = minify_css((ROOT / "styles.css").read_text())
    brand = '--brand:"WASM.RIP",'
    assert brand in css, "--brand font stack not found"
    css = hero_font_css(html) + css.replace(brand, brand + '"WASM.RIP Hero",')
    js = minify_js((ROOT / "script.js").read_text())
    data = {"games": games, "members": members, "thumbWidths": THUMB_WIDTHS}
    data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    data = data.replace("</", "<\\/")

    html = round_svgs(html)
    html, sprite_name, sprite = sprite_logos(html)
    for old_sprite in (ROOT / "img").glob("logos.*.svg"):
        old_sprite.unlink()
    (ROOT / sprite_name).write_text(sprite)
    html = minify_html(html)
    html = html.replace('<link rel="stylesheet" href="styles.css" />', f"<style>{css}</style>")
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
    assert "<style>" in html, "stylesheet link not found"
    script_tag = re.search(r'<script src="script\.js"( defer)?></script>', html)
    assert script_tag, "script tag not found"
    # the inline script has to sit at the end of body so the page is parsed first
    html = html.replace(script_tag.group(0), "")
    html = html.replace(
        "</body>",
        f'<script id="site-data" type="application/json">{data}</script><script>{js}</script></body>',
    )
    (ROOT / "index.html").write_text(html)
    print(f"index.html: {len(html.encode()) // 1024} KB")


if __name__ == "__main__":
    main()
