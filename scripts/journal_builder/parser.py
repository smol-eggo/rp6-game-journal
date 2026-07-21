from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import markdown

from .config import ROOT, VERDICT_EMOJIS
from .models import GameReview


def clean_markdown(value: str) -> str:
    """Remove common Markdown formatting from a short value."""
    value = re.sub(r"[*_`]", "", value)
    value = re.sub(r"^[^\w]+", "", value)
    return value.strip()


def slugify(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "review"


def extract_title(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return clean_markdown(match.group(1)) if match else fallback


def extract_verdict(content: str) -> str:
    match = re.search(
        r"^##\s+Verdict\s*\n+\s*(.+)$",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if not match:
        return "Unknown"

    raw_value = clean_markdown(match.group(1))
    for verdict in VERDICT_EMOJIS:
        if verdict.casefold() in raw_value.casefold():
            return verdict
    return raw_value


def extract_bullet_value(content: str, label: str) -> str | None:
    pattern = rf"^-\s+\*\*{re.escape(label)}:\*\*\s*(.+)$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    return clean_markdown(match.group(1)) if match else None


def extract_heading_value(content: str, heading: str) -> str | None:
    pattern = rf"^##\s+{re.escape(heading)}\s*\n+\s*(.+)$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    return clean_markdown(match.group(1)) if match else None


def extract_section(content: str, heading: str) -> str | None:
    pattern = (
        rf"^##\s+{re.escape(heading)}\s*$"
        rf"(.*?)(?=^##\s+|\Z)"
    )
    match = re.search(
        pattern,
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else None


def make_description(content: str, title: str) -> str:
    preferred_sections = (
        "smol-eggo's Verdict",
        "Experience",
    )
    source = next(
        (
            section
            for heading in preferred_sections
            if (section := extract_section(content, heading))
        ),
        "",
    )

    source = re.sub(r"!\[[^\]]*]\([^)]+\)", "", source)
    source = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", source)
    source = re.sub(r"[#>*_`~-]", " ", source)
    source = re.sub(r"\s+", " ", source).strip()

    if not source:
        return f"A personal review of {title} from smol-eggo's Game Journal."

    if len(source) > 157:
        source = source[:157].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"
    return source


def get_git_date(path: Path) -> tuple[str | None, str]:
    """Return the most recent Git commit date for a review."""
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "-1",
                "--format=%cs",
                "--",
                str(path.relative_to(ROOT)),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        raw_date = result.stdout.strip()
        if raw_date:
            parsed = datetime.strptime(raw_date, "%Y-%m-%d")
            return raw_date, parsed.strftime("%B %Y")
    except (subprocess.CalledProcessError, ValueError):
        pass

    return None, "Date unknown"


def render_markdown(content: str) -> str:
    return markdown.markdown(
        content,
        extensions=[
            "extra",
            "sane_lists",
            "smarty",
        ],
        output_format="html5",
    )


def parse_review(path: Path) -> GameReview:
    content = path.read_text(encoding="utf-8")
    fallback_title = path.stem.replace("-", " ").replace("_", " ").title()
    title = extract_title(content, fallback_title)
    verdict = extract_verdict(content)
    date_iso, date_display = get_git_date(path)

    # File-based slugs stay stable even if a review title is edited later.
    slug = slugify(path.stem)

    return GameReview(
        source_path=path,
        title=title,
        slug=slug,
        verdict=verdict,
        emoji=VERDICT_EMOJIS.get(verdict, "❔"),
        store=(
            extract_bullet_value(content, "Store")
            or extract_heading_value(content, "Platform")
            or "Unknown"
        ),
        device=extract_bullet_value(content, "Device") or "Not listed",
        operating_system=(
            extract_bullet_value(content, "Operating System")
            or "Not listed"
        ),
        compatibility_layer=(
            extract_bullet_value(content, "Compatibility Layer")
            or "Not listed"
        ),
        review_date_iso=date_iso,
        review_date_display=date_display,
        description=make_description(content, title),
        markdown=content,
        rendered_html=render_markdown(content),
    )


def load_reviews(games_dir: Path) -> list[GameReview]:
    if not games_dir.exists():
        raise FileNotFoundError(f"Games directory not found: {games_dir}")

    reviews = [
        parse_review(path)
        for path in sorted(games_dir.glob("*.md"))
    ]
    return sorted(reviews, key=lambda review: review.title.casefold())
