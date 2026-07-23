from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass

from .config import SITE_DESCRIPTION, SITE_NAME, SITE_URL
from .models import GameReview


@dataclass(frozen=True)
class ReviewSections:
    experience: str = ""
    verdict: str = ""
    did_i_forget: str = ""


def _value(review: GameReview, name: str, default: str = "") -> str:
    value = getattr(review, name, default)
    return str(value) if value is not None else default


def _plain_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return " ".join(html.unescape(text).split())


def _normalise_heading(fragment: str) -> str:
    value = _plain_text(fragment).casefold()
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"[^a-z0-9']+", " ", value)
    return " ".join(value.split()).strip()


def _clean_section(fragment: str) -> str:
    """Remove generator-only tail copy while preserving the review's HTML."""
    fragment = fragment.strip()
    fragment = re.sub(
        r"<p><em>\s*Reviewed by smol-eggo.*?</em></p>\s*$",
        "",
        fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    fragment = re.sub(
        r"<hr\s*/?>\s*$",
        "",
        fragment,
        flags=re.IGNORECASE,
    )
    return fragment.strip()


def _parse_review_sections(rendered_html: str) -> ReviewSections:
    """Split the canonical Markdown review into the three page-level sections.

    The hero and compatibility panel already own the title, score, and setup.
    Only Experience is rendered in the article body. The written verdict and
    testing answer are moved into the Eggo conclusion card.
    """
    if not rendered_html:
        return ReviewSections()

    heading_pattern = re.compile(
        r"<h(?P<level>[1-6])(?:\s[^>]*)?>(?P<title>.*?)</h(?P=level)>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    matches = list(heading_pattern.finditer(rendered_html))
    sections: dict[str, str] = {}

    for index, match in enumerate(matches):
        heading = _normalise_heading(match.group("title"))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(rendered_html)
        body = _clean_section(rendered_html[start:end])

        if heading == "experience":
            sections["experience"] = body
        elif heading in {"smol eggo's verdict", "smol-eggo's verdict", "smol eggo verdict"}:
            sections["verdict"] = body
        elif heading in {
            "did i forget i was testing",
            "did i forget i was testing?",
        }:
            sections["did_i_forget"] = body

    # Safe fallback for older reviews that do not yet follow the canonical
    # headings. Showing the full review is preferable to silently losing it.
    experience = sections.get("experience", "")
    if not experience:
        experience = _clean_section(rendered_html)

    return ReviewSections(
        experience=experience,
        verdict=sections.get("verdict", ""),
        did_i_forget=sections.get("did_i_forget", ""),
    )


def _emotion_class(verdict: str) -> str:
    verdict_key = verdict.casefold()
    if "lost track" in verdict_key:
        return "eggo-elated"
    if "one more run" in verdict_key:
        return "eggo-hyped"
    if "worth packing" in verdict_key:
        return "eggo-ready"
    if "tinkering" in verdict_key:
        return "eggo-thinking"
    if "leave at home" in verdict_key:
        return "eggo-worried"
    return "eggo-neutral"


def _eggo(verdict: str, extra_class: str = "") -> str:
    classes = " ".join(
        part for part in ("review-eggo", _emotion_class(verdict), extra_class) if part
    )
    return f"""<div class="{classes}" aria-hidden="true">
  <span class="review-eggo-spark review-eggo-spark-one">✦</span>
  <span class="review-eggo-spark review-eggo-spark-two">✦</span>
  <span class="review-eggo-arm review-eggo-arm-left"></span>
  <span class="review-eggo-arm review-eggo-arm-right"></span>
  <span class="review-eggo-body">
    <span class="review-eggo-glasses">
      <span class="review-eggo-lens"></span>
      <span class="review-eggo-lens"></span>
    </span>
    <span class="review-eggo-mouth"></span>
    <span class="review-eggo-cheek review-eggo-cheek-left"></span>
    <span class="review-eggo-cheek review-eggo-cheek-right"></span>
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
    cover_url: str = "",
) -> str:
    title = html.escape(_value(review, "title"))
    verdict = html.escape(_value(review, "verdict"))
    raw_verdict = _value(review, "verdict")
    emoji = html.escape(_value(review, "emoji", "🎮"))
    description = html.escape(_value(review, "description", SITE_DESCRIPTION))
    store = html.escape(_value(review, "store", "Unknown"))
    layer = html.escape(_value(review, "compatibility_layer", "Not recorded"))
    date_display = html.escape(_value(review, "review_date_display", "Date not recorded"))
    relative_url = _value(review, "relative_url", f"/reviews/{_value(review, 'slug')}/")
    canonical = f"{SITE_URL}{relative_url}"
    cover_src = f"../../{cover_url}" if cover_url else ""
    absolute_cover = f"{SITE_URL}/{cover_url}" if cover_url else ""
    hero_class = "review-hero review-hero-with-cover" if cover_url else "review-hero"
    cover_markup = (
        f'<figure class="review-cover"><img src="{html.escape(cover_src)}" '
        f'alt="Cover art for {title}" loading="eager" decoding="async"></figure>'
        if cover_url
        else ""
    )
    social_image_meta = (
        f'<meta property="og:image" content="{html.escape(absolute_cover)}">\n'
        f'  <meta name="twitter:card" content="summary_large_image">\n'
        f'  <meta name="twitter:image" content="{html.escape(absolute_cover)}">'
        if cover_url
        else '<meta name="twitter:card" content="summary">'
    )

    rendered_content = (
        _value(review, "rendered_html")
        or _value(review, "html_content")
        or _value(review, "content_html")
        or _value(review, "body_html")
    )
    sections = _parse_review_sections(rendered_content)
    experience = sections.experience or f"<p>{description}</p>"
    verdict_copy = sections.verdict or f"<p>{description}</p>"
    testing_copy = sections.did_i_forget or "<p>The verdict above is the answer.</p>"
    emotion = _emotion_class(raw_verdict)

    structured_data = {
        "@context": "https://schema.org",
        "@type": "Review",
        "name": html.unescape(title),
        "description": html.unescape(description),
        "url": canonical,
        "author": {"@type": "Person", "name": "smol-eggo"},
        "itemReviewed": {"@type": "VideoGame", "name": html.unescape(title)},
    }

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title} review | {html.escape(SITE_NAME)}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{html.escape(canonical)}">
  {social_image_meta}
  <link rel="canonical" href="{html.escape(canonical)}">
  <link rel="stylesheet" href="../../assets/review-pages.css">
  <title>{title} review | {html.escape(SITE_NAME)}</title>
  <script type="application/ld+json">{json.dumps(structured_data, ensure_ascii=False)}</script>
</head>
<body class="review-score-{emotion}">
  <div class="reading-progress" aria-hidden="true"><span id="reading-progress-bar"></span></div>

  <header class="review-site-header">
    <a class="back-link" href="../../">← Back to the journal</a>
    <span class="review-site-name">{html.escape(SITE_NAME)}</span>
  </header>

  <main class="review-shell">
    <article class="review-article">
      <header class="{hero_class}">
        <div class="review-hero-copy">
          <p class="review-kicker">RP6 field report</p>
          <h1>{title}</h1>
          <p class="review-verdict">{emoji} {verdict}</p>
          <p class="review-description">{description}</p>
          <p class="review-date">Reviewed {date_display}</p>
        </div>
        {cover_markup}
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

      <section class="review-experience" aria-labelledby="experience-title">
        <p class="section-overline">The play session</p>
        <h2 id="experience-title">Experience</h2>
        <div class="review-content">{experience}</div>
      </section>

      <aside class="eggo-conclusion {emotion}" aria-label="Review conclusion">
        <div class="eggo-stage">{_eggo(raw_verdict, "review-eggo-conclusion")}</div>

        <section class="conclusion-verdict" aria-labelledby="written-verdict-title">
          <p class="panel-kicker">smol-eggo’s verdict</p>
          <h2 id="written-verdict-title"><span aria-hidden="true">{emoji}</span> {verdict}</h2>
          <div class="conclusion-copy">{verdict_copy}</div>
        </section>

        <section class="conclusion-testing" aria-labelledby="testing-title">
          <p class="panel-kicker">The question behind every review</p>
          <h2 id="testing-title">Did I forget I was testing?</h2>
          <div class="conclusion-copy">{testing_copy}</div>
        </section>
      </aside>

      <nav class="review-navigation" aria-label="More reviews">
        {_navigation_card(previous_review, "Previous review", "previous")}
        {_navigation_card(next_review, "Next review", "next")}
      </nav>
    </article>
  </main>

  <footer class="review-footer">
    <p>An independent community project by smol-eggo.</p>
    <nav aria-label="Footer links">
      <a href="../../feed.xml">RSS</a>
      <a href="../../sitemap.xml">Sitemap</a>
      <a href="../../">Browse the journal</a>
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


def reviews_index(reviews: list[GameReview]) -> str:
    """Compatibility shim retained for older imports.

    The generator now writes its own redirect for /reviews/, so this function
    should not normally be called.
    """
    del reviews
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=../">
  <link rel="canonical" href="../">
  <title>Back to the RP6 Game Journal</title>
</head>
<body>
  <p><a href="../">Continue to the RP6 Game Journal</a></p>
</body>
</html>"""
