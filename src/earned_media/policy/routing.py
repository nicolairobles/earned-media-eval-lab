from __future__ import annotations

from typing import Any

from ..models import PairScore

OVERCLAIM_PATTERNS = [
    "guaranteed coverage",
    "went viral",
    "massive reach",
    "definitively caused",
    "proves the campaign",
]


def route_pair(pair: PairScore, policy: dict[str, Any]) -> PairScore:
    routes = policy["routes"]
    flags: list[str] = list(pair.policy_flags)

    if not pair.url or not pair.title or not pair.outlet:
        flags.append("missing_metadata")
    if not pair.evidence:
        flags.append("missing_evidence")

    suppress = {"missing_evidence", "missing_metadata", "overclaim_detected"} & set(flags)
    if suppress and pair.earned_media_score >= routes["needs_review"]["min_earned_media_score"]:
        pair.route = "suppress"
        pair.policy_flags = flags
        return pair

    aa = routes["auto_accept"]
    if (
        pair.earned_media_score >= aa["min_earned_media_score"]
        and pair.breakdown.entity_match_score >= aa["min_entity_match_score"]
        and pair.breakdown.evidence_score >= aa["min_evidence_score"]
        and not (aa["disallow_duplicates"] and pair.duplicate_of)
        and not flags
    ):
        pair.route = "auto_accept"
    elif pair.earned_media_score >= routes["needs_review"]["min_earned_media_score"]:
        pair.route = "needs_review"
    else:
        pair.route = "reject"

    pair.policy_flags = flags
    return pair


def check_overclaim(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in OVERCLAIM_PATTERNS)
