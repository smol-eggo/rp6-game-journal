from __future__ import annotations

import html
import json
from collections.abc import Iterable

from .config import SITE_DESCRIPTION, SITE_NAME, SITE_URL
from .models import GameReview


def e(value: object) -> str:
    """Escape a value before placing it in generated HTML."""
    return html.escape(str(value), quote=True)


def page_shell(
    *,
    title: str,
    description: str,
    canonical_url: str,
    body: str,
    stylesheet_path: str,
    page_type: str = "website",
    json_ld: dict | None = None,
) -> str:
    """Render the shared document shell used by generated journal pages."""
    structured_data = ""

    if json_ld is not None:
        safe_json = json.dumps(
            json_ld,
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("</", "<\\/")

        structured_data = (
            '\n  <script type="application/ld+json">'
            f"{safe_json}</script>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="theme-color" content="#100d18">

  <link rel="canonical" href="{e(canonical_url)}">
  <link rel="stylesheet" href="{e(stylesheet_path)}">
  <link
    rel="alternate"
    type="application/rss+xml"
    title="{e(SITE_NAME)} RSS"
    href="{e(SITE_URL)}/feed.xml"
  >

  <meta property="og:type" content="{e(page_type)}">
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
  <a class="skip-link" href="#main-content">Skip to the review</a>
  <div class="reading-progress" aria-hidden="true">
    <span class="reading-progress-bar"></span>
  </div>

{body}

  <script>
    (() => {{
      const progressBar = document.querySelector(".reading-progress-bar");

      if (!progressBar) {{
        return;
      }}

      const updateProgress = () => {{
        const scrollable =
          document.documentElement.scrollHeight - window.innerHeight;

        const progress =
          scrollable > 0
            ? Math.min(window.scrollY / scrollable, 1)
            : 0;

        progressBar.style.transform = `scaleX(${{progress}})`;
      }};

      updateProgress();
      window.addEventListener("scroll", updateProgress, {{ passive: true }});
      window.addEventListener("resize", updateProgress);
    }})();
  </script>
</body>
</html>
"""


def review_page(
    review: GameReview,
    previous_review: GameReview | None,
    next_review: GameReview | None,
) -> str:
    """Render one complete game-review page."""
    canonical = f"{SITE_URL}{review.relative_url}"

    if review.review_date_iso:
        date_meta = (
            f'<time datetime="{e(review.review_date_iso)}">'
            f"{e(review.review_date_display)}</time>"
        )
    else:
        date_meta = e(review.review_date_display)

    facts = [
        ("Device", review.device),
        ("Operating system", review.operating_system),
        ("Store", review.store),
        ("Compatibility layer", review.compatibility_layer),
    ]

    fact_html = "\n".join(
        f"""
        <div class="setup-item">
          <dt>{e(label)}</dt>
          <dd>{e(value)}</dd>
        </div>
        """
        for label, value in facts
    )

    previous_link = (
        f"""
        <a
          class="review-nav-link review-nav-previous"
          href="../{e(previous_review.slug)}/"
          rel="prev"
        >
          <span class="review-nav-direction">← Previous review</span>
          <strong>{e(previous_review.title)}</strong>
          <small>
            {e(previous_review.emoji)} {e(previous_review.verdict)}
          </small>
        </a>
        """
        if previous_review
        else '<span class="review-nav-placeholder" aria-hidden="true"></span>'
    )

    next_link = (
        f"""
        <a
          class="review-nav-link review-nav-next"
          href="../{e(next_review.slug)}/"
          rel="next"
        >
          <span class="review-nav-direction">Next review →</span>
          <strong>{e(next_review.title)}</strong>
          <small>
            {e(next_review.emoji)} {e(next_review.verdict)}
          </small>
        </a>
        """
        if next_review
        else '<span class="review-nav-placeholder" aria-hidden="true"></span>'
    )

    body = f"""
  <header class="site-header">
    <a class="brand" href="../../" aria-label="{e(SITE_NAME)} home">
      <span class="brand-mark" aria-hidden="true">🍇</span>
      <span>{e(SITE_NAME)}</span>
    </a>

    <nav class="site-nav" aria-label="Primary navigation">
      <a href="../">All reviews</a>
      <a href="../../feed.xml">RSS</a>
    </nav>
  </header>

  <main id="main-content" class="review-layout">
    <article class="review-article">
      <header class="review-hero">
        <a class="back-link" href="../">← Back to all reviews</a>

        <div class="review-kicker">
          <span>Game review</span>
          <span aria-hidden="true">·</span>
          <span>{date_meta}</span>
        </div>

        <h1>{e(review.title)}</h1>

        <div class="verdict-badge">
          <span class="verdict-emoji" aria-hidden="true">
            {e(review.emoji)}
          </span>
          <span>
            <small>smol-eggo's verdict</small>
            <strong>{e(review.verdict)}</strong>
          </span>
        </div>

        <p class="review-description">{e(review.description)}</p>
      </header>

      <section class="compatibility-panel" aria-labelledby="setup-heading">
        <div class="compatibility-heading">
          <div>
            <p class="section-label">Handheld compatibility</p>
            <h2 id="setup-heading">RP6 test setup</h2>
          </div>

          <p class="compatibility-verdict">
            <span aria-hidden="true">{e(review.emoji)}</span>
            {e(review.verdict)}
          </p>
        </div>

        <dl class="test-setup">
          {fact_html}
        </dl>
      </section>

      <div class="article-divider" aria-hidden="true">
        <span>🍇</span>
      </div>

      <div class="review-content">
        {review.rendered_html}
      </div>

      <footer class="article-ending">
        <div class="article-ending-mark" aria-hidden="true">🍇</div>

        <p class="section-label">Filed in the journal</p>
        <h2>Compatibility doesn't matter if you forgot you were testing.</h2>

        <p>
          Reviewed by <strong>smol-eggo</strong>
          <span aria-hidden="true">·</span>
          {date_meta}
        </p>

        <a class="source-link" href="../../">
          Return to the journal
        </a>
      </footer>
    </article>

    <nav class="review-navigation" aria-label="Adjacent reviews">
      {previous_link}
      {next_link}
    </nav>
  </main>

  <footer class="site-footer">
    <p>Eggo is always looking for the next adventure.</p>
    <div class="footer-links">
      <a href="../">Browse all reviews</a>
      <a href="../../feed.xml">Follow via RSS</a>
    </div>
  </footer>
"""

    json_ld: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Review",
        "name": f"{review.title} review",
        "url": canonical,
        "description": review.description,
        "author": {
            "@type": "Person",
            "name": "smol-eggo",
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": f"{SITE_URL}/",
        },
        "itemReviewed": {
            "@type": "VideoGame",
            "name": review.title,
        },
        "reviewBody": review.description,
    }

    if review.review_date_iso:
        json_ld["datePublished"] = review.review_date_iso
        json_ld["dateModified"] = review.review_date_iso

    return page_shell(
        title=f"{review.title} review | {SITE_NAME}",
        description=review.description,
        canonical_url=canonical,
        body=body,
        stylesheet_path="../../assets/review-pages.css",
        page_type="article",
        json_ld=json_ld,
    )


def reviews_index(reviews: Iterable[GameReview]) -> str:
    """Render the generated archive containing every review."""
    review_list = list(reviews)
    cards: list[str] = []

    for review in review_list:
        cards.append(
            f"""
        <article class="review-card">
          <a class="review-card-link" href="{e(review.slug)}/">
            <div class="review-card-topline">
              <p class="card-verdict">
                <span aria-hidden="true">{e(review.emoji)}</span>
                {e(review.verdict)}
              </p>
              <span class="card-arrow" aria-hidden="true">↗</span>
            </div>

            <h2>{e(review.title)}</h2>
            <p class="review-card-description">
              {e(review.description)}
            </p>

            <div class="card-meta">
              <span>{e(review.store)}</span>
              <span>{e(review.review_date_display)}</span>
            </div>
          </a>
        </article>
        """
        )

    review_word = "review" if len(review_list) == 1 else "reviews"

    body = f"""
  <header class="site-header">
    <a class="brand" href="../" aria-label="{e(SITE_NAME)} home">
      <span class="brand-mark" aria-hidden="true">🍇</span>
      <span>{e(SITE_NAME)}</span>
    </a>

    <nav class="site-nav" aria-label="Primary navigation">
      <a aria-current="page" href="./">All reviews</a>
      <a href="../feed.xml">RSS</a>
    </nav>
  </header>

  <main id="main-content" class="index-layout">
    <header class="index-hero">
      <p class="section-label">The complete shelf</p>
      <h1>Game reviews</h1>
      <p>{e(SITE_DESCRIPTION)}</p>

      <div class="archive-count">
        <strong>{len(review_list)}</strong>
        <span>{review_word} currently in the journal</span>
      </div>
    </header>

    <section class="review-grid" aria-label="All game reviews">
      {''.join(cards)}
    </section>
  </main>

  <footer class="site-footer">
    <p>Compatibility doesn't matter if you forgot you were testing.</p>
    <div class="footer-links">
      <a href="../">Return to the journal</a>
      <a href="../feed.xml">Follow via RSS</a>
    </div>
  </footer>
"""

    return page_shell(
        title=f"Game reviews | {SITE_NAME}",
        description=SITE_DESCRIPTION,
        canonical_url=f"{SITE_URL}/reviews/",
        body=body,
        stylesheet_path="../assets/review-pages.css",
        page_type="website",
        json_ld={
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Game reviews",
            "url": f"{SITE_URL}/reviews/",
            "description": SITE_DESCRIPTION,
            "isPartOf": {
                "@type": "WebSite",
                "name": SITE_NAME,
                "url": f"{SITE_URL}/",
            },
            "numberOfItems": len(review_list),
        },
    )
