# Product Brief: Earned Media Eval Lab

## Problem

A newswire company can distribute press releases but cannot credibly prove
which media outlets picked them up. Manual editorial analysis exists for
select clients but does not scale. An AI similarity score alone is not a
product: clients only pay for a pickup metric they can trust.

## Product

An evaluation workbench for earned-media measurement. Given a press release
and a set of candidate articles, the system:

1. Shortlists candidates with lexical retrieval (BM25).
2. Scores each release/article pair on similarity, entity match, source
   quality, timeliness, and evidence quality.
3. Detects syndicated near-duplicates so they cannot inflate the metric.
4. Composes a conservative earned-media score.
5. Routes every pair through threshold policy: auto-accept, needs review,
   reject, or suppress.
6. Sends borderline cases to an LLM review agent (Gemini) whose promotions
   are gated by deterministic policy.
7. Reports client-facing results only for pairs that pass every gate.

## Trust Requirements

- A false positive shown to a client is the worst failure mode.
- A false negative undermines the product promise; borderline cases go to a
  human review queue rather than being silently dropped.
- Every accepted result must carry URL, title, outlet, and evidence snippets.
- Duplicates count once.
- Every run must include cost telemetry.

## Non-Goals

- Comprehensive coverage of the entire web.
- Publishing low-confidence results without review.
- Autonomous client communication. The system drafts and routes; humans send.

## Success Criteria (MVP)

- Client-facing precision >= 0.99 on the labeled fixture set.
- Recall (accept + review queue) >= 0.75.
- Zero unsafe accepts, zero duplicate double counts, zero injection
  promotions on the adversarial cases.
- Cost per release and monthly projection reported on every eval run.
