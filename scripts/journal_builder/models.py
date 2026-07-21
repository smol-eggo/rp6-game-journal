from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GameReview:
    source_path: Path
    title: str
    slug: str
    verdict: str
    emoji: str
    store: str
    device: str
    operating_system: str
    compatibility_layer: str
    review_date_iso: str | None
    review_date_display: str
    description: str
    markdown: str
    rendered_html: str

    @property
    def relative_url(self) -> str:
        return f"/reviews/{self.slug}/"

    @property
    def source_filename(self) -> str:
        return self.source_path.name
