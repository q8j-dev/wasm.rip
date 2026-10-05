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

// how many of the newest ports get a "new" badge
const NEW_COUNT = 3;

const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

// "crackers & slqnt" -> ["crackers", "slqnt"]
const splitPorters = (porter) =>
  porter.split(/\s*(?:&|,|\band\b)\s*/i).map((p) => p.trim()).filter(Boolean);

const isExternal = (url) => /^https?:\/\//.test(url);

const byName = (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

let games = [];
let members = [];
let newGames = new Set();

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

function card(game) {
  const a = document.createElement("a");
  a.className = "port";
  a.href = game.gameUrl;
  a.target = "_blank";
  a.rel = "noopener";

  const thumb = document.createElement("div");
  thumb.className = "thumb";
  const img = document.createElement("img");
  img.src = game.imageUrl;
  img.alt = "";
  img.loading = "lazy";
  img.decoding = "async";
  img.width = 320;
  img.height = 200;
  img.addEventListener("error", () => img.remove(), { once: true });
  thumb.appendChild(img);

  const badges = document.createElement("div");
  badges.className = "badges";
  if (game.featured) {
    const b = document.createElement("span");
    b.className = "badge";
    b.title = "featured";
    b.innerHTML = '<svg class="flare" aria-hidden="true"><use href="#flare"/></svg>';
    b.append("featured");
    badges.appendChild(b);
  }
  if (newGames.has(game)) {
    const b = document.createElement("span");
    b.className = "badge";
    b.textContent = "new";
    badges.appendChild(b);
  }
  if (isExternal(game.gameUrl)) {
    const b = document.createElement("span");
    b.className = "badge badge-ext";
    b.textContent = "external";
    badges.appendChild(b);
  }

  const meta = document.createElement("div");
  meta.className = "meta";
  const title = document.createElement("span");
  title.className = "title";
  title.textContent = game.name;
  const by = document.createElement("span");
  by.className = "by";
  by.textContent = `port by ${game.porter}`;
  meta.append(title, by);

  a.append(thumb, badges, meta);
  return a;
}

function render() {
  const list = visibleGames();
  grid.replaceChildren(...list.map(card));

  countEl.textContent =
    list.length === games.length ? `${games.length} total` : `${list.length} of ${games.length}`;

  empty.hidden = list.length > 0;
  if (!list.length) {
    empty.innerHTML = "";
    empty.append(
      state.q ? `nothing matches "${state.q}". ` : "nothing here. ",
      "want it ported? ask in the "
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
      img.addEventListener("error", () => (img.style.visibility = "hidden"), { once: true });

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

Promise.all([
  fetch("games.json").then((r) => r.json()),
  fetch("members.json").then((r) => r.json()).catch(() => []),
])
  .then(([g, m]) => {
    // file order is the order things were added, ids have dupes so don't trust them
    games = g.map((game, i) => ({ ...game, _order: i }));
    members = m;
    newGames = new Set([...games].sort((a, b) => b._order - a._order).slice(0, NEW_COUNT));

    const latest = games[games.length - 1];
    document.querySelector("#stat-ports").textContent = games.length;
    document.querySelector("#stat-people").textContent = members.length || "–";
    document.querySelector("#stat-latest").textContent = latest ? latest.name : "–";
    document.querySelector("#stat-latest").title = latest ? latest.name : "";

    render();
    renderPeople();
  })
  .catch(() => {
    countEl.textContent = "";
    empty.hidden = false;
    empty.textContent = "hi, games failed to load, either someone messed something up or idk";
  });
