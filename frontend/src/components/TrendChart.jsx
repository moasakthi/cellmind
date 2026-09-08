import { useRef, useState } from "react";

const WIDTH = 640;
const HEIGHT = 220;
const PAD = { top: 16, right: 46, bottom: 30, left: 32 };

function niceTicks(min, max, count = 4) {
  const step = (max - min || 1) / count;
  return Array.from({ length: count + 1 }, (_, i) => min + step * i);
}

/**
 * Two-series line chart on one shared axis (both series must share a unit).
 * series: [{ key, label, color, points: number[] }]
 */
export default function TrendChart({ series, xLabels, unit = "%" }) {
  const [hover, setHover] = useState(null);
  const svgRef = useRef(null);

  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = HEIGHT - PAD.top - PAD.bottom;
  const n = xLabels.length;

  const allValues = series.flatMap((s) => s.points);
  const rawMin = Math.min(...allValues);
  const rawMax = Math.max(...allValues);
  const span = rawMax - rawMin || 1;
  const min = Math.max(0, rawMin - span * 0.15);
  const max = unit === "%" ? Math.min(100, rawMax + span * 0.15) : rawMax + span * 0.15;
  const ticks = niceTicks(min, max, 4);

  const x = (i) => PAD.left + (n <= 1 ? innerW / 2 : (i / (n - 1)) * innerW);
  const y = (v) => PAD.top + innerH - ((v - min) / (max - min || 1)) * innerH;

  function handleMove(e) {
    const rect = svgRef.current.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * WIDTH;
    const rel = (px - PAD.left) / innerW;
    const idx = Math.min(n - 1, Math.max(0, Math.round(rel * (n - 1))));
    setHover(idx);
  }

  return (
    <div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        width="100%"
        height={HEIGHT}
        onMouseMove={handleMove}
        onMouseLeave={() => setHover(null)}
        style={{ overflow: "visible", cursor: "crosshair" }}
      >
        {ticks.map((t, i) => (
          <g key={i}>
            <line x1={PAD.left} x2={WIDTH - PAD.right} y1={y(t)} y2={y(t)} stroke="var(--line)" strokeWidth="1" />
            <text x={PAD.left - 8} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize="9.5" fill="var(--ink-mute)" fontFamily="var(--font-mono)">
              {Math.round(t)}{unit}
            </text>
          </g>
        ))}

        {xLabels.map((lbl, i) => (
          <text key={i} x={x(i)} y={HEIGHT - PAD.bottom + 18} textAnchor="middle" fontSize="9" fill="var(--ink-mute)" fontFamily="var(--font-mono)">
            {lbl}
          </text>
        ))}

        {hover != null && (
          <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={HEIGHT - PAD.bottom} stroke="var(--ink-mute)" strokeWidth="1" strokeDasharray="2,3" />
        )}

        {series.map((s) => {
          const d = s.points.map((v, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(v)}`).join(" ");
          const lastIdx = s.points.length - 1;
          return (
            <g key={s.key}>
              <path d={d} fill="none" stroke={s.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              {s.points.map((v, i) =>
                (i === lastIdx || hover === i) ? (
                  <circle
                    key={i} cx={x(i)} cy={y(v)} r={hover === i ? 4.5 : 4}
                    fill={s.color} stroke="var(--paper-raised)" strokeWidth="2"
                  />
                ) : null
              )}
              <text x={x(lastIdx) + 8} y={y(s.points[lastIdx])} dominantBaseline="middle" fontSize="11" fontWeight="700" fill={s.color}>
                {s.points[lastIdx]}{unit}
              </text>
            </g>
          );
        })}
      </svg>

      <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 6, flexWrap: "wrap" }}>
        {series.map((s) => (
          <span key={s.key} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 11.5, color: "var(--ink-soft)" }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: s.color, display: "inline-block" }} />
            {s.label}
          </span>
        ))}
        {hover != null && (
          <span className="mono" style={{ marginLeft: "auto", fontSize: 11, color: "var(--ink-mute)" }}>
            {xLabels[hover]}: {series.map((s) => `${s.label} ${s.points[hover]}${unit}`).join(" · ")}
          </span>
        )}
      </div>
    </div>
  );
}
