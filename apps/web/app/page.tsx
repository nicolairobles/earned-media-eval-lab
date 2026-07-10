"use client";

import { useEffect, useState } from "react";
import { ScoreBar } from "./components";

type ReleaseRow = {
  release_id: string;
  title: string;
  company: string;
  release_date: string;
  industry: string;
  earned_media_score: number;
  accepted_pickups: number;
  review_queue: number;
  duplicate_adjusted_pickup_count: number;
};

export default function Home() {
  const [rows, setRows] = useState<ReleaseRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/releases")
      .then((r) => {
        if (!r.ok) throw new Error(`API ${r.status}`);
        return r.json();
      })
      .then(setRows)
      .catch((e) => setError(String(e)));
  }, []);

  if (error)
    return (
      <main className="container">
        <p className="muted">
          Could not reach the API ({error}). Run the FastAPI server first.
        </p>
      </main>
    );

  const totals = rows?.reduce(
    (acc, r) => ({
      accepted: acc.accepted + r.duplicate_adjusted_pickup_count,
      review: acc.review + r.review_queue,
    }),
    { accepted: 0, review: 0 }
  );

  return (
    <main className="container">
      <h1>Release Queue</h1>
      <p className="subtitle">
        Synthetic press releases scored for earned-media pickup. Every score is
        gated by threshold policy before it can be shown to a client.
      </p>

      <div className="grid cols-3">
        <div className="card metric">
          <div className="label">Releases</div>
          <div className="value">{rows ? rows.length : "-"}</div>
        </div>
        <div className="card metric">
          <div className="label">Verified pickups (deduped)</div>
          <div className="value">{totals ? totals.accepted : "-"}</div>
        </div>
        <div className="card metric">
          <div className="label">Human review queue</div>
          <div className="value">{totals ? totals.review : "-"}</div>
        </div>
      </div>

      <h2>Releases</h2>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Release</th>
              <th>Industry</th>
              <th>Date</th>
              <th>Score</th>
              <th>Pickups</th>
              <th>Review</th>
            </tr>
          </thead>
          <tbody>
            {rows === null ? (
              <tr>
                <td colSpan={6} className="muted">
                  Loading...
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.release_id}>
                  <td>
                    <a href={`/release/?id=${r.release_id}`}>{r.title}</a>
                    <div className="muted small">{r.company}</div>
                  </td>
                  <td className="muted">{r.industry}</td>
                  <td className="muted">{r.release_date}</td>
                  <td>
                    <ScoreBar value={r.earned_media_score} />
                  </td>
                  <td>{r.duplicate_adjusted_pickup_count}</td>
                  <td>{r.review_queue}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

