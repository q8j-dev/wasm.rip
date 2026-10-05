# WASM.RIP Black Italic

The display face used on the site, drawn from the lettering in the WASM.RIP logo.

Nothing here is traced into the font. The eight letters in the logo
(W A S M . R I P) were traced only to measure the design: slant (9.67°), stem
and bar weights, curve radii and tension, diagonal widths, overshoot, dot size
and terminal angles. Every glyph is then built from those numbers as clean
geometry, so the letters the logo doesn't have match the ones it does.

- `kit.py`: geometry primitives (rects, superellipse corners, strokes, boolean ops)
- `glyphs.py`: the eight logo letters as parametric constructions
- `fit.py`: tunes those parameters until each construction, pushed through the
  same blur/threshold the 512px logo went through, overlaps the trace
  (`logo-trace/`). Writes `params.json`.
- `full.py`: A–Z, a–z, 0–9, punctuation and symbols built from the fitted parameters
- `extra.py`: curly quotes, Latin-1 accented letters, Æ Œ Ø Ð Þ ß, currency, etc.
- `space.py`: optical (area-based) sidebearings
- `build.py`: spacing, slant, kerning, writes `../fonts/WasmRip-BlackItalic.{otf,woff2}`

Rebuild:

```sh
pip install fonttools brotli skia-pathops numpy scipy opencv-python-headless pillow
cd font-src
python3 build.py          # rebuild the font from params.json
python3 fit.py -r3        # (optional) refit the logo letters first
```

206 glyphs: ASCII, Latin-1 letters, Œ œ Š š Ž ž Ÿ, typographic quotes,
dashes, ellipsis, guillemets, € £ ¥ ¢ © ® ° × ÷ ±. About 1,100 kerning pairs.
