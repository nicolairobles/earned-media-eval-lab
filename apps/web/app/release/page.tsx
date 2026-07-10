"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { RouteBadge, ScoreBar } from "../components";

type Evidence = { snippet: string; reason: string };
type Breakdown = {
  similarity_score: number;
  entity_match_score: number;
  novelty_score: number;
  source_quality_score: number;
  timeliness_score: number;
  evidence_score: number;
};
type AgentReview = {
  label: string;
  confidence: string;
  rationale: string;
  overclaim_risk: boolean;
  reviewer: string;
};
type Pair = {
  article_id: string;
  url: string;
  title: string;
  outlet: string;
  publish_date: string | null;
  breakdown: Breakdown;
  earned_media_score: number;
  predicted_label: string;
  confidence_band: string;
  route: string;
  duplicate_of: string | null;
  evidence: Evidence[];
  agent_review: AgentReview | null;
  policy_flags: string[];
  editorial_label: string | null;
  editorial_rationale: string | null;
};
type Report = {
  release_id: string;
  release_title: string;
  release_body: string;
  company: string;
  release_date: string;
  pairs: Pair[];
  earned_media_score: number;
  duplicate_adjusted_pickup_count: number;
  cost: { llm_calls: number; estimated_usd: number };
  scoring_version: string;
};

function simulateRoute(p: Pair, floor: number): string {
  if (p.route === "suppress") return "suppress";
  if (
    p.earned_media_score >= floor &&
    p.breakdown.entity_match_score >= 0.6 &&
    p.breakdown.evidence_score >= 0.5 &&
    !p.duplicate_of &&
    p.policy_flags.length === 0
  )
    return "auto_accept";
  if (p.earned_media_score >= 0.4) return "needs_review";
  return "reject";
}

function ReleaseDetail() {
  const params = useSearchParams();
  const id = params.get("id") ?? "rel-001";
  const [report, setReport] = useState<Report | null>(null);
  const [floor, setFloor] = useState(0.65);
  const [showBody, setShowBody] = useState(false);

  useEffect(() => {
    fetch(`/api/releases/${id}/report`)
      .then((r) => r.json())
      .then(setReport)
      .catch(() => setReport(null));
  }, [id]);

  const simulated = useMemo(() => {
    if (!report) return null;
    const counts = { auto_accept: 0, needs_review: 0, reject: 0, suppress: 0 };
    for (const p of report.pairs) {
      counts[simulateRoute(p, floor) as keyof typeof counts]++;
    }
    return counts;
  }, [report, floor]);

  if (!report)
    return (
      <main className="container">
        <p className="muted">Loading report for {id}...</p>
      </main>
    );

  return (
    <main className="container">
      <p className="small">
        <a href="/">&larr; All releases</a>
      </p>
      <h1>{report.release_title}</h1>
      <p className="subtitle">
        {report.company} &middot; {report.release_date} &middot; scoring{" "}
        {report.scoring_version} &middot;{" "}
        <a onClick={() => setShowBody(!showBody)} style={{ cursor: "pointer" }}>
          {showBody ? "hide" : "show"} release text
        </a>
      </p>
      {showBody && <div className="card small mt">{report.release_body}</div>}

      <div className="grid cols-4 mt">
        <div className="card metric">
          <div className="label">Earned media score</div>
          <div className="value">{report.earned_media_score.toFixed(2)}</div>
        </div>
        <div className="card metric">
          <div className="label">Verified pickups</div>
          <div className="value">{report.duplicate_adjusted_pickup_count}</div>
        </div>
        <div className="card metric">
          <div className="label">Candidates scored</div>
          <div className="value">{report.pairs.length}</div>
        </div>
        <div className="card metric">
          <div className="label">LLM cost (this run)</div>
          <div className="value">${report.cost.estimated_usd.toFixed(4)}</div>
        </div>
      </div>

      <h2>Threshold simulator</h2>
      <div className="card">
        <div className="muted small">
          Drag the auto-accept floor to see the quality/volume tradeoff. Entity,
          evidence, duplicate, and suppression guards always apply.
        </div>
        <div className="slider-row">
          <input
            type="range"
            min={0.4}
            max={0.9}
            step={0.01}
            value={floor}
            onChange={(e) => setFloor(parseFloat(e.target.value))}
          />
          <span className="val">{floor.toFixed(2)}</span>
        </div>
        {simulated && (
          <div className="breakdown">
            <span>auto accept: {simulated.auto_accept}</span>
            <span>needs review: {simulated.needs_review}</span>
            <span>reject: {simulated.reject}</span>
            <span>suppress: {simulated.suppress}</span>
          </div>
        )}
      </div>

      <h2>Candidate articles</h2>
      {report.pairs.map((p) => (
        <div className="card mt" key={p.article_id}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <strong>{p.title}</strong>
              <div className="muted small">
                {p.outlet} &middot; {p.publish_date ?? "no date"} &middot;{" "}
                <a href={p.url} target="_blank" rel="noreferrer">
                  {p.url.replace("https://", "").slice(0, 48)}
                </a>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
              {p.duplicate_of && <span className="badge dup">duplicate</span>}
              <RouteBadge route={p.route} />
            </div>
          </div>

          <div className="mt">
            <ScoreBar value={p.earned_media_score} />
          </div>
          <div className="breakdown">
            <span>similarity {p.breakdown.similarity_score.toFixed(2)}</span>
            <span>entity {p.breakdown.entity_match_score.toFixed(2)}</span>
            <span>source {p.breakdown.source_quality_score.toFixed(2)}</span>
            <span>timeliness {p.breakdown.timeliness_score.toFixed(2)}</span>
            <span>evidence {p.breakdown.evidence_score.toFixed(2)}</span>
            <span>confidence {p.confidence_band}</span>
            {p.editorial_label && (
              <span className="badge gold">gold: {p.editorial_label}</span>
            )}
          </div>

          {p.evidence.map((e, i) => (
            <div className="evidence" key={i}>
              &ldquo;{e.snippet}&rdquo;
              <div className="reason">{e.reason}</div>
            </div>
          ))}

          {p.agent_review && (
            <div className="agentbox">
              <span className="who">
                {p.agent_review.reviewer === "gemini"
                  ? "Gemini borderline reviewer"
                  : "Heuristic reviewer (offline fallback)"}
              </span>{" "}
              &rarr; {p.agent_review.label} ({p.agent_review.confidence}{" "}
              confidence)
              <div className="muted small">{p.agent_review.rationale}</div>
            </div>
          )}

          {p.policy_flags.length > 0 && (
            <div className="mt small" style={{ color: "var(--red)" }}>
              policy flags: {p.policy_flags.join(", ")}
            </div>
          )}
        </div>
      ))}
    </main>
  );
}

export default function ReleasePage() {
  return (
    <Suspense fallback={<main className="container">Loading...</main>}>
      <ReleaseDetail />
    </Suspense>
  );
}
