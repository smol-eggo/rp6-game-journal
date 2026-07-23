(() => {
  "use strict";

  const state = {
    games: [],
    query: "",
    verdict: "all",
    sort: "alphabetical",
  };

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

    return url.startsWith("http") || url.startsWith("/")
      ? url
      : `./${url}`;
  };

  const searchableText = (game) => [
    game.title,
    game.verdict,
    game.store,
    game.compatibilityLayer,
    game.date,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  function visibleGames() {
    const query = state.query.trim().toLowerCase();

    const filtered = state.games.filter((game) => {
      const verdictMatches =
        state.verdict === "all" || game.verdict === state.verdict;

      const searchMatches =
        !query || searchableText(game).includes(query);

      return verdictMatches && searchMatches;
    });

    return filtered.sort((a, b) => {
      if (state.sort === "verdict") {
        const difference =
          verdictOrder.indexOf(a.verdict) -
          verdictOrder.indexOf(b.verdict);

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
    link.setAttribute(
      "aria-label",
      `Read the ${game.title} review`
    );

    if (game.coverUrl) {
      const cover = document.createElement("img");
      cover.className = "game-card-cover";
      cover.src = normalizeUrl(game.coverUrl);
      cover.alt = `Cover art for ${game.title}`;
      cover.loading = "lazy";
      cover.decoding = "async";

      link.append(cover);
    }

    const cardBody = document.createElement("div");
    cardBody.className = "game-card-body";

    const verdict = document.createElement("p");
    verdict.className = "verdict";
    verdict.textContent =
      `${game.emoji || "🎮"} ${game.verdict}`;

    const title = document.createElement("h3");
    title.textContent = game.title;

    const details = document.createElement("p");
    details.className = "game-details";
    details.textContent = [
      game.store,
      game.compatibilityLayer,
      game.date,
    ]
      .filter(Boolean)
      .join(" · ");

    const read = document.createElement("span");
    read.className = "card-read-more";
    read.textContent = "Read review →";

    cardBody.append(verdict, title, details, read);
    link.append(cardBody);
    article.append(link);

    return article;
  }

  function render() {
    const games = visibleGames();

    elements.results?.replaceChildren();

    if (elements.resultCount) {
      elements.resultCount.textContent =
        `${games.length} ${games.length === 1 ? "review" : "reviews"}`;
    }

    if (!elements.results) return;

    if (!games.length) {
      const message = document.createElement("p");
      message.className = "message";
      message.textContent =
        "No games found. Eggo checked behind the sofa too.";

      elements.results.append(message);
      return;
    }

    const fragment = document.createDocumentFragment();

    games.forEach((game) => {
      fragment.append(createCard(game));
    });

    elements.results.append(fragment);
  }

  function animateCounter(element, target) {
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    if (prefersReducedMotion || target <= 0) {
      element.textContent = String(target);
      return;
    }

    const duration = Math.min(
      1200,
      Math.max(650, 500 + target * 12)
    );

    const startTime = performance.now();

    element.textContent = "0";

    function tick(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easedProgress =
        1 - Math.pow(1 - progress, 3);

      const currentValue = Math.round(
        target * easedProgress
      );

      element.textContent = String(
        Math.min(currentValue, target)
      );

      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        element.textContent = String(target);
      }
    }

    requestAnimationFrame(tick);
  }

  function updateStatistics() {
    const count = (predicate) =>
      state.games.filter(predicate).length;

    const values = {
      "stat-total": state.games.length,

      "stat-lost-track": count(
        (game) =>
          game.verdict === "Lost Track of Time"
      ),

      "stat-packable": count(
        (game) =>
          verdictOrder.indexOf(game.verdict) <= 2
      ),

      "stat-leave-home": count(
        (game) =>
          game.verdict === "Leave at Home"
      ),
    };

    Object.entries(values).forEach(([id, value]) => {
      const element = document.getElementById(id);

      if (element) {
        animateCounter(element, value);
      }
    });
  }

  function showFeatured() {
    const favourites = state.games.filter(
      (game) =>
        game.verdict === "Lost Track of Time"
    );

    const pool = favourites.length
      ? favourites
      : state.games;

    if (!pool.length || !elements.featuredSection) {
      return;
    }

    const game =
      pool[Math.floor(Math.random() * pool.length)];

    const target = normalizeUrl(
      game.reviewUrl || game.url
    );

    if (elements.featuredTitle) {
      elements.featuredTitle.textContent = game.title;
      elements.featuredTitle.href = target;
    }

    if (elements.featuredVerdict) {
      elements.featuredVerdict.textContent =
        `${game.emoji || "🎮"} ${game.verdict}`;
    }

    if (elements.featuredDetails) {
      elements.featuredDetails.textContent = [
        game.store,
        game.compatibilityLayer,
        game.date,
      ]
        .filter(Boolean)
        .join(" · ");
    }

    if (elements.featuredLink) {
      elements.featuredLink.href = target;
    }

    const decoration =
      elements.featuredSection.querySelector(
        ".featured-decoration"
      );

    const deviceImage =
      decoration?.querySelector(
        ".featured-device-image"
      );

    let coverImage =
      decoration?.querySelector(
        ".featured-cover-image"
      );

    if (game.coverUrl && decoration) {
      if (!coverImage) {
        coverImage = document.createElement("img");
        coverImage.className =
          "featured-cover-image";

        decoration.prepend(coverImage);
      }

      coverImage.src = normalizeUrl(game.coverUrl);
      coverImage.alt =
        `Cover art for ${game.title}`;
      coverImage.hidden = false;

      if (deviceImage) {
        deviceImage.hidden = true;
      }
    } else {
      if (coverImage) {
        coverImage.hidden = true;
      }

      if (deviceImage) {
        deviceImage.hidden = false;
      }
    }

    elements.featuredSection.hidden = false;
  }

  function bindControls() {
    elements.search?.addEventListener(
      "input",
      (event) => {
        state.query = event.target.value;
        render();
      }
    );

    elements.sort?.addEventListener(
      "change",
      (event) => {
        state.sort = event.target.value;
        render();
      }
    );

    elements.filters.forEach((button) => {
      button.addEventListener("click", () => {
        state.verdict =
          button.dataset.verdict || "all";

        elements.filters.forEach((item) => {
          item.classList.toggle(
            "active",
            item === button
          );
        });

        render();
      });
    });
  }

  async function initialise() {
    bindControls();

    try {
      const response = await fetch(
        "./games.json",
        { cache: "no-store" }
      );

      if (!response.ok) {
        throw new Error(
          `games.json returned ${response.status}`
        );
      }

      const games = await response.json();

      if (!Array.isArray(games)) {
        throw new Error(
          "games.json did not contain an array"
        );
      }

      state.games = games;

      updateStatistics();
      showFeatured();
      render();
    } catch (error) {
      console.error(error);

      if (elements.results) {
        elements.results.innerHTML =
          '<p class="message">The journal could not be loaded. Eggo has been sent to inspect the cables.</p>';
      }

      if (elements.resultCount) {
        elements.resultCount.textContent =
          "Journal unavailable";
      }
    }
  }

  initialise();
})();
