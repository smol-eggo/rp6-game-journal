from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAMES_DIR = ROOT / "games"
DOCS_DIR = ROOT / "docs"
REVIEWS_DIR = DOCS_DIR / "reviews"
ASSETS_DIR = DOCS_DIR / "assets"

GAMES_JSON = DOCS_DIR / "games.json"
SITEMAP_FILE = DOCS_DIR / "sitemap.xml"
FEED_FILE = DOCS_DIR / "feed.xml"
ROBOTS_FILE = DOCS_DIR / "robots.txt"

SITE_NAME = "smol-eggo's Game Journal"
SITE_DESCRIPTION = (
    "Personal game reviews, handheld impressions, and Retroid Pocket 6 "
    "compatibility notes."
)
SITE_URL = "https://smol-eggo.github.io/rp6-game-journal"
REPOSITORY_BLOB_URL = (
    "https://github.com/smol-eggo/rp6-game-journal/blob/main"
)

VERDICT_EMOJIS = {
    "Lost Track of Time": "🍇",
    "Just One More Run": "☕",
    "Worth Packing": "🎒",
    "Needs Tinkering": "🛠",
    "Leave at Home": "🚧",
}
