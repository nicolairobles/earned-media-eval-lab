import os

import pytest

from earned_media.fixtures import label_map, load_articles, load_releases
from earned_media.pipeline import score_release


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture(scope="module")
def reports():
    os.environ.pop("GEMINI_API_KEY", None)
    return {
        r.release_id: score_release(r, load_articles(r.release_id))
        for r in load_releases()
    }


def test_no_unsafe_auto_accepts(reports):
    labels = label_map()
    for report in reports.values():
        for pair in report.pairs:
            gold = labels[(pair.release_id, pair.article_id)].label
            if pair.route == "auto_accept":
                assert gold != "not_pickup", f"{pair.article_id} unsafely accepted"


def test_injection_articles_never_accepted(reports):
    for report in reports.values():
        for pair in report.pairs:
            if pair.article_id.endswith("-art-09"):
                assert pair.route != "auto_accept"


def test_duplicates_never_counted_as_wins(reports):
    for report in reports.values():
        for pair in report.pairs:
            if pair.duplicate_of:
                assert pair.route != "auto_accept"
        assert report.duplicate_adjusted_pickup_count <= report.accepted_pickups


def test_accepted_pairs_have_required_metadata(reports):
    for report in reports.values():
        for pair in report.pairs:
            if pair.route == "auto_accept":
                assert pair.url and pair.title and pair.outlet
                assert pair.evidence, f"{pair.article_id} accepted without evidence"


def test_cost_telemetry_present(reports):
    for report in reports.values():
        assert report.cost is not None


def test_clear_pickup_accepted_for_every_release(reports):
    for rid, report in reports.items():
        accepted = {p.article_id for p in report.pairs if p.route == "auto_accept"}
        assert f"{rid}-art-01" in accepted
