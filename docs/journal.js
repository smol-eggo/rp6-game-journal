"use strict";

/* =========================================================
   Journal configuration
   ========================================================= */

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
    emoji: "🛠",
    slug: "needs-tinkering",
    rank: 4,
  },

  "Leave at Home": {
    emoji: "🚧",
    slug: "leave-home",
    rank: 5,
  },
};

let games = [];
let activeVerdict = "all";


/* =========================================================
   Page elements
   ========================================================= */

const searchInput = document.querySelector("#search");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#result-count");
const filterButtons = document.querySelectorAll("[data-verdict]");
const sortSelect = document.querySelector("#sort");

const statTotal = document.querySelector("#stat-total");
const statLostTrack = document.querySelector("#stat-lost-track");
const statPackable = document.querySelector("#stat-packable");
const statLeaveHome = document.querySelector("#stat-leave-home");

const featuredSection = document.querySelector("#featured-section");
const featuredVerdict = document.querySelector("#featured-verdict");
const featuredTitle = document.querySelector("#featured-title");
const featuredDetails = document.querySelector("#featured-details");
const featuredLink = document.querySelector("#featured-link");


/* =========================================================
   Helpers
   ========================================================= */

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


/* =========================================================
   Game cards
   ========================================================= */

function createGameCard(game) {
  const verdictData = getVerdictData(game.verdict);
  const article = document.createElement("article");

  article.className =
    `game-card game-card-${verdictData.slug}`;

  const cardTop = document.createElement("div");
  cardTop.className = "game-card-top";

  const verdict = document.createElement("p");
  verdict.className = "verdict";
  verdict.textContent =
    `${getGameEmoji(game)} ${game.verdict}`;

  const arrow = document.createElement("span");
  arrow.className = "card-arrow";
  arrow.setAttribute("aria-hidden", "true");
  arrow.textContent = "↗";

  cardTop.append(verdict, arrow);

  const title = document.createElement("h3");

  const link = document.createElement("a");
  link.href = game.url;
  link.textContent = game.title;
  link.setAttribute(
    "aria-label",
    `Read the ${game.title} review`
  );

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


/* =========================================================
   Filtering and sorting
   ========================================================= */

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
      activeVerdict === "all" ||
      game.verdict === activeVerdict;

    return matchesSearch && matchesVerdict;
  });

  if (sortSelect.value === "verdict") {
    return filtered.sort((a, b) => {
      const rankDifference =
        getVerdictData(a.verdict).rank -
        getVerdictData(b.verdict).rank;

      return (
        rankDifference ||
        a.title.localeCompare(b.title)
      );
    });
  }

  return filtered.sort((a, b) =>
    a.title.localeCompare(b.title)
  );
}

function renderGames() {
  const filteredGames = getFilteredGames();

  results.replaceChildren();

  resultCount.textContent =
    `${filteredGames.length} ${
      filteredGames.length === 1 ? "game" : "games"
    } found`;

  if (filteredGames.length === 0) {
    const message = document.createElement("p");

    message.className = "message";
    message.textContent =
      "No games found. The journal gremlins checked every shelf.";

    results.appendChild(message);
    return;
  }

  const fragment = document.createDocumentFragment();

  filteredGames.forEach((game) => {
    fragment.appendChild(createGameCard(game));
  });

  results.appendChild(fragment);
}

function setActiveVerdict(button) {
  activeVerdict = button.dataset.verdict;

  filterButtons.forEach((candidate) => {
    const isActive = candidate === button;

    candidate.classList.toggle("active", isActive);
    candidate.setAttribute(
      "aria-pressed",
      String(isActive)
    );
  });

  renderGames();
}


/* =========================================================
   Statistics
   ========================================================= */

function renderStatistics() {
  const countByVerdict = (verdict) =>
    games.filter((game) => game.verdict === verdict).length;

  const lostTrackCount =
    countByVerdict("Lost Track of Time");

  const oneMoreRunCount =
    countByVerdict("Just One More Run");

  const worthPackingCount =
    countByVerdict("Worth Packing");

  const leaveHomeCount =
    countByVerdict("Leave at Home");

  statTotal.textContent = String(games.length);
  statLostTrack.textContent = String(lostTrackCount);

  statPackable.textContent = String(
    lostTrackCount +
    oneMoreRunCount +
    worthPackingCount
  );

  statLeaveHome.textContent = String(leaveHomeCount);
}


/* =========================================================
   Featured review
   ========================================================= */

function renderFeaturedReview() {
  const favourites = games.filter(
    (game) => game.verdict === "Lost Track of Time"
  );

  const candidates =
    favourites.length > 0 ? favourites : games;

  if (candidates.length === 0) {
    featuredSection.hidden = true;
    return;
  }

  const randomIndex = Math.floor(
    Math.random() * candidates.length
  );

  const game = candidates[randomIndex];
  const emoji = getGameEmoji(game);

  featuredVerdict.textContent =
    `${emoji} ${game.verdict}`;

  featuredTitle.textContent = game.title;
  featuredTitle.href = game.url;

  featuredDetails.textContent =
    getDetailParts(game).join(" · ");

  featuredLink.href = game.url;

  featuredSection.hidden = false;
}


/* =========================================================
   Events
   ========================================================= */

searchInput.addEventListener("input", renderGames);
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


/* =========================================================
   Load the journal
   ========================================================= */

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
  })

  .catch((error) => {
    console.error(error);

    resultCount.textContent =
      "The journal could not be loaded.";

    const message = document.createElement("p");

    message.className = "message";
    message.textContent =
      "The searchable journal is temporarily unavailable. " +
      "The reviews are still available on GitHub.";

    results.replaceChildren(message);
  });
