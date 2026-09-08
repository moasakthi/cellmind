/**
 * Part-to-whole horizontal bar. segments: [{ key, label, value, color }]
 * Inline value label shown when a segment is wide enough to hold it;
 * every segment is always named in the legend row below (never color-alone).
 */
export default function StatusBar({ segments }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;

  return (
    <div>
      <div style={{ display: "flex", height: 26, borderRadius: 8, overflow: "hidden", gap: 2, background: "var(--line-soft)" }}>
        {segments.map((s) => {
          const pct = (s.value / total) * 100;
          if (pct <= 0) return null;
          return (
            <div
              key={s.key}
              title={`${s.label}: ${s.value} (${pct.toFixed(0)}%)`}
              style={{
                width: `${pct}%`, background: s.color,
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "width 240ms",
              }}
            >
              {pct >= 14 && (
                <span style={{ fontSize: 10.5, fontWeight: 700, color: "#fff", whiteSpace: "nowrap" }}>{s.value}</span>
              )}
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 14, marginTop: 10, flexWrap: "wrap" }}>
        {segments.map((s) => {
          const pct = (s.value / total) * 100;
          return (
            <span key={s.key} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11.5, color: "var(--ink-soft)" }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: s.color, display: "inline-block" }} />
              {s.label}{" "}
              <b className="mono" style={{ color: "var(--ink)" }}>{s.value}</b>
              <span style={{ color: "var(--ink-mute)" }}>({pct.toFixed(0)}%)</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
