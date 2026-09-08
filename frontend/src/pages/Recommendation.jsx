import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";
import { useAuth } from "../auth/AuthContext.jsx";

async function loadRecommendation(investigationId) {
  let invId = investigationId;
  if (!invId) {
    const { items } = await api.listInvestigations();
    if (!items.length) return null;
    invId = items[0].investigationId;
  }
  const inv = await api.getInvestigation(invId);
  let rec;
  try {
    rec = await api.getRecommendation(invId);
  } catch (e) {
    if (e.status !== 404) throw e;
    // No recommendation yet — generate one via Azure OpenAI on the spot.
    // A 503 here (AI unavailable) is intentionally left to propagate.
    rec = await api.generateRecommendation(invId);
  }
  return { ...rec, batchId: inv.batchId };
}

const SIM_PARAMETERS = [
  { value: "temperature", label: "Firing Temperature" },
  { value: "gasFlow", label: "Gas Flow" },
  { value: "pressure", label: "Pressure" },
];

export default function Recommendation() {
  const { investigationId } = useParams();
  const { user, has } = useAuth();
  const { data: rec, loading, error, reload } = useFetch(() => loadRecommendation(investigationId), [investigationId]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [simParam, setSimParam] = useState("temperature");
  const [simDirection, setSimDirection] = useState("reduce");
  const [sim, setSim] = useState(null);
  const [simBusy, setSimBusy] = useState(false);
  const [regenBusy, setRegenBusy] = useState(false);
  const [regenMsg, setRegenMsg] = useState(null);
  const canApprove = has("approve_quality_action") || has("approve_process_action") || has("approve_equipment_action");

  if (loading) return <p className="loading">Loading recommendation… (generating via AI if none exists yet — this can take a few seconds)</p>;
  if (error) {
    if (error.status === 503) {
      return <div className="alert alert-warn" style={{ marginTop: 20 }}>AI recommendation engine unavailable right now — try again shortly. ({error.message})</div>;
    }
    return <p className="error-box">Failed to load recommendation: {error.message}</p>;
  }
  if (!rec) {
    return (
      <p className="page-sub">
        No recommendation has been generated for this investigation yet
        {investigationId && <> — see the <Link to={`/app/investigation/${investigationId}`}>investigation</Link> for details</>}.
      </p>
    );
  }

  async function runSimulation() {
    setSimBusy(true);
    try {
      const result = await api.runSimulation({
        batchId: rec.batchId,
        parameter: simParam,
        adjustment: `${simDirection} ${simParam}`,
      });
      setSim(result);
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setSimBusy(false);
    }
  }

  async function approve(decision) {
    setBusy(true);
    setMsg(null);
    try {
      await api.approveRecommendation(rec.recommendationId, { actingUserId: user.userId, decision });
      setMsg({ ok: true, text: `Recorded: ${decision}.` });
      reload();
    } catch (e) {
      setMsg({ ok: false, text: e.message });
    } finally {
      setBusy(false);
    }
  }

  async function regenerate() {
    setRegenBusy(true);
    setRegenMsg(null);
    try {
      await api.generateRecommendation(rec.investigationId);
      setRegenMsg({ ok: true, text: "Recommendation regenerated." });
      reload();
    } catch (e) {
      setRegenMsg({ ok: false, text: e.status === 503 ? "AI recommendation engine unavailable — try again shortly." : e.message });
    } finally {
      setRegenBusy(false);
    }
  }

  return (
    <>
      <h1 className="page-title">Recommendation &amp; Approval</h1>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
        <span className="chip chip-info">AUTONOMY: LEVEL {rec.autonomyLevel} — AUTO-SUGGEST</span>
        {rec.authoredBy === "system:AIRecommendationAgent" && <span className="chip chip-neutral">AI-GENERATED</span>}
        <button className="btn btn-secondary" disabled={regenBusy} onClick={regenerate} style={{ marginLeft: "auto" }}>
          {regenBusy ? "Regenerating…" : "Regenerate with AI"}
        </button>
      </div>

      {regenMsg && (
        <div className={`alert ${regenMsg.ok ? "alert-info" : "alert-bad"}`} style={{ marginBottom: 16 }}>
          {regenMsg.text}
        </div>
      )}

      {rec.reasoning && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3>AI Reasoning</h3>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: "var(--ink-soft)" }}>{rec.reasoning}</p>
        </div>
      )}

      <div className="grid cols-3" style={{ marginBottom: 16 }}>
        {rec.rankedActions.map((a) => (
          <div key={a.actionId} className={`action-card ${a.preSelected ? "selected" : ""}`}>
            <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)" }}>
              RANK {a.rank}{a.preSelected ? " · PRE-SELECTED" : ""}
            </div>
            <h4 style={{ fontSize: 13.5, margin: "4px 0 0" }}>{a.title}</h4>
            <div className="metrics">
              <div>Cost<br /><b>{a.cost}</b></div>
              <div>Impact<br /><b>+{a.expectedImprovementPct}%</b></div>
              <div>Downtime<br /><b>{a.downtimeHours || "None"}</b></div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>What-If Simulation</h3>
          <div style={{ display: "flex", gap: 20, marginBottom: 12 }}>
            <div>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)" }}>CURRENT</div>
              <div className="mono tabular" style={{ fontSize: 20 }}>{(sim ?? rec.simulation).currentDefectRatePct}%</div>
            </div>
            <div>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)" }}>PREDICTED</div>
              <div className="mono tabular" style={{ fontSize: 20, color: "var(--good-ink)" }}>{(sim ?? rec.simulation).predictedDefectRatePct}%</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <select value={simDirection} onChange={(e) => setSimDirection(e.target.value)}>
              <option value="reduce">Reduce</option>
              <option value="increase">Increase</option>
            </select>
            <select value={simParam} onChange={(e) => setSimParam(e.target.value)}>
              {SIM_PARAMETERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
            <button className="btn btn-secondary" disabled={simBusy} onClick={runSimulation}>
              {simBusy ? "Running…" : "Run simulation"}
            </button>
          </div>
          <p style={{ fontSize: 11.5, color: "var(--ink-mute)", marginTop: 8 }}>{(sim ?? rec.simulation).disclaimer}</p>
        </div>

        <div className="card">
          <h3>Approval</h3>
          {rec.approval ? (
            <div className="alert alert-info">
              Decision recorded: <b>{rec.approval.decision}</b> by <span className="mono">{rec.approval.approver}</span>
            </div>
          ) : (
            <>
              <p style={{ fontSize: 12.5, margin: "0 0 10px" }}>
                Authored by <span className="mono">{rec.authoredBy}</span>. Signed in as <b className="mono">{user?.name}</b> ({user?.role?.roleName}).
              </p>
              {!canApprove && <div className="alert alert-warn">Your role cannot approve recommendations — buttons disabled (RBAC).</div>}
              {msg && <div className={`alert ${msg.ok ? "alert-info" : "alert-bad"}`}>{msg.text}</div>}
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-secondary" disabled={busy || !canApprove} onClick={() => approve("rejected")}>Reject</button>
                <button className="btn btn-primary" disabled={busy || !canApprove} onClick={() => approve("approved")}>Approve action</button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
