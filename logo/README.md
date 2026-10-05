# WASM.RIP logo

The logo rebuilt from scratch at 4096px. It's made of layers that are each
described by numbers, so it renders cleanly at any size and every part can be
changed.

- `wasm-rip-logo.svg`: the editable logo. The starfield is an image layer and
  "WASM.RIP" is live text in the WASM.RIP font (embedded), one `<tspan>` per
  letter, with a three-stop grey gradient.
- `background.png`: the starfield on its own, 4096×4096. The strip behind the
  letters is filled in, so the text can move.
- `wasm-rip-logo.png`: everything flattened into one 4096px image.
- `model/`: what the starfield is made of. `render.py` draws it.

## the model

All positions and sizes are in pixels of the original 512px logo
(`img/logo.png`), whatever size you render at.

| file | what it holds |
|---|---|
| `stars.csv` | 5,724 stars: position, brightness, width |
| `streaks.json` | 9 diagonal streaks: a line and a brightness profile along it |
| `flare.json` | the big star on the left: radial glow, 8 spikes |
| `nebula.npz` | the clouds: about 148,000 elliptical gaussian brush strokes in three sizes |
| `text.json` | each letter's position, baseline and size, and the gradient |

None of these store pixels from the original. They were fitted to it: stars
and streaks were measured, and the brush strokes were optimised until the
rendered clouds matched.

## rendering

```
pip install numpy pillow
python3 render.py                 # 4096px
python3 render.py --size 8192     # any size
python3 render.py --sharp 1.0     # star width: 1.0 = as measured, default 0.85 (a little crisper)
```

It writes `background.png`, `wasm-rip-logo.svg` and `wasm-rip-logo.png` next
to itself.

## how close it is

Rendered at 4096px and scaled back down to 512px, compared with the original
over the whole image, letters included:

| scaled down with | SSIM | PSNR |
|---|---|---|
| area averaging | 0.982 | 32.2 dB |
| Lanczos | 0.969 | 31.4 dB |

With `--sharp 1.0` (stars exactly as measured) it's 0.988 and 0.980. The
starfield alone, away from the letters, scores 0.993 at the default and 0.999
with `--sharp 1.0`. What's left is mostly at the letter edges, where the
font's shapes differ slightly from the original lettering.
