from __future__ import annotations

import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
GAMES_DIRECTORY = ROOT / "games"
README_PATH = ROOT / "README.md"

START_MARKER = "<!-- GAME-JOURNAL:START -->"
END_MARKER = "<!-- GAME-JOURNAL:END -->"

RATINGS = {
    "Lost Track of Time": "🍇",
    "Just One More Run": "☕",
    "Worth Packing": "🎒",
    "Needs Tinkering": "🛠",
    "Leave at Home": "🚧",
}


def read_game_title(content: str, fallback: str) -> str:
    """Return the first level-one Markdown heading."""
    match = re.search(r"^#\s+(.+?)\s*$", content, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def read_game_rating(content: str) -> tuple[str, str]:
    """Find one of the known Booberry Scale ratings."""
    for rating, emoji in RATINGS.items():
        if rating.lower() in content.lower():
            return rating, emoji

    return "Unrated", "❔"


def last_commit_timestamp(path: Path) -> int:
    """Return the Unix timestamp of the most recent commit touching a file."""
    relative_path = path.relative_to(ROOT)

    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", str(relative_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    value = result.stdout.strip()

    if value.isdigit():
        return int(value)

    # Useful when testing locally before the file has been committed.
    return int(path.stat().st_mtime)


def collect_games() -> list[dict[str, object]]:
    games: list[dict[str, object]] = []

    if not GAMES_DIRECTORY.exists():
        return games

    for path in sorted(GAMES_DIRECTORY.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        rating, emoji = read_game_rating(content)
        timestamp = last_commit_timestamp(path)

        games.append(
            {
                "title": read_game_title(content, path.stem.replace("-", " ").title()),
                "rating": rating,
                "emoji": emoji,
                "path": path.relative_to(ROOT).as_posix(),
                "timestamp": timestamp,
            }
        )

    return games


def build_section(games: list[dict[str, object]]) -> str:
    counts = Counter(str(game["rating"]) for game in games)

    lines = [
        START_MARKER,
        "## The journal so far",
        "",
        f"**Games tested:** {len(games)}",
        "",
        f"🍇 **Lost Track of Time:** {counts['Lost Track of Time']}  ",
        f"☕ **Just One More Run:** {counts['Just One More Run']}  ",
        f"🎒 **Worth Packing:** {counts['Worth Packing']}  ",
        f"🛠 **Needs Tinkering:** {counts['Needs Tinkering']}  ",
        f"🚧 **Leave at Home:** {counts['Leave at Home']}",
        "",
        "## Recently tested",
        "",
    ]

    recent_games = sorted(
        games,
        key=lambda game: int(game["timestamp"]),
        reverse=True,
    )[:5]

    if not recent_games:
        lines.append("*No games have wandered into the journal yet.*")
    else:
        for game in recent_games:
            encoded_path = quote(str(game["path"]), safe="/")
            tested_date = datetime.fromtimestamp(
                int(game["timestamp"])
            ).strftime("%B %Y")

            lines.append(
                f"- {game['emoji']} "
                f"[**{game['title']}**]({encoded_path}) "
                f"· {game['rating']} · {tested_date}"
            )

    lines.extend(
        [
            "",
            "*This section is updated automatically whenever the journal changes.*",
            END_MARKER,
        ]
    )

    return "\n".join(lines)


def update_readme() -> None:
    if not README_PATH.exists():
        raise FileNotFoundError("README.md could not be found.")

    readme = README_PATH.read_text(encoding="utf-8")

    if START_MARKER not in readme or END_MARKER not in readme:
        raise RuntimeError(
            "README markers are missing. Add GAME-JOURNAL:START "
            "and GAME-JOURNAL:END first."
        )

    generated_section = build_section(collect_games())

    updated_readme = re.sub(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        generated_section,
        readme,
        flags=re.DOTALL,
    )

    README_PATH.write_text(updated_readme, encoding="utf-8")


if __name__ == "__main__":
    update_readme()
