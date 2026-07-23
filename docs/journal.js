(() => {
  "use strict";

  const state = { games: [], query: "", verdict: "all", sort: "alphabetical" };
  const verdictOrder = [
    "Lost Track of Time",
    "Just One More Run",
    "Worth Packing",
    "Needs Tinkering",
    "Leave at Home",
  ];

  const elements = {
    results: document.querySelector("#results"),
    search: document.querySelector("#search"),
    sort: document.querySelector("#sort"),
    resultCount: document.querySelector("#result-count"),
    filters: [...document.querySelectorAll(".filter")],
    featuredSection: document.querySelector("#featured-section"),
    featuredTitle: document.querySelector("#featured-title"),
    featuredVerdict: document.querySelector("#featured-verdict"),
    featuredDetails: document.querySelector("#featured-details"),
    featuredLink: document.querySelector("#featured-link"),
  };

  const normalizeUrl = (url) => {
    if (!url) return "#";
    return url.startsWith("http") || url.startsWith("/") ? url : `./${url}`;
  };

  const searchableText = (game) => [
    game.title,
    game.verdict,
    game.store,
    game.compatibilityLayer,
    game.date,
  ].filter(Boolean).join(" ").toLowerCase();

  function visibleGames() {
    const query = state.query.trim().toLowerCase();
    const filtered = state.games.filter((game) => {
      const verdictMatches = state.verdict === "all" || game.verdict === state.verdict;
      return verdictMatches && (!query || searchableText(game).includes(query));
    });

    return filtered.sort((a, b) => {
      if (state.sort === "verdict") {
        const difference = verdictOrder.indexOf(a.verdict) - verdictOrder.indexOf(b.verdict);
        return difference || a.title.localeCompare(b.title);
      }
      return a.title.localeCompare(b.title);
    });
  }

  function createCard(game) {
    const article = document.createElement("article");
    article.className = "game-card";

    const link = document.createElement("a");
    link.className = "game-card-link";
    link.href = normalizeUrl(game.reviewUrl || game.url);
    link.setAttribute("aria-label", `Read the ${game.title} review`);

    const verdict = document.createElement("p");
    verdict.className = "verdict";
    verdict.textContent = `${game.emoji || "🎮"} ${game.verdict}`;

    const title = document.createElement("h3");
    title.textContent = game.title;

    const details = document.createElement("p");
    details.className = "game-details";
    details.textContent = [game.store, game.compatibilityLayer, game.date].filter(Boolean).join(" · ");

    const read = document.createElement("span");
    read.className = "card-read-more";
    read.textContent = "Read review →";

    link.append(verdict, title, details, read);
    article.append(link);
    return article;
  }

  function render() {
    const games = visibleGames();
    elements.results.replaceChildren();
    elements.resultCount.textContent = `${games.length} ${games.length === 1 ? "review" : "reviews"}`;

    if (!games.length) {
      const message = document.createElement("p");
      message.className = "message";
      message.textContent = "No games found. Eggo checked behind the sofa too.";
      elements.results.append(message);
      return;
    }

    const fragment = document.createDocumentFragment();
    games.forEach((game) => fragment.append(createCard(game)));
    elements.results.append(fragment);
  }

  function updateStatistics() {
    const count = (predicate) => state.games.filter(predicate).length;
    const values = {
      "stat-total": state.games.length,
      "stat-lost-track": count((game) => game.verdict === "Lost Track of Time"),
      "stat-packable": count((game) => verdictOrder.indexOf(game.verdict) <= 2),
      "stat-leave-home": count((game) => game.verdict === "Leave at Home"),
    };

    Object.entries(values).forEach(([id, value]) => {
      const element = document.getElementById(id);
      if (element) element.textContent = String(value);
    });
  }

  function showFeatured() {
    const favourites = state.games.filter((game) => game.verdict === "Lost Track of Time");
    const pool = favourites.length ? favourites : state.games;
    if (!pool.length || !elements.featuredSection) return;

    const game = pool[Math.floor(Math.random() * pool.length)];
    const target = normalizeUrl(game.reviewUrl || game.url);
    elements.featuredTitle.textContent = game.title;
    elements.featuredTitle.href = target;
    elements.featuredVerdict.textContent = `${game.emoji || "🎮"} ${game.verdict}`;
    elements.featuredDetails.textContent = [game.store, game.compatibilityLayer, game.date].filter(Boolean).join(" · ");
    elements.featuredLink.href = target;
    elements.featuredSection.hidden = false;
  }

  function bindControls() {
    elements.search?.addEventListener("input", (event) => {
      state.query = event.target.value;
      render();
    });

    elements.sort?.addEventListener("change", (event) => {
      state.sort = event.target.value;
      render();
    });

    elements.filters.forEach((button) => {
      button.addEventListener("click", () => {
        state.verdict = button.dataset.verdict || "all";
        elements.filters.forEach((item) => item.classList.toggle("active", item === button));
        render();
      });
    });
  }

  async function initialise() {
    bindControls();
    try {
      const response = await fetch("./games.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`games.json returned ${response.status}`);
      state.games = await response.json();
      updateStatistics();
      showFeatured();
      render();
    } catch (error) {
      console.error(error);
      elements.results.innerHTML = '<p class="message">The journal could not be loaded. Eggo has been sent to inspect the cables.</p>';
      elements.resultCount.textContent = "Journal unavailable";
    }
  }

  initialise();
})();
