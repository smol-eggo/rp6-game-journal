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
from .templates import review_page, reviews_index


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def generate_games_json(reviews: list[GameReview]) -> None:
    """
    Preserve the original homepage data contract.

    Existing keys remain unchanged:
    title, verdict, emoji, store, compatibilityLayer, date, url

    reviewUrl is additive, so current journal.js code can safely ignore it
    until you are ready to link cards to the generated review pages.
    """
    games = []
    for review in reviews:
        encoded_filename = quote(review.source_filename)
        games.append(
            {
                "title": review.title,
                "verdict": review.verdict,
                "emoji": review.emoji,
                "store": review.store,
                "compatibilityLayer": review.compatibility_layer,
                "date": review.review_date_display,
                "url": (
                    f"{REPOSITORY_BLOB_URL}/games/{encoded_filename}"
                ),
                "reviewUrl": f"reviews/{review.slug}/",
            }
        )

    write_text(
        GAMES_JSON,
        json.dumps(games, ensure_ascii=False, indent=2),
    )


def generate_review_pages(reviews: list[GameReview]) -> None:
    # Remove stale generated review folders, then recreate them cleanly.
    if REVIEWS_DIR.exists():
        shutil.rmtree(REVIEWS_DIR)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    write_text(REVIEWS_DIR / "index.html", reviews_index(reviews))

    for index, review in enumerate(reviews):
        previous_review = reviews[index - 1] if index > 0 else None
        next_review = (
            reviews[index + 1]
            if index + 1 < len(reviews)
            else None
        )
        output = REVIEWS_DIR / review.slug / "index.html"
        write_text(
            output,
            review_page(review, previous_review, next_review),
        )


def generate_sitemap(reviews: list[GameReview]) -> None:
    entries = [
        (f"{SITE_URL}/", None),
        (f"{SITE_URL}/reviews/", None),
    ]
    entries.extend(
        (
            f"{SITE_URL}{review.relative_url}",
            review.review_date_iso,
        )
        for review in reviews
    )

    url_nodes = []
    for url, modified in entries:
        lastmod = (
            f"\n    <lastmod>{xml_escape(modified)}</lastmod>"
            if modified
            else ""
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
            parsed = datetime.strptime(
                review.review_date_iso,
                "%Y-%m-%d",
            ).replace(tzinfo=timezone.utc)
            pub_date = (
                f"\n      <pubDate>{format_datetime(parsed)}</pubDate>"
            )

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

    generate_games_json(reviews)
    generate_review_pages(reviews)
    generate_sitemap(reviews)
    generate_feed(reviews)
    generate_robots()

    print(
        "Generated "
        f"{len(reviews)} review pages, games.json, sitemap.xml, "
        "feed.xml, and robots.txt."
    )
