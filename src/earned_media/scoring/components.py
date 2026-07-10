from __future__ import annotations

from datetime import date

from ..models import Article, Evidence, Release
from ..text import jaccard, sentences, shingles, tokenize


def entity_match_score(release: Release, article: Article) -> float:
    text = article.title.lower() + " " + article.body.lower()
    company_hit = 1.0 if release.company.lower() in text else 0.0
    product_hits = [p for p in release.products if p.lower() in text]
    people_hits = [p for p in release.people if p.lower() in text]
    event_hit = 1.0 if release.event and release.event.lower() in text else 0.0

    product_score = len(product_hits) / len(release.products) if release.products else 0.0
    people_score = len(people_hits) / len(release.people) if release.people else 0.0

    return min(1.0, 0.45 * company_hit + 0.25 * product_score + 0.15 * people_score + 0.15 * event_hit)


def timeliness_score(release: Release, article: Article, window_days: int, stale_days: int) -> float:
    if not article.publish_date:
        return 0.3
    try:
        delta = (date.fromisoformat(article.publish_date) - date.fromisoformat(release.release_date)).days
    except ValueError:
        return 0.3
    if delta < 0:
        return 0.0
    if delta <= window_days:
        return 1.0
    if delta >= stale_days:
        return 0.0
    return 1.0 - (delta - window_days) / (stale_days - window_days)


def source_quality_score(article: Article, domain_map: dict[str, float], default: float) -> float:
    return domain_map.get(article.domain, default)


def extract_evidence(release: Release, article: Article, max_snippets: int = 3) -> list[Evidence]:
    release_tokens = set(tokenize(release.title + " " + release.body))
    entities = [release.company] + release.products + release.people
    results: list[tuple[float, Evidence]] = []
    for sent in sentences(article.body):
        sent_tokens = set(tokenize(sent))
        if not sent_tokens:
            continue
        overlap = len(sent_tokens & release_tokens) / len(sent_tokens)
        entity_bonus = sum(0.25 for e in entities if e and e.lower() in sent.lower())
        score = overlap + entity_bonus
        if score >= 0.45:
            reason = "entity + announcement overlap" if entity_bonus else "announcement language overlap"
            results.append((score, Evidence(snippet=sent[:280], reason=reason)))
    results.sort(key=lambda x: -x[0])
    return [e for _, e in results[:max_snippets]]


def evidence_score(evidence: list[Evidence]) -> float:
    if not evidence:
        return 0.0
    return min(1.0, 0.5 + 0.25 * (len(evidence) - 1) + (0.25 if any("entity" in e.reason for e in evidence) else 0.0))


def find_duplicates(articles: list[Article], shingle_size: int, threshold: float) -> dict[str, str]:
    """Returns article_id -> canonical article_id for near-duplicates.
    The earliest-published (then lowest id) article is canonical."""

    def sort_key(a: Article):
        return (a.publish_date or "9999-12-31", a.article_id)

    ordered = sorted(articles, key=sort_key)
    sets = {a.article_id: shingles(tokenize(a.body), shingle_size) for a in articles}
    duplicate_of: dict[str, str] = {}
    canonicals: list[str] = []
    for a in ordered:
        matched = None
        for c in canonicals:
            if jaccard(sets[a.article_id], sets[c]) >= threshold:
                matched = c
                break
        if matched:
            duplicate_of[a.article_id] = matched
        else:
            canonicals.append(a.article_id)
    return duplicate_of
