import { useState } from "react";
import { PALETTES, useTheme } from "../theme/ThemeContext.jsx";

const SWATCH = {
  nova: "linear-gradient(135deg,#8B7CFF,#4F8CFF)",
  teal: "#0E8F85", amber: "#8A6D12", indigo: "#3B4FBF", mono: "#33383D",
};

export default function ThemeSwitcher() {
  const { mode, toggleMode, palette, setPalette } = useTheme();
  const [open, setOpen] = useState(false);

  return (
    <div className="theme-menu">
      <button className="theme-toggle" onClick={() => setOpen((o) => !o)} title="Theme & palette">
        ◐ {mode === "system" ? "auto" : mode}
      </button>
      {open && (
        <div className="theme-menu-panel" onMouseLeave={() => setOpen(false)}>
          <button onClick={toggleMode}>Mode: {mode} (click to cycle)</button>
          <div style={{ height: 1, background: "var(--line-soft)", margin: "6px 0" }} />
          {PALETTES.map((p) => (
            <button key={p.id} onClick={() => setPalette(p.id)}>
              <span className="swatch-dot" style={{ background: SWATCH[p.id] }} />
              {p.label} {palette === p.id ? "✓" : ""}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
