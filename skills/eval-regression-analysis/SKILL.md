# Skill: Eval Regression Analysis

Use when an eval run fails a gate or a metric moves unexpectedly.

## Procedure

1. Diff `evals/reports/latest.json` against the last known good report.
2. Locate which gate or metric moved, then which releases contributed via
   the per_release section.
3. Reproduce on the smallest scope: run `score_release` for one release and
   inspect pair-level routes, breakdowns, and policy flags.
4. Classify the cause: fixture change, scoring weight change, threshold
   change, retrieval change, or agent behavior change.
5. Check offline vs online: if only online mode regressed, the reviewer
   agent or its prompt is the cause; the deterministic path is unaffected.
6. Fix forward with a new fixture case when the regression exposed a gap in
   the taxonomy, not just a parameter tweak.
