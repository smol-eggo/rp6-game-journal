"use strict";

let games = [];
let activeVerdict = "all";

const searchInput = document.querySelector("#search");
const results = document.querySelector("#results");
const resultCount = document.querySelector("#result-count");
const filterButtons = document.querySelectorAll("[data-verdict]");
const sortSelect = document.querySelector("#sort");

function normalise(value) {
  return String(value ?? "").trim().toLowerCase();
}

function createGameCard(game) {
  const article = document.createElement("article");
  article.className = "game-card";

  const verdict = document.createElement("p");
  verdict.className = "verdict";
  verdict.textContent = `${game.emoji} ${game.verdict}`;

  const title = document.createElement("h2");

  const link = document.createElement("a");
  link.href = game.url;
  link.textContent = game.title;

  title.appendChild(link);

  const details = document.createElement("p");
  details.className = "details";

  const detailParts = [game.store];

  if (
    game.compatibilityLayer &&
    game.compatibilityLayer !== "Not listed"
  ) {
    detailParts.push(game.compatibilityLayer);
  }

  detailParts.push(game.date);

  details.textContent = detailParts.join(" · ");

  article.append(verdict, title, details);

  return article;
}

function getFilteredGames() {
  const query = normalise(searchInput.value);

  const filtered = games.filter((game) => {
    const searchableText = normalise([
      game.title,
      game.verdict,
      game.store,
      game.compatibilityLayer,
      game.date,
    ].join(" "));

    const matchesSearch = searchableText.includes(query);

    const matchesVerdict =
      activeVerdict === "all" ||
      game.verdict === activeVerdict;

    return matchesSearch && matchesVerdict;
  });

  if (sortSelect.value === "verdict") {
    return filtered.sort((a, b) =>
      a.verdict.localeCompare(b.verdict) ||
      a.title.localeCompare(b.title)
    );
  }

  return filtered.sort((a, b) =>
    a.title.localeCompare(b.title)
  );
}

function renderGames() {
  const filteredGames = getFilteredGames();

  results.replaceChildren();

  resultCount.textContent =
    `${filteredGames.length} ${filteredGames.length === 1 ? "game" : "games"} found`;

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
    candidate.setAttribute("aria-pressed", String(isActive));
  });

  renderGames();
}

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

fetch("./games.json")
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Could not load games.json (${response.status}).`);
    }

    return response.json();
  })
  .then((data) => {
    if (!Array.isArray(data)) {
      throw new Error("The journal data has an unexpected format.");
    }

    games = data;
    renderGames();
  })
  .catch((error) => {
    console.error(error);

    resultCount.textContent = "The journal could not be loaded.";

    const message = document.createElement("p");
    message.className = "message";
    message.textContent =
      "The searchable journal is temporarily unavailable. The reviews are still available on GitHub.";

    results.replaceChildren(message);
  });
