# WASM.RIP logo

The logo rebuilt from scratch at 4096px. It's made of layers that are each
described by numbers, so it renders cleanly at any size and every part can be
changed. No pixels of the original image are used.

- `wasm-rip-logo.svg`: the editable logo. The starfield is an image layer and
  "WASM.RIP" is live text in the WASM.RIP font (embedded), one `<tspan>` per
  letter, with a three-stop grey gradient.
- `background.png`: the starfield on its own, 4096×4096. The strip behind the
  letters is filled in, so the text can move.
- `wasm-rip-logo.png`: everything flattened into one 4096px image.
- `model/`: what the starfield is made of. `render.py` draws it.

## the model

Positions and sizes are in pixels of the original 512px logo
(`img/logo.png`), whatever size you render at.

| file | what it holds |
|---|---|
| `stars.csv` | 12,889 stars: position, brightness, measured width |
| `streaks.json` | 9 diagonal streaks: a line and a brightness profile along it |
| `flare.json` | the big star on the left: radial glow, 8 spikes |
| `nebula.npz` | the clouds: 33,313 soft elliptical brush strokes in two sizes |
| `text.json` | each letter's position, baseline and size, and the gradient |
| `meta.json` | the original's own blur, star core/halo shapes, cloud sharpening |

The original is a small, JPEG-damaged image, so the model keeps its shapes and
leaves its damage out:

- Every point of light is a star in `stars.csv`, drawn crisp at its real width:
  the measured width with the original's blur (0.33px) taken out. Bigger stars
  get a crisp core inside a soft halo.
- The clouds were fitted to a cleaned, star-free version of the original
  (JPEG blocks and speckle removed), with strokes no smaller than 0.8px and
  never negative, so they can't produce dark spots, blocks or pixel patterns.
- The original only holds cloud detail down to its own pixel size. The clouds
  are as sharp as that allows; anything finer would have to be invented.

## rendering

```
pip install numpy pillow
python3 render.py                    # 4096px
python3 render.py --size 8192        # any size
python3 render.py --parts stars      # only some layers: nebula, stars, streaks, flare
```

It writes `background.png`, `wasm-rip-logo.svg` and `wasm-rip-logo.png` next
to itself.

## how close it is

The rebuild is crisp and the original is soft, so the starfield is first given
the original's blur (the text isn't; in the original it sits on top of the
photo). The result is then scaled to 512px and compared over the whole image:

| measure | score |
|---|---|
| multi-scale SSIM | 0.981 |
| single-scale SSIM | 0.936 |

Single-scale SSIM compares pixel by pixel, so it also counts the original's
JPEG noise and blocks, which the rebuild deliberately doesn't copy.
Multi-scale SSIM judges structure across several scales and is the better
measure of whether it looks like the same picture.
