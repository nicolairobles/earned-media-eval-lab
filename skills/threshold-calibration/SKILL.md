# Skill: Threshold Calibration

Use when tuning `specs/threshold-policy.yaml` routing thresholds.

## Procedure

1. Run `python evals/run_evals.py` to get the current baseline.
2. Identify the tradeoff to move: precision floor, strict recall, or review
   queue volume.
3. Change one threshold at a time. Never remove the entity, evidence,
   duplicate, or suppression guards to gain recall.
4. Rerun evals. Compare precision, recall_with_review, and review queue per
   release against the previous report.
5. Reject any change that produces unsafe accepts, injection promotions, or
   duplicate double counts, regardless of metric gains.
6. Update GATES in `evals/run_evals.py` only when the product owner accepts a
   new floor, and note the rationale in the commit message.
