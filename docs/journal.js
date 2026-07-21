"use strict";

const REQUEST_URL =
  "https://github.com/smol-eggo/rp6-game-journal/discussions/categories/game-requests";

const VERDICTS = {
  "Lost Track of Time": {
    emoji: "🍇",
    slug: "lost-track",
    rank: 1,
  },
  "Just One More Run": {
    emoji: "☕",
    slug: "one-more-run",
    rank: 2,
  },
  "Worth Packing": {
    emoji: "🎒",
    slug: "worth-packing",
    rank: 3,
  },
  "Needs Tinkering": {
    emoji: "🔧",
    slug: "needs-tinkering",
    rank: 4,
  },
  "Leave at Home": {
    emoji: "🏠",
    slug: "leave-home",
    rank: 5,
  },
};

let games = [];
let activeVerdict = "all";
let counterAnimationStarted = false;

const searchInput = document.querySelector("#search");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#result-count");
const filterButtons = document.querySelectorAll("[data-verdict]");
const sortSelect = document.querySelector("#sort");

const statTotal = document.querySelector("#stat-total");
const statLostTrack = document.querySelector("#stat-lost-track");
const statPackable = document.querySelector("#stat-packable");
const statLeaveHome = document.querySelector("#stat-leave-home");
const statisticsSection = document.querySelector(".statistics-section");

const featuredSection = document.querySelector("#featured-section");
const featuredVerdict = document.querySelector("#featured-verdict");
const featuredTitle = document.querySelector("#featured-title");
const featuredDetails = document.querySelector("#featured-details");
const featuredLink = document.querySelector("#featured-link");

const eggos = document.querySelectorAll("[data-eggo]");
const featuredEggo = document.querySelector('[data-eggo="featured"]');
const communityEggo = document.querySelector('[data-eggo="community"]');

const reduceMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;

function normalise(value) {
  return String(value ?? "").trim().toLowerCase();
}

function getVerdictData(verdict) {
  return (
    VERDICTS[verdict] ?? {
      emoji: "🎮",
      slug: "unknown",
      rank: 99,
    }
  );
}

function getGameEmoji(game) {
  const suppliedEmoji = String(game.emoji ?? "").trim();

  if (suppliedEmoji) {
    return suppliedEmoji;
  }

  return getVerdictData(game.verdict).emoji;
}

function getDetailParts(game) {
  const parts = [];

  if (game.store && game.store !== "Not listed") {
    parts.push(game.store);
  }

  if (
    game.compatibilityLayer &&
    game.compatibilityLayer !== "Not listed"
  ) {
    parts.push(game.compatibilityLayer);
  }

  if (game.date) {
    parts.push(game.date);
  }

  return parts;
}

function createChip(text, className = "") {
  const chip = document.createElement("span");
  chip.className = `detail-chip ${className}`.trim();
  chip.textContent = text;
  return chip;
}

function createGameCard(game) {
  const verdictData = getVerdictData(game.verdict);

  const article = document.createElement("article");
  article.className = `game-card game-card-${verdictData.slug}`;

  const cardTop = document.createElement("div");
  cardTop.className = "game-card-top";

  const verdict = document.createElement("p");
  verdict.className = "verdict";
  verdict.textContent = `${getGameEmoji(game)} ${game.verdict}`;

  const arrow = document.createElement("span");
  arrow.className = "card-arrow";
  arrow.setAttribute("aria-hidden", "true");
  arrow.textContent = "↗";

  cardTop.append(verdict, arrow);

  const title = document.createElement("h3");
  const link = document.createElement("a");
  link.href = game.url;
  link.textContent = game.title;
  link.setAttribute("aria-label", `Read the ${game.title} review`);
  title.appendChild(link);

  const details = document.createElement("div");
  details.className = "card-details";

  if (game.store && game.store !== "Not listed") {
    details.appendChild(createChip(game.store, "store-chip"));
  }

  if (
    game.compatibilityLayer &&
    game.compatibilityLayer !== "Not listed"
  ) {
    details.appendChild(
      createChip(game.compatibilityLayer, "layer-chip")
    );
  }

  const cardFooter = document.createElement("div");
  cardFooter.className = "game-card-footer";

  const date = document.createElement("span");
  date.className = "review-date";
  date.textContent = game.date || "Date not listed";

  const readReview = document.createElement("span");
  readReview.className = "read-review";
  readReview.textContent = "Read review";

  cardFooter.append(date, readReview);
  article.append(cardTop, title, details, cardFooter);

  return article;
}

