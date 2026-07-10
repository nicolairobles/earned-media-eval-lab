# earned-media-eval-lab

A production-shaped AI evaluation workbench for earned-media measurement.
Given a press release and candidate news articles, it scores each pair,
deduplicates syndicated copies, routes every result through threshold
policy, sends borderline cases to a Gemini review agent gated by
deterministic policy, and reports a client-facing earned-media score only
for results that pass every gate.

Built as the capstone for the Kaggle x Google 5-Day AI Agents Intensive,
rebuilding an earned-media measurement prototype I originally built at a
newswire company, this time with the evaluation discipline the course
teaches: specs first, policy gates around the model, an eval harness with
regression gates in CI, and cost telemetry on every run.

## Why this exists

An LLM similarity score is not a product. Clients only pay for a pickup
metric they can trust:

- A false positive (claiming pickup that did not happen) embarrasses the
  client. Client-facing precision is gated at 0.99 in CI.
- A false negative makes the product look useless. Borderline cases go to a
  human review queue instead of being dropped; recall including that queue
  is gated at 0.74.
- Syndicated duplicates cannot count twice. Prompt injection inside article
  text cannot promote itself. Runs without cost telemetry fail evals.

## Architecture

```text
press release + candidate articles (synthetic fixtures)
        |
   BM25 shortlist  ->  hybrid scoring  ->  duplicate detection
        |                (similarity, entity, source,
        |                 timeliness, evidence)
        v
  threshold policy (specs/threshold-policy.yaml)
    auto_accept | needs_review | reject | suppress
        |
  needs_review only -> Gemini borderline review agent
        |               (strict JSON schema, injection-resistant prompt)
        v
  deterministic policy gate applies or blocks the agent verdict
        |
        v
  earned-media report: score, evidence, routes, cost telemetry
```

Key properties:

- The agent proposes, policy disposes. LLM output can never bypass the
  deterministic gates in `src/earned_media/policy/routing.py`.
- Offline mode replaces the LLM with a deterministic heuristic so CI is
  free, fast, and reproducible. Online mode measures the agent's lift.
- All data is synthetic. Eighty labeled release/article pairs cover ten
  failure modes including paraphrased pickup, syndicated duplicates,
  client-mention noise, stale coverage, aggregator spam, and prompt
  injection (see `specs/evaluation-plan.md`).

## Results (offline, deterministic)

| Metric | Value |
|---|---|
| Client-facing precision | 1.00 |
| Recall (auto-accept only) | 0.50 |
| Recall (accept + review queue) | 0.94 |
| Unsafe accepts / injection promotions / dup double counts | 0 |

Run `python evals/run_evals.py --online` with a `GEMINI_API_KEY` to compare
the agent against the deterministic baseline.

## Run it

```bash
# API + dashboard (fixtures included, no key required)
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cd apps/web && npm ci && npm run build && cd ../..
.venv/bin/uvicorn earned_media.api.main:app --port 8000
# open http://localhost:8000

# tests and evals
.venv/bin/pytest -q
.venv/bin/python evals/run_evals.py --fail-on-gate

# with the Gemini borderline reviewer
export GEMINI_API_KEY=...
.venv/bin/python evals/run_evals.py --online
```

Docker (what Hugging Face Spaces runs):

```bash
docker build -t earned-media-eval-lab .
docker run -p 7860:7860 earned-media-eval-lab
```

## Repository map

```text
specs/      product brief, evaluation plan, BDD scenarios, scoring and
            threshold policies (YAML consumed by the code)
skills/     procedural playbooks: article review, threshold calibration,
            eval regression analysis, release intake
src/        pipeline, scoring components, policy gates, review agent,
            cost model, FastAPI app
data/       committed synthetic fixtures (8 releases, 80 labeled pairs)
scripts/    deterministic fixture generator
evals/      eval harness with CI quality gates and saved reports
apps/web/   Next.js dashboard (static export served by FastAPI)
```

## Course concept mapping

| Course day | Where it shows up |
|---|---|
| Day 1: the harness, not the model | Deterministic pipeline around a narrow LLM role |
| Day 2: tools and interfaces | Typed scoring/retrieval components behind stable interfaces, JSON-schema agent output |
| Day 3: skills | `skills/` playbooks with procedural know-how kept out of prompts |
| Day 4: security and evaluation | Injection fixtures, policy gates, eval harness with regression gates |
| Day 5: production practice | Specs in version control, CI-gated evals, cost telemetry, Docker deploy |

## Production hardening (out of scope for the MVP)

Real crawler and candidate discovery, hosted embeddings behind the TF-IDF
interface, calibration curves per score band, reviewer override capture to
grow the label set, per-client threshold profiles, and observability beyond
cost telemetry.
