from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
GAMES_DIR = ROOT / "games"
OUTPUT_FILE = ROOT / "docs" / "games.json"

REPOSITORY_URL = "https://github.com/smol-eggo/rp6-game-journal/blob/main"

VERDICT_EMOJIS = {
    "Lost Track of Time": "🍇",
    "Just One More Run": "☕",
    "Worth Packing": "🎒",
    "Needs Tinkering": "🛠",
    "Leave at Home": "🚧",
}


def clean_markdown(value: str) -> str:
    """Remove common Markdown formatting from a short value."""
    value = re.sub(r"[*_`]", "", value)
    value = re.sub(r"^[^\w]+", "", value)
    return value.strip()


def extract_title(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return clean_markdown(match.group(1)) if match else fallback


def extract_verdict(content: str) -> str:
    match = re.search(
        r"^## Verdict\s*\n+\s*(.+)$",
        content,
        re.MULTILINE,
    )

    if not match:
        return "Unknown"

    raw_value = clean_markdown(match.group(1))

    for verdict in VERDICT_EMOJIS:
        if verdict.lower() in raw_value.lower():
            return verdict

    return raw_value


def extract_bullet_value(content: str, label: str) -> str | None:
    pattern = rf"^-\s+\*\*{re.escape(label)}:\*\*\s*(.+)$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    return clean_markdown(match.group(1)) if match else None


def extract_heading_value(content: str, heading: str) -> str | None:
    pattern = rf"^## {re.escape(heading)}\s*\n+\s*(.+)$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    return clean_markdown(match.group(1)) if match else None


def extract_store(content: str) -> str:
    return (
        extract_bullet_value(content, "Store")
        or extract_heading_value(content, "Platform")
        or "Unknown"
    )


def extract_compatibility_layer(content: str) -> str:
    return extract_bullet_value(content, "Compatibility Layer") or "Not listed"


def get_git_date(path: Path) -> str:
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
            return parsed.strftime("%B %Y")
    except (subprocess.CalledProcessError, ValueError):
        pass

    return "Date unknown"


def build_game_entry(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")

    title = extract_title(content, path.stem.replace("-", " ").title())
    verdict = extract_verdict(content)

    encoded_filename = quote(path.name)

    return {
        "title": title,
        "verdict": verdict,
        "emoji": VERDICT_EMOJIS.get(verdict, "❔"),
        "store": extract_store(content),
        "compatibilityLayer": extract_compatibility_layer(content),
        "date": get_git_date(path),
        "url": f"{REPOSITORY_URL}/games/{encoded_filename}",
    }


def main() -> None:
    if not GAMES_DIR.exists():
        raise FileNotFoundError(f"Games directory not found: {GAMES_DIR}")

    games = [
        build_game_entry(path)
        for path in sorted(GAMES_DIR.glob("*.md"))
    ]

    games.sort(key=lambda game: game["title"].casefold())

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(games, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)} with {len(games)} games.")


if __name__ == "__main__":
    main()
