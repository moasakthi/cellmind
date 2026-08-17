import { useState } from "react";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";
import { useAuth } from "../auth/AuthContext.jsx";

function statusChip(status) {
  const cls = status === "PROMOTED" ? "chip-good" : status === "REJECTED" ? "chip-bad" : "chip-warn";
  return <span className={`chip ${cls}`}>{status.replace("_", " ")}</span>;
}

export default function Retraining() {
  const { user } = useAuth();
  const { data: runs, loading, error, reload } = useFetch(() => api.listRuns(), []);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(null);

  if (loading) return <p className="loading">Loading retraining runs…</p>;
  if (error) return <p className="error-box">Failed to load runs: {error.message}</p>;

  const pending = runs.find((r) => r.status === "PENDING_APPROVAL");

  async function tryApprove(actingUserId) {
    setBusy(actingUserId);
    setMsg(null);
    try {
      await api.approveRun(pending.runId, { actingUserId, decision: "approved" });
      setMsg({ ok: true, text: `Approved by ${actingUserId}.` });
      reload();
    } catch (e) {
      setMsg({ ok: false, text: `${e.status}: ${e.message}` });
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <h1 className="page-title">Retraining Console</h1>
      <p className="page-sub">FR-19 — this "Approve as requester" button is wired to the real backend check for BR-10.</p>

      <div className="grid cols-2">
        <div className="card">
          <h3>Retraining Runs</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Run</th><th>Model</th><th>Trigger</th><th>Holdout</th><th>Status</th></tr></thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.runId} className={r.status === "PENDING_APPROVAL" ? "hi" : ""}>
                    <td className="mono">{r.runId}</td>
                    <td className="mono">{r.modelName}</td>
                    <td>{r.triggerType}</td>
                    <td className="mono tabular">{r.holdoutResult ?? "—"}</td>
                    <td>{statusChip(r.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {pending && (
          <div className="card">
            <h3>Approve {pending.runId}</h3>
            <p style={{ fontSize: 12.5, margin: "0 0 10px" }}>
              Requested by <b className="mono">{pending.requestedBy}</b> (Quality Engineer).
            </p>
            {msg && <div className={`alert ${msg.ok ? "alert-info" : "alert-bad"}`}>{msg.text}</div>}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn btn-danger" disabled={busy} onClick={() => tryApprove(pending.requestedBy)}>
                Approve as requester (should fail)
              </button>
              <button className="btn btn-primary" disabled={busy} onClick={() => tryApprove(user.userId)}>
                Approve as {user?.name} ({user?.role?.roleName})
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
