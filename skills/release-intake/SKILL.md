# Skill: Release Intake

Use when adding a new press release and its candidate articles to fixtures.

## Procedure

1. Add the release to RELEASES in `scripts/generate_fixtures.py` with
   company, one product, one spokesperson, event type, industry, date, and a
   body whose first sentence states the core announcement.
2. Ensure the generated candidates cover the full taxonomy in
   `specs/evaluation-plan.md` (art-01 through art-10).
3. Regenerate fixtures: `python scripts/generate_fixtures.py`.
4. Run `pytest -q` and `python evals/run_evals.py --fail-on-gate`.
5. Commit the generator change and regenerated JSONL together.
