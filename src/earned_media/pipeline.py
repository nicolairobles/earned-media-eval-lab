from __future__ import annotations

from datetime import datetime, timezone

from .agent.reviewer import BorderlineReviewAgent, apply_agent_review
from .config import SCORING_VERSION, scoring_policy, threshold_policy
from .cost.model import CostMeter
from .models import Article, EarnedMediaReport, PairScore, Release, ScoreBreakdown
from .policy.routing import route_pair
from .scoring.components import (
    entity_match_score,
    evidence_score,
    extract_evidence,
    find_duplicates,
    source_quality_score,
    timeliness_score,
)
from .text import BM25, TfIdfIndex


def _confidence_band(score: float, bands: dict[str, float]) -> str:
    if score >= bands["high"]:
        return "high"
    if score >= bands["medium"]:
        return "medium"
    return "low"


def _initial_label(pair: PairScore) -> str:
    if pair.route == "auto_accept":
        return "true_pickup"
    if pair.route == "needs_review":
        return "needs_review"
    return "not_pickup"


def score_release(
    release: Release,
    articles: list[Article],
    use_agent: bool = True,
) -> EarnedMediaReport:
    sp = scoring_policy()
    tp = threshold_policy()
    meter = CostMeter(sp)

    corpus = {a.article_id: a.title + "\n" + a.body for a in articles}
    release_doc_id = f"__release__{release.release_id}"
    corpus[release_doc_id] = release.title + "\n" + release.body

    bm25 = BM25(corpus, k1=sp["retrieval"]["bm25_k1"], b=sp["retrieval"]["bm25_b"])
    shortlist_ids = {
        d for d, s in bm25.rank(release.title + " " + release.body, sp["retrieval"]["bm25_top_k"] + 1)
        if d != release_doc_id
    }
    tfidf = TfIdfIndex(corpus)

    dd = sp["duplicate_detection"]
    duplicate_of = find_duplicates(articles, dd["shingle_size"], dd["jaccard_threshold"])

    w = sp["weights"]
    pen = sp["penalties"]
    tl = sp["timeliness"]
    sq = sp["source_quality"]

    pairs: list[PairScore] = []
    for article in articles:
        if article.article_id not in shortlist_ids:
            continue
        similarity = round(tfidf.similarity(release_doc_id, article.article_id), 4)
        entity = round(entity_match_score(release, article), 4)
        timeliness = round(timeliness_score(release, article, tl["pickup_window_days"], tl["stale_after_days"]), 4)
        source = source_quality_score(article, sq["domains"], sq["default"])
        evidence = extract_evidence(release, article)
        ev_score = round(evidence_score(evidence), 4)
        is_dup = article.article_id in duplicate_of
        novelty = 0.0 if is_dup else 1.0

        raw = (
            w["similarity"] * similarity
            + w["entity_match"] * entity
            + w["source_quality"] * source
            + w["timeliness"] * timeliness
            + w["evidence"] * ev_score
        )
        if is_dup:
            raw -= pen["duplicate"]
        if not evidence:
            raw -= pen["low_evidence"]
        ems = round(max(0.0, min(1.0, raw)), 4)

        pair = PairScore(
            release_id=release.release_id,
            article_id=article.article_id,
            url=article.url,
            title=article.title,
            outlet=article.outlet,
            publish_date=article.publish_date,
            breakdown=ScoreBreakdown(
                similarity_score=similarity,
                entity_match_score=entity,
                novelty_score=novelty,
                source_quality_score=source,
                timeliness_score=timeliness,
                evidence_score=ev_score,
            ),
            earned_media_score=ems,
            predicted_label="needs_review",
            confidence_band=_confidence_band(ems, sp["confidence_bands"]),
            route="reject",
            duplicate_of=duplicate_of.get(article.article_id),
            evidence=evidence,
        )
        pair = route_pair(pair, tp)
        pair.predicted_label = _initial_label(pair)
        pairs.append(pair)

    pairs.sort(key=lambda p: (-p.earned_media_score, p.article_id))

    if use_agent and tp["agent_review"]["enabled"]:
        agent = BorderlineReviewAgent(sp, meter)
        article_map = {a.article_id: a for a in articles}
        reviewed = 0
        for pair in pairs:
            if pair.route != "needs_review":
                continue
            if reviewed >= tp["agent_review"]["max_pairs_per_release"]:
                break
            review = agent.review(release, article_map[pair.article_id], pair)
            apply_agent_review(pair, review, tp)
            reviewed += 1

    accepted = [p for p in pairs if p.route == "auto_accept"]
    review_q = [p for p in pairs if p.route == "needs_review"]
    rejected = [p for p in pairs if p.route == "reject"]
    suppressed = [p for p in pairs if p.route == "suppress"]
    dedup_accepted = [p for p in accepted if not p.duplicate_of]

    release_score = (
        round(sum(p.earned_media_score for p in dedup_accepted) / len(dedup_accepted), 4)
        if dedup_accepted
        else 0.0
    )

    return EarnedMediaReport(
        release_id=release.release_id,
        release_title=release.title,
        company=release.company,
        release_date=release.release_date,
        pairs=pairs,
        accepted_pickups=len(accepted),
        review_queue=len(review_q),
        rejected=len(rejected),
        suppressed=len(suppressed),
        duplicate_adjusted_pickup_count=len(dedup_accepted),
        earned_media_score=release_score,
        cost=meter.telemetry,
        scoring_version=SCORING_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
