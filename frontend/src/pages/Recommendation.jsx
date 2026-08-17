import { useState } from "react";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Recommendation() {
  const { user, has } = useAuth();
  const { data: rec, loading, error, reload } = useFetch(() => api.getRecommendation("inv-1"), []);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const canApprove = has("approve_quality_action") || has("approve_process_action") || has("approve_equipment_action");

  if (loading) return <p className="loading">Loading recommendation…</p>;
  if (error) return <p className="error-box">Failed to load recommendation: {error.message}</p>;

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

  return (
    <>
      <h1 className="page-title">Recommendation &amp; Approval</h1>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16 }}>
        <span className="chip chip-info">AUTONOMY: LEVEL {rec.autonomyLevel} — AUTO-SUGGEST</span>
      </div>

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
          <div style={{ display: "flex", gap: 20 }}>
            <div>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)" }}>CURRENT</div>
              <div className="mono tabular" style={{ fontSize: 20 }}>{rec.simulation.currentDefectRatePct}%</div>
            </div>
            <div>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)" }}>PREDICTED</div>
              <div className="mono tabular" style={{ fontSize: 20, color: "var(--good-ink)" }}>{rec.simulation.predictedDefectRatePct}%</div>
            </div>
          </div>
          <p style={{ fontSize: 11.5, color: "var(--ink-mute)", marginTop: 8 }}>{rec.simulation.disclaimer}</p>
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
