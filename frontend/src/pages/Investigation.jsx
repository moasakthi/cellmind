import { Link, useParams } from "react-router-dom";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";

const STEPS = ["inspection", "process", "context", "rootCause"];
const LABELS = { inspection: "Inspection", process: "Process", context: "Context", rootCause: "Root Cause" };

function bandChip(band) {
  const cls = band === "HIGH" ? "chip-good" : band === "MEDIUM" ? "chip-warn" : band === "LOW" ? "chip-bad" : "chip-neutral";
  return <span className={`chip dot ${cls}`}>{band}</span>;
}

async function loadInvestigation(investigationId) {
  if (investigationId) return api.getInvestigation(investigationId);
  const { items } = await api.listInvestigations();
  if (!items.length) return null;
  return api.getInvestigation(items[0].investigationId);
}

export default function Investigation() {
  const { investigationId } = useParams();
  const { data: inv, loading, error } = useFetch(() => loadInvestigation(investigationId), [investigationId]);

  if (loading) return <p className="loading">Running Agent Hub pipeline…</p>;
  if (error) return <p className="error-box">Failed to load investigation: {error.message}</p>;
  if (!inv) {
    return (
      <p className="page-sub">
        No investigations yet — trigger one from a batch on the <Link to="/app">Dashboard</Link>.
      </p>
    );
  }

  const rootCause = inv.agents.rootCause;

  return (
    <>
      <h1 className="page-title">Investigation — Batch {inv.batchId}</h1>
      <p className="page-sub">
        Cell {inv.cellId} · status: {inv.status} ·{" "}
        <Link to={`/app/recommendation/${inv.investigationId}`}>View recommendation →</Link>
      </p>

      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Agent Pipeline</h3>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {STEPS.map((s) => (
            <span key={s} className="chip chip-good dot">{LABELS[s]} ✓</span>
          ))}
        </div>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 14 }}>
        <div className="card">
          <h3>Inspection</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <span className="chip chip-bad">DEFECT PROB. {Math.round(inv.agents.inspection.result.defectProbability * 100)}%</span>
            <span className="chip chip-warn">SEVERITY: {inv.agents.inspection.result.severity}</span>
            {bandChip(inv.agents.inspection.confidenceBand)}
          </div>
        </div>
        <div className="card">
          <h3>Evidence</h3>
          {rootCause.evidence.map((e, i) => (
            <div key={i} style={{ fontSize: 12.5, marginBottom: 8 }}>
              <span className="mono" style={{ color: "var(--ink-mute)" }}>{e.sourceType.toUpperCase()}</span>
              <div>{e.description}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Probable Contributing Factor</h3>
        <p style={{ margin: "0 0 10px", fontSize: 14 }}>
          <b>{rootCause.result.probableCause}</b> — presented as a probable factor, not a proven cause (BR-04).
        </p>
        <div style={{ maxWidth: 260 }}>
          <div className="mono" style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--ink-mute)", marginBottom: 4 }}>
            <span>Confidence</span><span>{Math.round(rootCause.confidence * 100)}%</span>
          </div>
          <div style={{ height: 7, borderRadius: 100, background: "var(--line-soft)", overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${rootCause.confidence * 100}%`, background: "var(--good)" }} />
          </div>
        </div>
      </div>
    </>
  );
}
