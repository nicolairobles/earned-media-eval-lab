from __future__ import annotations

import json
from pathlib import Path

from .config import DATA_DIR
from .models import Article, EditorialLabel, Release


def _read_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_releases() -> list[Release]:
    return [Release(**r) for r in _read_jsonl(DATA_DIR / "releases.jsonl")]


def load_articles(release_id: str | None = None) -> list[Article]:
    articles = [Article(**a) for a in _read_jsonl(DATA_DIR / "articles.jsonl")]
    if release_id:
        articles = [a for a in articles if a.release_id == release_id]
    return articles


def load_labels() -> list[EditorialLabel]:
    return [EditorialLabel(**l) for l in _read_jsonl(DATA_DIR / "editorial-labels.jsonl")]


def label_map() -> dict[tuple[str, str], EditorialLabel]:
    return {(l.release_id, l.article_id): l for l in load_labels()}
