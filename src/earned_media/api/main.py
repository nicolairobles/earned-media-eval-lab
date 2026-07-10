from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..config import ROOT, scoring_policy, threshold_policy
from ..fixtures import label_map, load_articles, load_releases
from ..models import EarnedMediaReport
from ..pipeline import score_release

app = FastAPI(title="earned-media-eval-lab", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_report_cache: dict[str, EarnedMediaReport] = {}


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "agent_online": bool(os.environ.get("GEMINI_API_KEY")),
    }


@app.get("/api/releases")
def releases() -> list[dict]:
    out = []
    for r in load_releases():
        report = _get_report(r.release_id)
        out.append(
            {
                "release_id": r.release_id,
                "title": r.title,
                "company": r.company,
                "release_date": r.release_date,
                "industry": r.industry,
                "earned_media_score": report.earned_media_score,
                "accepted_pickups": report.accepted_pickups,
                "review_queue": report.review_queue,
                "duplicate_adjusted_pickup_count": report.duplicate_adjusted_pickup_count,
            }
        )
    return out


def _get_report(release_id: str) -> EarnedMediaReport:
    if release_id not in _report_cache:
        matches = [r for r in load_releases() if r.release_id == release_id]
        if not matches:
            raise HTTPException(status_code=404, detail="release not found")
        _report_cache[release_id] = score_release(matches[0], load_articles(release_id))
    return _report_cache[release_id]


@app.get("/api/releases/{release_id}/report")
def release_report(release_id: str) -> dict:
    report = _get_report(release_id)
    labels = label_map()
    data = report.model_dump()
    for pair in data["pairs"]:
        gold = labels.get((release_id, pair["article_id"]))
        pair["editorial_label"] = gold.label if gold else None
        pair["editorial_rationale"] = gold.rationale if gold else None
    matches = [r for r in load_releases() if r.release_id == release_id]
    data["release_body"] = matches[0].body if matches else ""
    return data


@app.get("/api/evals/latest")
def latest_eval() -> dict:
    path = ROOT / "evals" / "reports" / "latest.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="no eval report; run evals/run_evals.py")
    return json.loads(path.read_text())


@app.get("/api/policies")
def policies() -> dict:
    return {"scoring": scoring_policy(), "thresholds": threshold_policy()}


static_dir = Path(os.environ.get("STATIC_DIR", ROOT / "apps" / "web" / "out"))
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

    @app.exception_handler(404)
    async def spa_fallback(request, exc):
        if not request.url.path.startswith("/api/"):
            index = static_dir / "index.html"
            if index.exists():
                return FileResponse(index, status_code=200)
        from fastapi.responses import JSONResponse

        return JSONResponse({"detail": "Not Found"}, status_code=404)
