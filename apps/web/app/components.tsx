"use client";

export function ScoreBar({ value }: { value: number }) {
  const color =
    value >= 0.65 ? "var(--green)" : value >= 0.4 ? "var(--yellow)" : "var(--muted)";
  return (
    <div className="scorebar">
      <div className="track">
        <div
          className="fill"
          style={{ width: `${Math.round(value * 100)}%`, background: color }}
        />
      </div>
      <span className="small">{value.toFixed(2)}</span>
    </div>
  );
}

export function RouteBadge({ route }: { route: string }) {
  const label = route.replace("_", " ");
  return <span className={`badge ${route}`}>{label}</span>;
}
