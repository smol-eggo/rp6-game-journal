from __future__ import annotations

import html
import json

from .config import SITE_DESCRIPTION, SITE_NAME, SITE_URL
from .models import GameReview


def _value(review: GameReview, name: str, default: str = "") -> str:
    value = getattr(review, name, default)
    return str(value) if value is not None else default


def _eggo() -> str:
    return """<div class="review-eggo" aria-hidden="true">
  <span class="review-eggo-arm review-eggo-arm-left"></span>
  <span class="review-eggo-arm review-eggo-arm-right"></span>
  <span class="review-eggo-body">
    <span class="review-eggo-glasses">
      <span class="review-eggo-lens"></span>
      <span class="review-eggo-lens"></span>
    </span>
    <span class="review-eggo-mouth"></span>
  </span>
  <span class="review-eggo-foot review-eggo-foot-left"></span>
  <span class="review-eggo-foot review-eggo-foot-right"></span>
</div>"""


def _navigation_card(review: GameReview | None, label: str, direction: str) -> str:
    if review is None:
        return '<span class="review-nav-card review-nav-card-empty" aria-hidden="true"></span>'

    title = html.escape(_value(review, "title"))
    emoji = html.escape(_value(review, "emoji", "🎮"))
    verdict = html.escape(_value(review, "verdict"))
    url = html.escape(_value(review, "relative_url", f"/reviews/{_value(review, 'slug')}/"))
    arrow = "←" if direction == "previous" else "→"
    return f"""<a class="review-nav-card review-nav-card-{direction}" href="{url}">
  <span class="review-nav-label">{arrow} {label}</span>
  <strong>{title}</strong>
  <span>{emoji} {verdict}</span>
</a>"""


def review_page(
    review: GameReview,
    previous_review: GameReview | None,
    next_review: GameReview | None,
) -> str:
    title = html.escape(_value(review, "title"))
    verdict = html.escape(_value(review, "verdict"))
    emoji = html.escape(_value(review, "emoji", "🎮"))
    description = html.escape(_value(review, "description", SITE_DESCRIPTION))
    store = html.escape(_value(review, "store", "Unknown"))
    layer = html.escape(_value(review, "compatibility_layer", "Not recorded"))
    date_display = html.escape(_value(review, "review_date_display", "Date not recorded"))
    relative_url = _value(review, "relative_url", f"/reviews/{_value(review, 'slug')}/")
    canonical = f"{SITE_URL}{relative_url}"
    content = _value(review, "html_content") or _value(review, "content_html") or _value(review, "body_html")

    if not content:
        content = f"<p>{description}</p>"

    structured_data = {
        "@context": "https://schema.org",
        "@type": "Review",
        "name": title,
        "description": description,
        "url": canonical,
        "author": {"@type": "Person", "name": "smol-eggo"},
        "itemReviewed": {"@type": "VideoGame", "name": title},
    }

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}">
  <link rel="canonical" href="{html.escape(canonical)}">
  <link rel="stylesheet" href="../../assets/review-pages.css">
  <title>{title} review | {html.escape(SITE_NAME)}</title>
  <script type="application/ld+json">{json.dumps(structured_data, ensure_ascii=False)}</script>
</head>
<body>
  <div class="reading-progress" aria-hidden="true"><span id="reading-progress-bar"></span></div>

  <header class="review-site-header">
    <a class="back-link" href="../../">← Back to the journal</a>
    <span class="review-site-name">{html.escape(SITE_NAME)}</span>
  </header>

  <main class="review-shell">
    <article class="review-article">
      <header class="review-hero">
        <p class="review-kicker">RP6 field report</p>
        <h1>{title}</h1>
        <p class="review-verdict">{emoji} {verdict}</p>
        <p class="review-description">{description}</p>
        <p class="review-date">Reviewed {date_display}</p>
      </header>

      <section class="compatibility-panel" aria-labelledby="setup-title">
        <div>
          <p class="panel-kicker">Test setup</p>
          <h2 id="setup-title">RP6 compatibility</h2>
        </div>
        <dl>
          <div><dt>Device</dt><dd>Retroid Pocket 6</dd></div>
          <div><dt>OS</dt><dd>Armada</dd></div>
          <div><dt>Store</dt><dd>{store}</dd></div>
          <div><dt>Compatibility layer</dt><dd>{layer}</dd></div>
        </dl>
      </section>

      <div class="review-content">
        {content}
      </div>

      <aside class="testing-answer">
        {_eggo()}
        <div>
          <p class="panel-kicker">The question behind every review</p>
          <h2>Did I forget I was testing?</h2>
          <p>The verdict above is the answer. Compatibility matters most when the hardware fades into the background.</p>
        </div>
      </aside>

      <nav class="review-navigation" aria-label="More reviews">
        {_navigation_card(previous_review, "Previous review", "previous")}
        {_navigation_card(next_review, "Next review", "next")}
      </nav>
    </article>

    <aside class="home-rail">
      {_eggo()}
      <h2>You’re heading the right way.</h2>
      <p>The homepage now contains the complete searchable journal.</p>
      <a href="../../">Browse every review →</a>
    </aside>
  </main>

  <footer class="review-footer">
    <p>An independent community project by smol-eggo.</p>
    <nav aria-label="Footer links">
      <a href="../../feed.xml">RSS</a>
      <a href="../../sitemap.xml">Sitemap</a>
      <a href="../../">Back to top</a>
    </nav>
  </footer>

  <script>
    (() => {{
      const bar = document.querySelector('#reading-progress-bar');
      const update = () => {{
        const height = document.documentElement.scrollHeight - window.innerHeight;
        const progress = height > 0 ? window.scrollY / height : 0;
        bar.style.transform = `scaleX(${{Math.min(1, Math.max(0, progress))}})`;
      }};
      update();
      addEventListener('scroll', update, {{ passive: true }});
      addEventListener('resize', update);
    }})();
  </script>
</body>
</html>"""
