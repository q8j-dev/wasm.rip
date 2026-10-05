// WHO made ts
// (the starfield that used to live here is gone, the logo does that job now)

const grid = document.querySelector("#grid");
const empty = document.querySelector("#empty");
const countEl = document.querySelector("#ports-count");
const searchEl = document.querySelector("#q");
const sortEl = document.querySelector("#sort");
const tabs = document.querySelectorAll(".tab");
const chip = document.querySelector("#porter-chip");
const chipName = document.querySelector("#porter-name");
const peopleList = document.querySelector("#people-list");

const state = { q: "", filter: "all", sort: "featured", porter: null };

const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

// "crackers & slqnt" -> ["crackers", "slqnt"]
const splitPorters = (porter) =>
  porter.split(/\s*(?:&|,|\band\b)\s*/i).map((p) => p.trim()).filter(Boolean);

// links to this site, or to wasm.rip itself (fast previews point games there),
// aren't "external"
const HOME_HOSTS = ["wasm.rip", "www.wasm.rip", location.hostname];
const isExternal = (url) =>
  /^https?:\/\//.test(url) && !HOME_HOSTS.includes(new URL(url).hostname);

const byName = (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

let games = [];
let members = [];

function matchesPorter(game, member) {
  const keys = [member.name, member.github, ...(member.aliases || [])].map(norm);
  return splitPorters(game.porter).some((p) => keys.includes(norm(p)));
}

function visibleGames() {
  const q = norm(state.q);
  let list = games.filter((g) => {
    if (state.filter === "featured" && !g.featured) return false;
    if (state.porter && !matchesPorter(g, state.porter)) return false;
    if (q && !norm(g.name).includes(q) && !norm(g.porter).includes(q)) return false;
    return true;
  });

  if (state.sort === "az") list.sort(byName);
  else if (state.sort === "new") list.sort((a, b) => b._order - a._order);
  else list.sort((a, b) => (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || byName(a, b));

  return list;
}

// thumbnails and the logo sprite wait for the page's load event, which comes
// once the hero image and fonts are in. On a slow connection that gives the
// first screen all the bandwidth; on a fast one it costs nothing.
const afterLoad = new Promise((resolve) =>
  document.readyState === "complete" ? resolve() : addEventListener("load", resolve, { once: true })
);
afterLoad.then(() => {
  document.querySelectorAll("use[data-href]").forEach((u) => u.setAttribute("href", u.dataset.href));
});

// cards are built once and reused, so typing in search doesn't rebuild
// every card and its image on each keystroke
const cards = new Map();
const cardFor = (game) => {
  if (!cards.has(game)) cards.set(game, card(game));
  return cards.get(game);
};

// the deployed page has small AVIF/WebP copies of each image (see
// tools/build.py); the plain source files just use the original image
const THUMB_SIZES = "(max-width: 340px) 286px, (max-width: 640px) 45vw, 272px";
let thumbWidths = [];
const srcset = (base, ext) => thumbWidths.map((w) => `${base}-${w}.${ext} ${w}w`).join(", ");

function card(game) {
  const a = document.createElement("a");
  a.className = "port";
  a.href = game.gameUrl;
  a.target = "_blank";
  a.rel = "noopener";

  const thumb = document.createElement("div");
  thumb.className = "thumb";
  const img = document.createElement("img");
  img.alt = "";
  img.loading = "lazy";
  img.decoding = "async";
  // the hero image goes first; thumbnails can wait a moment
  img.fetchPriority = "low";
  img.width = 320;
  img.height = 200;
  if (game.thumb) {
    const picture = document.createElement("picture");
    const avif = document.createElement("source");
    avif.type = "image/avif";
    avif.sizes = THUMB_SIZES;
    img.sizes = THUMB_SIZES;
    afterLoad.then(() => {
      avif.srcset = srcset(game.thumb, "avif");
      img.srcset = srcset(game.thumb, "webp");
      img.src = `${game.thumb}-${thumbWidths[0]}.webp`;
    });
    // a missing thumbnail falls back to the original image
    img.addEventListener(
      "error",
      () => {
        picture.replaceWith(img);
        img.removeAttribute("srcset");
        img.src = game.imageUrl;
        img.addEventListener("error", () => img.remove(), { once: true });
      },
      { once: true }
    );
    picture.append(avif, img);
    thumb.appendChild(picture);
  } else {
    afterLoad.then(() => (img.src = game.imageUrl));
    img.addEventListener("error", () => img.remove(), { once: true });
    thumb.appendChild(img);
  }

  const meta = document.createElement("div");
  meta.className = "meta";
  const title = document.createElement("span");
  title.className = "title";
  title.textContent = game.name;
  // a game hosted somewhere else gets an arrow; hovering shows where it goes
  if (isExternal(game.gameUrl)) {
    const host = new URL(game.gameUrl).hostname;
    const arrow = document.createElement("span");
    arrow.className = "ext";
    arrow.textContent = " \u2197";
    arrow.setAttribute("aria-label", `, opens ${host}`);
    title.appendChild(arrow);
    a.title = `opens ${host}`;
  }
  const by = document.createElement("span");
  by.className = "by";
  // a porter field in parentheses is a note, e.g. "(click for more info)"
  const note = game.porter.match(/^\((.*)\)$/);
  by.textContent = note ? note[1] : `port by ${game.porter}`;
  by.title = by.textContent;
  meta.append(title, by);

  a.append(thumb, meta);
  return a;
}

function render() {
  const list = visibleGames();
  grid.replaceChildren(...list.map(cardFor));

  countEl.textContent =
    list.length === games.length ? `${games.length} total` : `${list.length} of ${games.length}`;

  empty.hidden = list.length > 0;
  if (!list.length) {
    empty.innerHTML = "";
    empty.append(
      state.q ? `nothing matches "${state.q}". ` : "nothing here. ",
      "if you want it ported, ask in the "
    );
    const link = document.createElement("a");
    link.href = "https://discord.gg/uubyGYPHQw";
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "discord";
    empty.append(link, ".");
  }

  chip.hidden = !state.porter;
  if (state.porter) chipName.textContent = state.porter.name;
}

function renderPeople() {
  peopleList.replaceChildren(
    ...members.map((m) => {
      const n = games.filter((g) => matchesPorter(g, m)).length;

      const li = document.createElement("li");
      li.className = "person";

      const img = document.createElement("img");
      img.src = m.avatar;
      img.alt = "";
      img.loading = "lazy";
      img.width = 44;
      img.height = 44;
      // dead avatar -> first letter of their name instead of a broken image
      img.addEventListener(
        "error",
        () => {
          const fallback = document.createElement("span");
          fallback.className = "person-fallback";
          fallback.textContent = m.name.charAt(0);
          img.replaceWith(fallback);
        },
        { once: true }
      );

      const text = document.createElement("div");
      text.className = "person-text";

      const name = document.createElement("a");
      name.className = "person-name";
      name.href = `https://github.com/${m.github}`;
      name.target = "_blank";
      name.rel = "noopener";
      name.textContent = m.name;

      const ports = document.createElement("button");
      ports.type = "button";
      ports.className = "person-ports";
      ports.textContent = n ? `${n} port${n === 1 ? "" : "s"}` : "no ports listed";
      ports.disabled = !n;
      ports.addEventListener("click", () => {
        state.porter = m;
        state.filter = "all";
        state.q = "";
        searchEl.value = "";
        syncTabs();
        render();
        document.querySelector("#ports").scrollIntoView();
      });

      text.append(name, ports);
      li.append(img, text);
      return li;
    })
  );
}

function syncTabs() {
  tabs.forEach((t) => t.setAttribute("aria-pressed", String(t.dataset.filter === state.filter)));
}

searchEl.addEventListener("input", () => {
  state.q = searchEl.value.trim();
  render();
});

sortEl.addEventListener("change", () => {
  state.sort = sortEl.value;
  render();
});

tabs.forEach((t) =>
  t.addEventListener("click", () => {
    state.filter = t.dataset.filter;
    syncTabs();
    render();
  })
);

document.querySelector("#porter-clear").addEventListener("click", () => {
  state.porter = null;
  render();
});

// the bar's wordmark only shows up once the big one has scrolled away
const barMark = document.querySelector(".bar .wordmark");
const heroMark = document.querySelector("#hero-mark");
if (heroMark && "IntersectionObserver" in window) {
  new IntersectionObserver(([entry]) => {
    barMark.toggleAttribute("data-hidden", entry.isIntersecting);
  }, { rootMargin: "-61px 0px 0px 0px" }).observe(heroMark);
}

// press / to search, esc to bail
document.addEventListener("keydown", (e) => {
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
  if (e.key === "/" && !typing) {
    e.preventDefault();
    searchEl.focus();
  } else if (e.key === "Escape" && document.activeElement === searchEl) {
    searchEl.value = "";
    state.q = "";
    render();
    searchEl.blur();
  }
});

// the deployed page carries the data inline; the source files fetch it
const inline = document.querySelector("#site-data");
// (it still waits one frame, so the first screen paints before the grid is built)
const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve)));
const loaded = inline
  ? nextFrame()
      .then(() => JSON.parse(inline.textContent))
      .then((d) => {
        thumbWidths = d.thumbWidths;
        return [d.games, d.members];
      })
  : Promise.all([
      fetch("games.json").then((r) => r.json()),
      fetch("members.json").then((r) => r.json()).catch(() => []),
    ]);

loaded
  .then(([g, m]) => {
    // file order is the order things were added, ids have dupes so don't trust them
    games = g.map((game, i) => ({ ...game, _order: i }));
    members = m;
    // the intro names two games, then "and N more"
    document.querySelector("#more-count").textContent = Math.max(0, games.length - 2);

    render();
    renderPeople();
  })
  .catch(() => {
    countEl.textContent = "";
    empty.hidden = false;
    empty.textContent = "hi, games failed to load, either someone messed something up or idk";
  });
