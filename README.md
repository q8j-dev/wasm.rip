wasm.rip

## adding a game

Add an entry to `games.json` and put its image in `img/`. The
deploy makes the small thumbnails the site actually shows.

## how the page is built

The files in the repo (`index.html`, `styles.css`, `script.js`, `games.json`,
`members.json`) work as they are. Open them with any static server to work on
the site.

On deploy, `tools/build.py` turns them into a faster page:

- `img/t/` gets AVIF and WebP thumbnails at the sizes the cards are drawn at.
  The ones already in the repo are reused, and new ones are made for new games.
- The CSS, script and game list go straight into `index.html`, so the first
  response has everything needed to draw the page.
- The engine and platform logos move into one SVG file that loads after the
  page.

To try the built version locally, run it on a copy, never on your checkout:

```
pip install pillow fonttools brotli
python3 tools/build.py path/to/copy
```
