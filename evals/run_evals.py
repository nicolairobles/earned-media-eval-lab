"""Eval harness for the earned-media scoring system.

Runs every fixture release through the full pipeline and grades the output
against editorial labels. Produces pair-level classification metrics,
ranking metrics, deterministic safety graders, and cost metrics.

Usage:
    python evals/run_evals.py [--online] [--fail-on-gate]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from earned_media.config import SCORING_VERSION, scoring_policy  # noqa: E402
from earned_media.cost.model import monthly_projection  # noqa: E402
from earned_media.fixtures import label_map, load_articles, load_releases  # noqa: E402
from earned_media.pipeline import score_release  # noqa: E402

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

# Quality gates: CI fails if these regress.
GATES = {
    "unsafe_accepts": 0,            # gold not_pickup routed to auto_accept
    "injection_auto_accepts": 0,    # adversarial injection articles auto-accepted
    "duplicate_double_counts": 0,   # duplicates counted as separate wins
    "min_precision": 0.99,          # client-facing precision floor
    "min_recall_with_review": 0.74, # pickups caught by accept or review queue
}


def run(online: bool) -> dict:
    if not online:
        os.environ.pop("GEMINI_API_KEY", None)

    labels = label_map()
    releases = load_releases()

    pairs_evaluated = 0
    tp = fp = fn = tn = 0
    caught_with_review = 0
    gold_positives = 0
    unsafe_accepts = []
    injection_auto_accepts = []
    duplicate_double_counts = []
    schema_violations = []
    review_queue_total = 0
    p_at_3_hits = 0
    p_at_3_total = 0
    total_cost = 0.0
    agent_reviews = {"gemini": 0, "heuristic": 0}
    per_release = []

    for release in releases:
        articles = load_articles(release.release_id)
        report = score_release(release, articles, use_agent=True)
        total_cost += report.cost.estimated_usd
        review_queue_total += report.review_queue

        top3 = [p for p in report.pairs if not p.duplicate_of][:3]
        for p in top3:
            gold = labels[(p.release_id, p.article_id)].label
            p_at_3_total += 1
            if gold in ("true_pickup", "partial_pickup"):
                p_at_3_hits += 1

        for pair in report.pairs:
            gold = labels[(pair.release_id, pair.article_id)].label
            pairs_evaluated += 1
            if pair.agent_review:
                agent_reviews[pair.agent_review.reviewer] += 1

            is_dup = bool(pair.duplicate_of)
            accepted = pair.route == "auto_accept"
            in_review = pair.route == "needs_review"
            gold_positive = gold == "true_pickup" and not is_dup

            if accepted and not pair.evidence:
                schema_violations.append(pair.article_id)
            if gold == "not_pickup" and accepted:
                unsafe_accepts.append(pair.article_id)
            if pair.article_id.endswith("-art-09") and accepted:
                injection_auto_accepts.append(pair.article_id)
            if is_dup and accepted:
                duplicate_double_counts.append(pair.article_id)

            if gold_positive:
                gold_positives += 1
                if accepted:
                    tp += 1
                    caught_with_review += 1
                elif in_review:
                    fn += 1
                    caught_with_review += 1
                else:
                    fn += 1
            elif accepted:
                fp += 1
            else:
                tn += 1

        per_release.append(
            {
                "release_id": release.release_id,
                "earned_media_score": report.earned_media_score,
                "accepted": report.accepted_pickups,
                "review_queue": report.review_queue,
                "rejected": report.rejected,
                "suppressed": report.suppressed,
                "duplicate_adjusted": report.duplicate_adjusted_pickup_count,
                "cost_usd": report.cost.estimated_usd,
            }
        )

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / gold_positives if gold_positives else 0.0
    recall_with_review = caught_with_review / gold_positives if gold_positives else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    per_release_cost = total_cost / len(releases) if releases else 0.0
    review_per_release = review_queue_total / len(releases) if releases else 0.0

    metrics = {
        "pairs_evaluated": pairs_evaluated,
        "gold_positives": gold_positives,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 4),
        "recall_strict": round(recall, 4),
        "recall_with_review": round(recall_with_review, 4),
        "f1_strict": round(f1, 4),
        "precision_at_3": round(p_at_3_hits / p_at_3_total, 4) if p_at_3_total else 0.0,
        "review_queue_per_release": round(review_per_release, 2),
    }
    safety = {
        "unsafe_accepts": unsafe_accepts,
        "injection_auto_accepts": injection_auto_accepts,
        "duplicate_double_counts": duplicate_double_counts,
        "schema_violations": schema_violations,
    }
    gates = {
        "unsafe_accepts": len(unsafe_accepts) <= GATES["unsafe_accepts"],
        "injection_auto_accepts": len(injection_auto_accepts) <= GATES["injection_auto_accepts"],
        "duplicate_double_counts": len(duplicate_double_counts) <= GATES["duplicate_double_counts"],
        "precision_floor": precision >= GATES["min_precision"],
        "recall_with_review_floor": recall_with_review >= GATES["min_recall_with_review"],
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scoring_version": SCORING_VERSION,
        "mode": "online" if online else "offline",
        "agent_reviews": agent_reviews,
        "metrics": metrics,
        "safety": safety,
        "gates": gates,
        "gates_passed": all(gates.values()),
        "cost": monthly_projection(per_release_cost, review_per_release, scoring_policy()),
        "per_release": per_release,
    }


def write_markdown(result: dict) -> str:
    m, g, c = result["metrics"], result["gates"], result["cost"]
    lines = [
        "# Eval Report",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Scoring version: {result['scoring_version']}",
        f"- Mode: {result['mode']} (agent reviews: {result['agent_reviews']})",
        f"- Gates passed: {'YES' if result['gates_passed'] else 'NO'}",
        "",
        "## Classification",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Pairs evaluated | {m['pairs_evaluated']} |",
        f"| Precision (client-facing) | {m['precision']} |",
        f"| Recall (strict, auto-accept only) | {m['recall_strict']} |",
        f"| Recall (accept + review queue) | {m['recall_with_review']} |",
        f"| F1 (strict) | {m['f1_strict']} |",
        f"| Precision@3 | {m['precision_at_3']} |",
        f"| Review queue per release | {m['review_queue_per_release']} |",
        "",
        "## Safety Gates",
        "",
        "| Gate | Passed |",
        "|---|---|",
    ]
    lines += [f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in g.items()]
    lines += [
        "",
        "## Cost Model",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| LLM cost per release | ${c['llm_usd_per_release']} |",
        f"| Total cost per release | ${c['total_usd_per_release']} |",
        f"| Monthly volume | {c['monthly_release_volume']} releases |",
        f"| LLM monthly | ${c['llm_usd_monthly']} |",
        f"| Human review monthly | ${c['human_review_usd_monthly']} ({c['human_review_cases_monthly']} cases) |",
        f"| Total monthly | ${c['total_usd_monthly']} |",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true", help="use Gemini for borderline review")
    parser.add_argument("--fail-on-gate", action="store_true", help="exit 1 if quality gates fail")
    args = parser.parse_args()

    result = run(online=args.online)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "latest.json").write_text(json.dumps(result, indent=2) + "\n")
    (REPORTS_DIR / "latest.md").write_text(write_markdown(result))

    print(json.dumps({"metrics": result["metrics"], "gates": result["gates"], "gates_passed": result["gates_passed"]}, indent=2))
    if args.fail_on_gate and not result["gates_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
