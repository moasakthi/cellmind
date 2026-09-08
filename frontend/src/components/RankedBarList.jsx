/**
 * Emphasis-form ranked bar list: the top item carries the accent color,
 * the rest are de-emphasized gray. items: [{ key, label, value, sublabel }]
 */
export default function RankedBarList({ items, unit = "%", accent = "var(--furnace)" }) {
  const sorted = [...items].sort((a, b) => b.value - a.value);
  const max = Math.max(...sorted.map((i) => i.value), 1);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {sorted.map((it, i) => {
        const pct = (it.value / max) * 100;
        const isTop = i === 0;
        return (
          <div
            key={it.key}
            title={it.sublabel}
            style={{ display: "grid", gridTemplateColumns: "56px 1fr 52px", alignItems: "center", gap: 10 }}
          >
            <span className="mono" style={{ fontSize: 11.5, color: isTop ? "var(--ink)" : "var(--ink-soft)", fontWeight: isTop ? 700 : 500 }}>
              {it.label}
            </span>
            <div style={{ height: 14, borderRadius: 7, background: "var(--line-soft)", overflow: "hidden" }}>
              <div
                style={{
                  width: `${pct}%`, height: "100%", borderRadius: 7,
                  background: isTop ? accent : "var(--ink-mute)",
                  opacity: isTop ? 1 : 0.35,
                  transition: "width 240ms",
                }}
              />
            </div>
            <span
              className="mono tabular"
              style={{ fontSize: 11.5, textAlign: "right", color: isTop ? "var(--ink)" : "var(--ink-mute)", fontWeight: isTop ? 700 : 500 }}
            >
              {it.value}{unit}
            </span>
          </div>
        );
      })}
    </div>
  );
}
