from earned_media.fixtures import load_articles, load_releases
from earned_media.models import Article, Release
from earned_media.scoring.components import (
    entity_match_score,
    extract_evidence,
    find_duplicates,
    timeliness_score,
)


def _release() -> Release:
    return load_releases()[0]


def _articles() -> list[Article]:
    return load_articles(_release().release_id)


def test_entity_match_rewards_company_mention():
    rel = _release()
    arts = {a.article_id: a for a in _articles()}
    direct = entity_match_score(rel, arts["rel-001-art-01"])
    unrelated_industry = entity_match_score(rel, arts["rel-001-art-06"])
    assert direct > 0.6
    assert unrelated_industry < 0.2


def test_timeliness_window():
    rel = _release()
    arts = {a.article_id: a for a in _articles()}
    in_window = timeliness_score(rel, arts["rel-001-art-01"], 14, 45)
    stale = timeliness_score(rel, arts["rel-001-art-07"], 14, 45)
    assert in_window == 1.0
    assert stale == 0.0


def test_syndicated_duplicate_detected():
    dups = find_duplicates(_articles(), shingle_size=5, threshold=0.55)
    assert "rel-001-art-03" in dups
    assert dups["rel-001-art-03"] == "rel-001-art-01"


def test_evidence_extracted_for_true_pickup():
    rel = _release()
    arts = {a.article_id: a for a in _articles()}
    assert extract_evidence(rel, arts["rel-001-art-01"])