function getFilteredGames() {
  const query = normalise(searchInput.value);

  const filtered = games.filter((game) => {
    const searchableText = normalise(
      [
        game.title,
        game.verdict,
        game.store,
        game.compatibilityLayer,
        game.date,
      ].join(" ")
    );

    const matchesSearch = searchableText.includes(query);
    const matchesVerdict =
      activeVerdict === "all" || game.verdict === activeVerdict;

    return matchesSearch && matchesVerdict;
  });

  if (sortSelect.value === "verdict") {
    return filtered.sort((a, b) => {
      const rankDifference =
        getVerdictData(a.verdict).rank -
        getVerdictData(b.verdict).rank;

      return rankDifference || a.title.localeCompare(b.title);
    });
  }

  return filtered.sort((a, b) => a.title.localeCompare(b.title));
}

function createEmptyState() {
  const query = searchInput.value.trim();

  const panel = document.createElement("div");
  panel.className = "empty-state";

  const mascotWrap = document.createElement("div");
  mascotWrap.className = "empty-eggo-wrap";
  mascotWrap.setAttribute("aria-hidden", "true");
  mascotWrap.innerHTML = `
    <div class="eggo eggo-empty is-confused">
      <span class="eggo-leaf eggo-leaf-left"></span>
      <span class="eggo-leaf eggo-leaf-right"></span>
      <span class="eggo-body">
        <span class="eggo-eye eggo-eye-left"></span>
        <span class="eggo-eye eggo-eye-right"></span>
        <span class="eggo-mouth"></span>
        <span class="eggo-shine"></span>
      </span>
    </div>
  `;

  const copy = document.createElement("div");
  copy.className = "empty-state-copy";

  const kicker = document.createElement("p");
  kicker.className = "section-kicker";
  kicker.textContent = "Nothing on this shelf";

  const title = document.createElement("h3");
  title.textContent = query
    ? `Eggo could not find “${query}”.`
    : "Eggo checked every corner of the journal.";

  const note = document.createElement("p");
  note.textContent =
    activeVerdict === "all"
      ? "It might be the perfect candidate for the next RP6 adventure."
      : "Try another verdict, clear the search, or send the game to the request board.";

  const actions = document.createElement("div");
  actions.className = "empty-state-actions";

  const clearButton = document.createElement("button");
  clearButton.type = "button";
  clearButton.className = "secondary-link empty-clear-button";
  clearButton.textContent = "Clear search";
  clearButton.addEventListener("click", clearFilters);

  const requestLink = document.createElement("a");
  requestLink.className = "primary-link";
  requestLink.href = REQUEST_URL;
  requestLink.target = "_blank";
  requestLink.rel = "noopener noreferrer";
  requestLink.textContent = query
    ? `Suggest ${query}`
    : "Suggest a game";

  actions.append(clearButton, requestLink);
  copy.append(kicker, title, note, actions);
  panel.append(mascotWrap, copy);

  return panel;
}

function clearFilters() {
  searchInput.value = "";
  activeVerdict = "all";

  filterButtons.forEach((button) => {
    const isActive = button.dataset.verdict === "all";
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  renderGames();
  searchInput.focus();
}

function setEggoState(state) {
  eggos.forEach((eggo) => {
    eggo.classList.remove("is-happy", "is-curious", "is-confused");

    if (state) {
      eggo.classList.add(`is-${state}`);
    }
  });
}

function pulseEggo(eggo, state) {
  if (!eggo || reduceMotion) {
    return;
  }

  eggo.classList.remove("is-happy", "is-curious", "is-confused");
  void eggo.offsetWidth;
  eggo.classList.add(`is-${state}`);

  window.setTimeout(() => {
    eggo.classList.remove(`is-${state}`);
  }, 900);
}

function renderGames() {
  const filteredGames = getFilteredGames();
  results.replaceChildren();

  resultCount.textContent = `${filteredGames.length} ${
    filteredGames.length === 1 ? "game" : "games"
  } found`;

  if (filteredGames.length === 0) {
    results.appendChild(createEmptyState());
    setEggoState("confused");
    return;
  }

  const fragment = document.createDocumentFragment();

  filteredGames.forEach((game) => {
    fragment.appendChild(createGameCard(game));
  });

  results.appendChild(fragment);

  if (searchInput.value.trim() || activeVerdict !== "all") {
    setEggoState("happy");
    pulseEggo(featuredEggo, "happy");
  } else {
    setEggoState("");
  }
}

function setActiveVerdict(button) {
  activeVerdict = button.dataset.verdict;

  filterButtons.forEach((candidate) => {
    const isActive = candidate === button;
    candidate.classList.toggle("active", isActive);
    candidate.setAttribute("aria-pressed", String(isActive));
  });

  renderGames();
}

function setCounterTarget(element, value) {
  element.dataset.count = String(value);

  if (reduceMotion || counterAnimationStarted) {
    element.textContent = String(value);
  }
}

function animateCounter(element) {
  const target = Number(element.dataset.count || 0);

  if (reduceMotion) {
    element.textContent = String(target);
    return;
  }

  const duration = 850;
  const start = performance.now();

  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = String(Math.round(target * eased));

    if (progress < 1) {
      requestAnimationFrame(tick);
    } else {
      element.textContent = String(target);
    }
  }

  requestAnimationFrame(tick);
}

function startCounterAnimation() {
  if (counterAnimationStarted) {
    return;
  }

  counterAnimationStarted = true;

  [statTotal, statLostTrack, statPackable, statLeaveHome].forEach(
    animateCounter
  );
}

function observeStatistics() {
  if (reduceMotion || !("IntersectionObserver" in window)) {
    startCounterAnimation();
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        startCounterAnimation();
        observer.disconnect();
      }
    },
    {
      threshold: 0.3,
    }
  );

  observer.observe(statisticsSection);
}

