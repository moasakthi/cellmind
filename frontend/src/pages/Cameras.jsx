import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";

function healthChip(status) {
  const cls = status === "ONLINE" ? "chip-good" : status === "DEGRADED" ? "chip-warn" : "chip-bad";
  return <span className={`chip dot ${cls}`}>{status}</span>;
}

export default function Cameras() {
  const { data: cameras, loading, error } = useFetch(() => api.listCameras(), []);

  if (loading) return <p className="loading">Loading cameras…</p>;
  if (error) return <p className="error-box">Failed to load cameras: {error.message}</p>;

  return (
    <>
      <h1 className="page-title">Camera Administration</h1>
      <p className="page-sub">FR-18 — registered EL/visual capture sources.</p>

      <div className="card">
        <h3>Registered Cameras</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Camera</th><th>Type</th><th>EL-Capable</th><th>Station</th><th>Health</th><th>Last Frame</th></tr>
            </thead>
            <tbody>
              {cameras.map((c) => (
                <tr key={c.cameraId} className={c.status !== "ONLINE" ? "hi" : ""}>
                  <td className="mono">{c.cameraId}</td>
                  <td>{c.cameraType}</td>
                  <td>{c.elCapable ? "✓" : "—"}</td>
                  <td>{c.lineId} / {c.stationId}</td>
                  <td>{healthChip(c.status)}</td>
                  <td className="mono">{new Date(c.lastFrameAt).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
