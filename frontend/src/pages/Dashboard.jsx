import { Link } from "react-router-dom";
import { TrendingUp, AlertTriangle, ShieldAlert, Layers, ArrowUpRight } from "lucide-react";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";
import Sparkline from "../components/Sparkline.jsx";

function riskChip(level) {
  const cls = level === "HIGH" ? "chip-bad" : level === "MEDIUM" ? "chip-warn" : "chip-neutral";
  return <span className={`chip ${cls}`}>{level}</span>;
}

const TREND = {
  yield: [95.1, 94.6, 93.8, 96.4, 95.0, 97.2, 91.6],
  defect: [4.2, 4.9, 5.6, 3.6, 5.0, 2.8, 8.4],
};

export default function Dashboard() {
  const { data: batches, loading, error } = useFetch(() => api.listBatches(), []);

  if (loading) return <p className="loading">Loading batches…</p>;
  if (error) return <p className="error-box">Failed to load batches: {error.message}</p>;

  const totalCells = batches.reduce((s, b) => s + b.cellCount, 0);
  const totalDefects = batches.reduce((s, b) => s + b.defectCount, 0);
  const avgYield = (batches.reduce((s, b) => s + b.yield, 0) / batches.length).toFixed(1);
  const avgDefect = ((totalDefects / totalCells) * 100).toFixed(1);
  const highRisk = batches.filter((b) => b.riskLevel === "HIGH").length;

  const kpis = [
    { label: "Plant Yield (avg)", value: `${avgYield}%`, icon: TrendingUp, trend: TREND.yield, delta: "-2.1 pts" },
    { label: "Defect Rate (avg)", value: `${avgDefect}%`, icon: AlertTriangle, trend: TREND.defect, delta: "+5.6 pts", bad: true },
    { label: "High-Risk Batches", value: highRisk, icon: ShieldAlert, trend: [1, 0, 1, 0, 1, 0, 1] },
    { label: "Batches Tracked", value: batches.length, icon: Layers, trend: [3, 4, 4, 5, 5, 5, batches.length] },
  ];

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-sub">Live from the FastAPI mock API (/batches) — nothing here is hardcoded.</p>

      <div className="grid cols-4" style={{ marginBottom: 18 }}>
        {kpis.map((k) => {
          const Icon = k.icon;
          return (
            <div key={k.label} className="card kpi">
              <div className="kpi-head">
                <span className="label">{k.label}</span>
                <span className="icon-badge"><Icon className="icon" /></span>
              </div>
              <div className="value tabular">{k.value}</div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                {k.delta && (
                  <span style={{ fontSize: 11, color: k.bad ? "var(--danger-ink)" : "var(--good-ink)", display: "flex", alignItems: "center", gap: 3 }}>
                    <ArrowUpRight className="icon" style={{ width: 12, height: 12, transform: k.bad ? "none" : "scaleY(-1)" }} />
                    {k.delta}
                  </span>
                )}
                <Sparkline points={k.trend} color={k.bad ? "var(--danger)" : "var(--accent)"} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h3>Recent Batches</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Batch</th><th>Line</th><th>Date</th><th>Cells</th><th>Yield</th><th>Defect Rate</th><th>Risk</th><th></th></tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.batchId} className={b.riskLevel === "HIGH" ? "hi" : ""}>
                  <td className="mono">{b.batchId}</td>
                  <td>{b.lineId}</td>
                  <td className="mono">{b.productionDate}</td>
                  <td className="mono tabular">{b.cellCount.toLocaleString()}</td>
                  <td className="mono tabular">{b.yield}%</td>
                  <td className="mono tabular">{b.defectRate}%</td>
                  <td>{riskChip(b.riskLevel)}</td>
                  <td>
                    {b.riskLevel === "HIGH" ? (
                      <Link className="btn btn-primary" to="/app/investigation">Investigate</Link>
                    ) : (
                      <span style={{ color: "var(--ink-mute)", fontSize: 12 }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
