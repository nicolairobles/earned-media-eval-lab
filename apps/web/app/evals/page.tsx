"use client";

import { useEffect, useState } from "react";

type EvalReport = {
  generated_at: string;
  scoring_version: string;
  mode: string;
  agent_reviews: Record<string, number>;
  metrics: Record<string, number>;
  gates: Record<string, boolean>;
  gates_passed: boolean;
  cost: Record<string, number>;
  per_release: {
    release_id: string;
    earned_media_score: number;
    accepted: number;
    review_queue: number;
    rejected: number;
    suppressed: number;
  }[];
};

const METRIC_LABELS: Record<string, string> = {
  precision: "Precision (client-facing)",
  recall_strict: "Recall (auto-accept only)",
  recall_with_review: "Recall (accept + review queue)",
  f1_strict: "F1 (strict)",
  precision_at_3: "Precision@3",
  review_queue_per_release: "Review queue per release",
};

export default function EvalsPage() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch("/api/evals/latest")
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(setReport)
      .catch(() => setError(true));
  }, []);

  if (error)
    return (
      <main className="container">
        <p className="muted">
          No eval report found. Run <code>python evals/run_evals.py</code>.
        </p>
      </main>
    );
  if (!report)
    return (
      <main className="container">
        <p className="muted">Loading...</p>
      </main>
    );

  const m = report.metrics;

  return (
    <main className="container">
      <h1>Eval Report</h1>
      <p className="subtitle">
        {report.scoring_version} &middot; {report.mode} mode &middot; generated{" "}
        {report.generated_at.slice(0, 19)} &middot; gates{" "}
        <span className={`badge ${report.gates_passed ? "pass" : "fail"}`}>
          {report.gates_passed ? "PASS" : "FAIL"}
        </span>
      </p>

      <div className="grid cols-4">
        {["precision", "recall_strict", "recall_with_review", "precision_at_3"].map(
          (k) => (
            <div className="card metric" key={k}>
              <div className="label">{METRIC_LABELS[k]}</div>
              <div className="value">{(m[k] * 100).toFixed(1)}%</div>
            </div>
          )
        )}
      </div>

      <h2>Safety gates</h2>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Gate</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(report.gates).map(([k, v]) => (
              <tr key={k}>
                <td>{k.replaceAll("_", " ")}</td>
                <td>
                  <span className={`badge ${v ? "pass" : "fail"}`}>
                    {v ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Cost model (at {report.cost.monthly_release_volume} releases/month)</h2>
      <div className="grid cols-3">
        <div className="card metric">
          <div className="label">Total per release</div>
          <div className="value">${report.cost.total_usd_per_release}</div>
        </div>
        <div className="card metric">
          <div className="label">LLM monthly</div>
          <div className="value">${report.cost.llm_usd_monthly}</div>
        </div>
        <div className="card metric">
          <div className="label">Total monthly</div>
          <div className="value">${report.cost.total_usd_monthly}</div>
        </div>
      </div>

      <h2>Per release</h2>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Release</th>
              <th>Score</th>
              <th>Accepted</th>
              <th>Review</th>
              <th>Rejected</th>
              <th>Suppressed</th>
            </tr>
          </thead>
          <tbody>
            {report.per_release.map((r) => (
              <tr key={r.release_id}>
                <td>
                  <a href={`/release/?id=${r.release_id}`}>{r.release_id}</a>
                </td>
                <td>{r.earned_media_score.toFixed(2)}</td>
                <td>{r.accepted}</td>
                <td>{r.review_queue}</td>
                <td>{r.rejected}</td>
                <td>{r.suppressed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="muted small mt">
        Agent reviews this run: {JSON.stringify(report.agent_reviews)}. Offline
        mode uses a deterministic heuristic so CI stays free and reproducible.
      </p>
    </main>
  );
}
