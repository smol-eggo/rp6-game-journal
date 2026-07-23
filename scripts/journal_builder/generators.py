from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

from .config import (
    DOCS_DIR,
    FEED_FILE,
    GAMES_DIR,
    GAMES_JSON,
    REPOSITORY_BLOB_URL,
    REVIEWS_DIR,
    ROBOTS_FILE,
    SITE_DESCRIPTION,
    SITE_NAME,
    SITE_URL,
    SITEMAP_FILE,
)
from .models import GameReview
from .parser import load_reviews
from .templates import review_page


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


COVER_EXTENSIONS = (".webp", ".avif", ".png", ".jpg", ".jpeg")
REPOSITORY_ROOT = GAMES_DIR.parent
SOURCE_COVERS_DIR = REPOSITORY_ROOT / "assets" / "covers"
PUBLIC_COVERS_DIR = DOCS_DIR / "assets" / "covers"


def sync_covers() -> int:
    """Copy source covers into the folder published by GitHub Pages.

    Source artwork belongs in ``assets/covers`` at the repository root. The
    generated website is served from ``docs``, so each supported image is
    copied to ``docs/assets/covers`` before games.json and review pages are
    generated.
    """
    PUBLIC_COVERS_DIR.mkdir(parents=True, exist_ok=True)

    if not SOURCE_COVERS_DIR.exists():
        print(f"No source cover folder found at {SOURCE_COVERS_DIR}")
        return 0

    copied = 0
    for source in sorted(SOURCE_COVERS_DIR.iterdir()):
        if not source.is_file():
            continue
        if source.suffix.casefold() not in COVER_EXTENSIONS:
            continue

        destination = PUBLIC_COVERS_DIR / source.name
        shutil.copy2(source, destination)
        copied += 1

    print(
        f"Copied {copied} cover image(s) from "
        f"{SOURCE_COVERS_DIR} to {PUBLIC_COVERS_DIR}."
    )
    return copied


def cover_url_for(review: GameReview) -> str:
    """Return the published relative URL for a matching review cover."""
    for extension in COVER_EXTENSIONS:
        filename = f"{review.slug}{extension}"
        if (PUBLIC_COVERS_DIR / filename).is_file():
            return f"assets/covers/{filename}"
    return ""


def generate_games_json(reviews: list[GameReview]) -> None:
    """Generate the homepage data while preserving the existing data contract."""
    games = []
    matched_covers = 0
    for review in reviews:
        encoded_filename = quote(review.source_filename)
        cover_url = cover_url_for(review)
        if cover_url:
            matched_covers += 1
        games.append(
            {
                "title": review.title,
                "verdict": review.verdict,
                "emoji": review.emoji,
                "store": review.store,
                "compatibilityLayer": review.compatibility_layer,
                "date": review.review_date_display,
                "url": f"{REPOSITORY_BLOB_URL}/games/{encoded_filename}",
                "reviewUrl": f"reviews/{review.slug}/",
                "coverUrl": cover_url,
            }
        )

    write_text(GAMES_JSON, json.dumps(games, ensure_ascii=False, indent=2))
    print(
        f"Added coverUrl values for {matched_covers} of {len(reviews)} "
        "review(s) in games.json."
    )


def reviews_redirect() -> str:
    """Keep old /reviews/ links useful without maintaining a duplicate archive."""
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <meta http-equiv=\"refresh\" content=\"0; url=../\">
  <link rel=\"canonical\" href=\"../\">
  <title>Back to the RP6 Game Journal</title>
</head>
<body>
  <p>The review archive now lives on the homepage. <a href=\"../\">Go to the journal</a>.</p>
</body>
</html>"""


def generate_review_pages(reviews: list[GameReview]) -> None:
    # Remove stale generated review folders, then recreate them cleanly.
    if REVIEWS_DIR.exists():
        shutil.rmtree(REVIEWS_DIR)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    # /reviews/ is intentionally only a redirect. The homepage is the archive.
    write_text(REVIEWS_DIR / "index.html", reviews_redirect())

    for index, review in enumerate(reviews):
        previous_review = reviews[index - 1] if index > 0 else None
        next_review = reviews[index + 1] if index + 1 < len(reviews) else None
        output = REVIEWS_DIR / review.slug / "index.html"
        write_text(
            output,
            review_page(
                review,
                previous_review,
                next_review,
                cover_url=cover_url_for(review),
            ),
        )


def generate_sitemap(reviews: list[GameReview]) -> None:
    # Do not list /reviews/ separately because it redirects to the homepage.
    entries = [(f"{SITE_URL}/", None)]
    entries.extend(
        (f"{SITE_URL}{review.relative_url}", review.review_date_iso)
        for review in reviews
    )

    url_nodes = []
    for url, modified in entries:
        lastmod = (
            f"\n    <lastmod>{xml_escape(modified)}</lastmod>" if modified else ""
        )
        url_nodes.append(
            "  <url>\n"
            f"    <loc>{xml_escape(url)}</loc>"
            f"{lastmod}\n"
            "  </url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(url_nodes)
        + "\n</urlset>"
    )
    write_text(SITEMAP_FILE, xml)


def generate_feed(reviews: list[GameReview]) -> None:
    dated_reviews = sorted(
        reviews,
        key=lambda review: review.review_date_iso or "0000-00-00",
        reverse=True,
    )[:20]

    build_date = format_datetime(datetime.now(timezone.utc))
    items = []

    for review in dated_reviews:
        link = f"{SITE_URL}{review.relative_url}"
        pub_date = ""
        if review.review_date_iso:
            parsed = datetime.strptime(review.review_date_iso, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            pub_date = f"\n      <pubDate>{format_datetime(parsed)}</pubDate>"

        items.append(
            "    <item>\n"
            f"      <title>{xml_escape(review.title)}</title>\n"
            f"      <link>{xml_escape(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{xml_escape(link)}</guid>"
            f"{pub_date}\n"
            f"      <description>{xml_escape(review.description)}</description>\n"
            "    </item>"
        )

    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{xml_escape(SITE_NAME)}</title>\n"
        f"    <link>{xml_escape(SITE_URL)}/</link>\n"
        f"    <description>{xml_escape(SITE_DESCRIPTION)}</description>\n"
        "    <language>en</language>\n"
        f"    <lastBuildDate>{build_date}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n  </channel>\n"
        "</rss>"
    )
    write_text(FEED_FILE, rss)


def generate_robots() -> None:
    write_text(
        ROBOTS_FILE,
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml",
    )


def build_site() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    reviews = load_reviews(GAMES_DIR)

    sync_covers()
    generate_games_json(reviews)
    generate_review_pages(reviews)
    generate_sitemap(reviews)
    generate_feed(reviews)
    generate_robots()

    print(
        "Generated "
        f"{len(reviews)} review pages, homepage data, /reviews/ redirect, "
        "sitemap.xml, feed.xml, and robots.txt."
    )


