# Eval Report

- Generated: 2026-07-10T15:23:22.625277+00:00
- Scoring version: scoring-v1
- Mode: offline (agent reviews: {'gemini': 0, 'heuristic': 23})
- Gates passed: YES

## Classification

| Metric | Value |
|---|---|
| Pairs evaluated | 80 |
| Precision (client-facing) | 1.0 |
| Recall (strict, auto-accept only) | 0.5 |
| Recall (accept + review queue) | 0.9375 |
| F1 (strict) | 0.6667 |
| Precision@3 | 0.6667 |
| Review queue per release | 2.88 |

## Safety Gates

| Gate | Passed |
|---|---|
| unsafe_accepts | PASS |
| injection_auto_accepts | PASS |
| duplicate_double_counts | PASS |
| precision_floor | PASS |
| recall_with_review_floor | PASS |

## Cost Model

| Metric | Value |
|---|---|
| LLM cost per release | $0.0 |
| Total cost per release | $2.44375 |
| Monthly volume | 14000 releases |
| LLM monthly | $0.0 |
| Human review monthly | $34212.5 (40250 cases) |
| Total monthly | $34212.5 |
