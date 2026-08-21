// Procedural SVG art — no external image assets, no licensing risk, on-brand.

export function SolarPanelGrid({ width = 220, height = 140, className }) {
  const cols = 6, rows = 4;
  const cells = [];
  const cw = width / cols, ch = height / rows;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      cells.push(
        <rect
          key={`${r}-${c}`}
          x={c * cw + 1}
          y={r * ch + 1}
          width={cw - 2}
          height={ch - 2}
          rx="2"
          fill="var(--accent-soft)"
          stroke="var(--accent)"
          strokeOpacity="0.5"
        />
      );
    }
  }
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className} role="img" aria-label="Solar panel cell grid">
      <rect x="0" y="0" width={width} height={height} rx="8" fill="var(--paper-raised)" stroke="var(--line)" />
      {cells}
    </svg>
  );
}

// Stylized EL (electroluminescence) scan: glowing cell grid with an optional defect patch.
export function ELScan({ width = 240, height = 240, severity = "LOW", className }) {
  const cols = 8, rows = 8;
  const cw = width / cols, ch = height / rows;
  const glow = severity === "HIGH" ? 0.9 : severity === "MEDIUM" ? 0.65 : 0.4;
  const defectCells =
    severity === "HIGH"
      ? [[3, 3], [3, 4], [4, 3], [4, 4], [5, 4]]
      : severity === "MEDIUM"
      ? [[5, 2], [5, 3]]
      : [];
  const cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const isDefect = defectCells.some(([dr, dc]) => dr === r && dc === c);
      const pseudoRandom = ((r * 7 + c * 13) % 10) / 10; // deterministic, avoids re-render flicker
      cells.push(
        <rect
          key={`${r}-${c}`}
          x={c * cw + 1}
          y={r * ch + 1}
          width={cw - 2}
          height={ch - 2}
          fill={isDefect ? "var(--danger)" : "var(--accent)"}
          opacity={isDefect ? 0.85 : glow * (0.5 + 0.5 * pseudoRandom)}
        />
      );
    }
  }
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className} role="img" aria-label={`EL scan, ${severity.toLowerCase()} severity`}>
      <defs>
        <radialGradient id="elbg" cx="50%" cy="50%" r="75%">
          <stop offset="0%" stopColor="var(--accent-soft)" stopOpacity="0.4" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
      </defs>
      <rect x="0" y="0" width={width} height={height} rx="6" fill="var(--ink)" />
      <rect x="0" y="0" width={width} height={height} rx="6" fill="url(#elbg)" />
      {cells}
    </svg>
  );
}
