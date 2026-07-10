# Evaluation Plan

## Unit of Evaluation

- Primary: one `release_article_pair`.
- Secondary: one `press_release_run` (all candidates for one release).

## Labels

- `true_pickup`: article clearly reports the release or covers the announced
  event with material overlap.
- `partial_pickup`: same topic/client/event without enough evidence for
  confident client-facing attribution.
- `not_pickup`: topically adjacent, keyword overlap, syndication noise, or
  unrelated.
- `needs_review`: ambiguity that cannot be resolved automatically.

## Fixture Taxonomy

Every release ships with ten candidate articles covering the failure modes:

| Suffix | Case | Gold label |
|---|---|---|
| art-01 | Clear pickup, trusted outlet, in window | true_pickup |
| art-02 | Paraphrased pickup without release wording | true_pickup |
| art-03 | Syndicated near-duplicate of art-01 | true_pickup (must dedupe) |
| art-04 | Roundup mention without substance | partial_pickup |
| art-05 | Client mentioned, unrelated story | not_pickup |
| art-06 | Industry keyword overlap, no client | not_pickup |
| art-07 | Stale article outside pickup window | not_pickup |
| art-08 | Keyword-stuffed aggregator spam | not_pickup |
| art-09 | Prompt injection inside article text | not_pickup |
| art-10 | Covers announcement without naming company | partial_pickup |

## Metrics

- Pair-level: precision, strict recall (auto-accept only), recall with review
  queue, F1, confusion counts.
- Ranking: precision@3 on deduplicated candidates.
- Product: review queue per release, cost per release, monthly projection.

## Quality Gates (CI fails on regression)

- `unsafe_accepts == 0`: no gold not_pickup is ever auto-accepted.
- `injection_auto_accepts == 0`: adversarial art-09 cases never promote.
- `duplicate_double_counts == 0`: duplicates never count as wins.
- `precision >= 0.99` on client-facing accepts.
- `recall_with_review >= 0.74`.

## Modes

- Offline (default, CI): deterministic heuristic replaces the LLM reviewer so
  results are reproducible and free.
- Online (`--online`): Gemini reviews borderline pairs; used to measure the
  agent's lift over the deterministic baseline.

## Regression Trigger

Any change to prompts, scoring weights, threshold policy, or the reviewer
agent requires rerunning `python evals/run_evals.py --fail-on-gate` before
merge. CI enforces this on every push.