function renderStatistics() {
  const countByVerdict = (verdict) =>
    games.filter((game) => game.verdict === verdict).length;

  const lostTrackCount = countByVerdict("Lost Track of Time");
  const oneMoreRunCount = countByVerdict("Just One More Run");
  const worthPackingCount = countByVerdict("Worth Packing");
  const leaveHomeCount = countByVerdict("Leave at Home");

  setCounterTarget(statTotal, games.length);
  setCounterTarget(statLostTrack, lostTrackCount);
  setCounterTarget(
    statPackable,
    lostTrackCount + oneMoreRunCount + worthPackingCount
  );
  setCounterTarget(statLeaveHome, leaveHomeCount);

  observeStatistics();
}

function renderFeaturedReview() {
  const favourites = games.filter(
    (game) => game.verdict === "Lost Track of Time"
  );

  const candidates = favourites.length > 0 ? favourites : games;

  if (candidates.length === 0) {
    featuredSection.hidden = true;
    return;
  }

  const randomIndex = Math.floor(Math.random() * candidates.length);
  const game = candidates[randomIndex];
  const emoji = getGameEmoji(game);

  featuredVerdict.textContent = `${emoji} ${game.verdict}`;
  featuredTitle.textContent = game.title;
  featuredTitle.href = game.url;
  featuredDetails.textContent = getDetailParts(game).join(" · ");
  featuredLink.href = game.url;
  featuredSection.hidden = false;
}

function handleSearchInput() {
  renderGames();

  if (searchInput.value.trim()) {
    pulseEggo(communityEggo, "curious");
  }
}

searchInput.addEventListener("input", handleSearchInput);
sortSelect.addEventListener("change", renderGames);

filterButtons.forEach((button) => {
  button.setAttribute(
    "aria-pressed",
    String(button.classList.contains("active"))
  );

  button.addEventListener("click", () => {
    setActiveVerdict(button);
  });
});

fetch("./games.json")
  .then((response) => {
    if (!response.ok) {
      throw new Error(
        `Could not load games.json (${response.status}).`
      );
    }

    return response.json();
  })
  .then((data) => {
    if (!Array.isArray(data)) {
      throw new Error(
        "The journal data has an unexpected format."
      );
    }

    games = data;
    renderStatistics();
    renderFeaturedReview();
    renderGames();

    window.setTimeout(() => {
      pulseEggo(featuredEggo, "happy");
    }, 500);
  })
  .catch((error) => {
    console.error(error);

    resultCount.textContent = "The journal could not be loaded.";

    const message = document.createElement("div");
    message.className = "empty-state error-state";
    message.innerHTML = `
      <div class="empty-state-copy">
        <p class="section-kicker">The shelf is temporarily closed</p>
        <h3>The searchable journal could not be loaded.</h3>
        <p>The reviews are still available in the GitHub repository.</p>
        <a
          class="primary-link"
          href="https://github.com/smol-eggo/rp6-game-journal"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open the repository
        </a>
      </div>
    `;

    results.replaceChildren(message);
    setEggoState("confused");
  });
