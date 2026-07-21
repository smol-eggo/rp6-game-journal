from __future__ import annotations

import html
import json
from collections.abc import Iterable

from .config import SITE_DESCRIPTION, SITE_NAME, SITE_URL
from .models import GameReview


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def page_shell(
    *,
    title: str,
    description: str,
    canonical_url: str,
    body: str,
    stylesheet_path: str,
    json_ld: dict | None = None,
) -> str:
    structured_data = ""
    if json_ld is not None:
        safe_json = json.dumps(
            json_ld,
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("</", "<\\/")

        structured_data = (
            '\n<script type="application/ld+json">'
            f"{safe_json}</script>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <link rel="canonical" href="{e(canonical_url)}">
  <link rel="stylesheet" href="{e(stylesheet_path)}">
  <link rel="alternate" type="application/rss+xml"
        title="{e(SITE_NAME)} RSS" href="{e(SITE_URL)}/feed.xml">

  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{e(SITE_NAME)}">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{e(canonical_url)}">

  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{e(title)}">
  <meta name="twitter:description" content="{e(description)}">
  {structured_data}
</head>
<body>
{body}
</body>
</html>
"""


def review_page(
    review: GameReview,
    previous_review: GameReview | None,
    next_review: GameReview | None,
) -> str:
    canonical = f"{SITE_URL}{review.relative_url}"
    date_meta = (
        f'<time datetime="{e(review.review_date_iso)}">'
        f"{e(review.review_date_display)}</time>"
        if review.review_date_iso
        else e(review.review_date_display)
    )

    facts = [
        ("Device", review.device),
        ("Operating System", review.operating_system),
        ("Store", review.store),
        ("Compatibility Layer", review.compatibility_layer),
    ]

    fact_html = "\n".join(
        f"<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>"
        for label, value in facts
    )

    previous_link = (
        f'<a class="review-nav-link previous" '
        f'href="../{e(previous_review.slug)}/">'
        f'<span>Previous review</span>{e(previous_review.title)}</a>'
        if previous_review
        else '<span class="review-nav-placeholder"></span>'
    )
    next_link = (
        f'<a class="review-nav-link next" href="../{e(next_review.slug)}/">'
        f'<span>Next review</span>{e(next_review.title)}</a>'
        if next_review
        else '<span class="review-nav-placeholder"></span>'
    )

    body = f"""
<header class="site-header">
  <a class="brand" href="../../">🍇 {e(SITE_NAME)}</a>
  <nav aria-label="Primary navigation">
    <a href="../">All reviews</a>
    <a href="../../feed.xml">RSS</a>
  </nav>
</header>

<main class="review-layout">
  <article class="review-article">
    <header class="review-hero">
      <p class="eyebrow">Game review · {date_meta}</p>
      <h1>{e(review.title)}</h1>
      <p class="verdict">
        <span aria-hidden="true">{e(review.emoji)}</span>
        {e(review.verdict)}
      </p>
      <p class="description">{e(review.description)}</p>
    </header>

    <dl class="test-setup">
      {fact_html}
    </dl>

    <div class="review-content">
      {review.rendered_html}
    </div>
  </article>

  <nav class="review-navigation" aria-label="Adjacent reviews">
    {previous_link}
    {next_link}
  </nav>
</main>

<footer class="site-footer">
  <p>Eggo is always looking for the next adventure.</p>
  <a href="../../">Return to the journal</a>
</footer>
"""

    json_ld = {
        "@context": "https://schema.org",
        "@type": "Review",
        "name": f"{review.title} review",
        "url": canonical,
        "description": review.description,
        "author": {
            "@type": "Person",
            "name": "smol-eggo",
        },
        "itemReviewed": {
            "@type": "VideoGame",
            "name": review.title,
        },
        "reviewBody": review.description,
    }
    if review.review_date_iso:
        json_ld["datePublished"] = review.review_date_iso

    return page_shell(
        title=f"{review.title} review | {SITE_NAME}",
        description=review.description,
        canonical_url=canonical,
        body=body,
        stylesheet_path="../../assets/review-pages.css",
        json_ld=json_ld,
    )


def reviews_index(reviews: Iterable[GameReview]) -> str:
    cards = []
    for review in reviews:
        cards.append(
            f"""
<article class="review-card">
  <p class="card-verdict">{e(review.emoji)} {e(review.verdict)}</p>
  <h2><a href="{e(review.slug)}/">{e(review.title)}</a></h2>
  <p>{e(review.description)}</p>
  <div class="card-meta">
    <span>{e(review.store)}</span>
    <span>{e(review.review_date_display)}</span>
  </div>
</article>
"""
        )

    body = f"""
<header class="site-header">
  <a class="brand" href="../">🍇 {e(SITE_NAME)}</a>
  <nav aria-label="Primary navigation">
    <a aria-current="page" href="./">All reviews</a>
    <a href="../feed.xml">RSS</a>
  </nav>
</header>

<main class="index-layout">
  <header class="index-hero">
    <p class="eyebrow">The complete shelf</p>
    <h1>Game reviews</h1>
    <p>{e(SITE_DESCRIPTION)}</p>
  </header>

  <section class="review-grid" aria-label="All game reviews">
    {''.join(cards)}
  </section>
</main>

<footer class="site-footer">
  <p>Compatibility doesn't matter if you forgot you were testing.</p>
  <a href="../">Return to the journal</a>
</footer>
"""

    return page_shell(
        title=f"Game reviews | {SITE_NAME}",
        description=SITE_DESCRIPTION,
        canonical_url=f"{SITE_URL}/reviews/",
        body=body,
        stylesheet_path="../assets/review-pages.css",
        json_ld={
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Game reviews",
            "url": f"{SITE_URL}/reviews/",
            "description": SITE_DESCRIPTION,
        },
    )
