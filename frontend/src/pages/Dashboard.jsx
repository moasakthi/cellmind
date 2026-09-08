import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TrendingUp, AlertTriangle, ShieldAlert, Layers, ArrowUpRight, Wifi, WifiOff, Camera } from "lucide-react";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";
import Sparkline from "../components/Sparkline.jsx";
import InfoTooltip from "../components/InfoTooltip.jsx";
import TrendChart from "../components/TrendChart.jsx";
import StatusBar from "../components/StatusBar.jsx";
import RankedBarList from "../components/RankedBarList.jsx";

function riskChip(level) {
  const cls = level === "HIGH" ? "chip-bad" : level === "MEDIUM" ? "chip-warn" : "chip-neutral";
  return <span className={`chip ${cls}`}>{level}</span>;
}

function fmtDelta(delta) {
  if (delta == null) return null;
  const sign = delta >= 0 ? "+" : "";
  return `${sign}${delta.toFixed(1)} pts`;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: batches, loading, error } = useFetch(() => api.listBatches(), []);
  const { data: equipment, loading: equipLoading } = useFetch(() => api.listEquipment(), []);
  const { data: cameras, loading: camLoading } = useFetch(() => api.listCameras(), []);
  const { data: auditLog, loading: auditLoading } = useFetch(() => api.auditLog(), []);
  const [investigatingId, setInvestigatingId] = useState(null);
  const [investigateError, setInvestigateError] = useState(null);

  if (loading || equipLoading || camLoading || auditLoading) return <p className="loading">Loading dashboard…</p>;
  if (error) return <p className="error-box">Failed to load batches: {error.message}</p>;

  async function investigate(batchId) {
    setInvestigatingId(batchId);
    setInvestigateError(null);
    try {
      const { items } = await api.listInvestigations();
      const existing = items.find((i) => i.batchId === batchId);
      const inv = existing || (await api.createInvestigation({ batchId }));
      navigate(`/app/investigation/${inv.investigationId}`);
    } catch (e) {
      setInvestigateError(`Batch ${batchId}: ${e.message}`);
    } finally {
      setInvestigatingId(null);
    }
  }

  // ---- KPI row: real trends derived from batches in production order ----
  const byDate = [...batches].sort((a, b) => new Date(a.productionDate) - new Date(b.productionDate));
  const xLabels = byDate.map((b) => new Date(b.productionDate).toLocaleDateString(undefined, { month: "short", day: "numeric" }));
  const yieldTrend = byDate.map((b) => b.yield);
  const defectTrend = byDate.map((b) => b.defectRate);
  let riskRunning = 0;
  const highRiskTrend = byDate.map((b) => (riskRunning += b.riskLevel === "HIGH" ? 1 : 0));
  const trackedTrend = byDate.map((_, i) => i + 1);

  const totalCells = batches.reduce((s, b) => s + b.cellCount, 0);
  const totalDefects = batches.reduce((s, b) => s + b.defectCount, 0);
  const avgYield = (batches.reduce((s, b) => s + b.yield, 0) / batches.length).toFixed(1);
  const avgDefect = ((totalDefects / totalCells) * 100).toFixed(1);
  const highRisk = batches.filter((b) => b.riskLevel === "HIGH").length;

  const yieldDelta = yieldTrend.length > 1 ? yieldTrend[yieldTrend.length - 1] - yieldTrend[0] : null;
  const defectDelta = defectTrend.length > 1 ? defectTrend[defectTrend.length - 1] - defectTrend[0] : null;

  const kpis = [
    {
      label: "Plant Yield (avg)", value: `${avgYield}%`, icon: TrendingUp, trend: yieldTrend,
      delta: fmtDelta(yieldDelta), bad: yieldDelta != null && yieldDelta < 0,
      info: "Average percentage of cells that passed inspection across every tracked batch. A sustained downward trend signals a process or equipment issue worth investigating before it compounds across future batches.",
    },
    {
      label: "Defect Rate (avg)", value: `${avgDefect}%`, icon: AlertTriangle, trend: defectTrend,
      delta: fmtDelta(defectDelta), bad: defectDelta != null && defectDelta > 0,
      info: "Average percentage of cells flagged defective — the inverse of yield. Rising defect rate is usually the earliest warning signal for a drifting process parameter or aging equipment, ahead of a visible yield drop.",
    },
    {
      label: "High-Risk Batches", value: highRisk, icon: ShieldAlert, trend: highRiskTrend,
      info: "Batches whose defect rate crossed the HIGH risk threshold. These are the ones worth opening an investigation on first — use the Investigate button in the table below to run the inspection/root-cause pipeline against them.",
    },
    {
      label: "Batches Tracked", value: batches.length, icon: Layers, trend: trackedTrend,
      info: "Total number of production batches currently recorded. Treat this as denominator context for the other KPIs — with a small sample, risk percentages can swing sharply on a single bad batch.",
    },
  ];

  // ---- Risk distribution ----
  const riskCounts = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  batches.forEach((b) => { riskCounts[b.riskLevel] = (riskCounts[b.riskLevel] || 0) + 1; });
  const riskSegments = [
    { key: "LOW", label: "Low", value: riskCounts.LOW, color: "var(--good)" },
    { key: "MEDIUM", label: "Medium", value: riskCounts.MEDIUM, color: "var(--furnace)" },
    { key: "HIGH", label: "High", value: riskCounts.HIGH, color: "var(--danger)" },
  ];

  // ---- Defect rate by production line ----
  const lineGroups = {};
  batches.forEach((b) => { (lineGroups[b.lineId] ??= []).push(b); });
  const lineItems = Object.entries(lineGroups).map(([lineId, rows]) => ({
    key: lineId, label: lineId,
    value: +(rows.reduce((s, r) => s + r.defectRate, 0) / rows.length).toFixed(1),
    sublabel: `${rows.length} batch${rows.length === 1 ? "" : "es"} on ${lineId}`,
  }));

  // ---- Equipment defect contribution ----
  const equipItems = equipment.map((e) => ({
    key: e.equipmentId, label: e.equipmentId, value: e.shareOfDefectsPct,
    sublabel: `${e.defectiveUnits}/${e.unitsProduced} units defective — ${e.defectRatePct}% defect rate`,
  }));
  const topEquip = [...equipItems].sort((a, b) => b.value - a.value)[0];

  // ---- Camera fleet health ----
  const camByLine = {};
  cameras.forEach((c) => { (camByLine[c.lineId] ??= []).push(c); });
  const offlineLines = Object.entries(camByLine)
    .filter(([, cams]) => cams.length > 0 && cams.every((c) => c.status === "OFFLINE"))
    .map(([lineId]) => lineId);
  const camCounts = { ONLINE: 0, DEGRADED: 0, OFFLINE: 0 };
  cameras.forEach((c) => { camCounts[c.status] = (camCounts[c.status] || 0) + 1; });

  // ---- Recent activity ----
  const recentEvents = [...auditLog].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 6);

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-sub">Live from the FastAPI + SQLite backend — every widget below is computed from real batch, equipment, camera, and audit data.</p>

      <div className="grid cols-4" style={{ marginBottom: 18 }}>
        {kpis.map((k) => {
          const Icon = k.icon;
          return (
            <div key={k.label} className="card kpi">
              <div className="kpi-head">
                <span className="label" style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  {k.label}
                  <InfoTooltip title={k.label}>{k.info}</InfoTooltip>
                </span>
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

      <div className="grid cols-2" style={{ marginBottom: 18 }}>
        <div className="card">
          <div className="widget-head">
            <h3>Yield vs Defect Rate Trend</h3>
            <InfoTooltip title="Yield vs Defect Rate Trend" align="right">
              Plant yield and defect rate plotted across every tracked batch, in production order. The two should
              move as mirror images — if one climbs without the other correspondingly moving, it's worth a second look.
            </InfoTooltip>
          </div>
          <TrendChart
            xLabels={xLabels}
            series={[
              { key: "yield", label: "Yield", color: "var(--good)", points: yieldTrend },
              { key: "defect", label: "Defect Rate", color: "var(--danger)", points: defectTrend },
            ]}
          />
        </div>

        <div className="card">
          <div className="widget-head">
            <h3>Batches by Risk Level</h3>
            <InfoTooltip title="Batches by Risk Level" align="right">
              Every tracked batch bucketed into LOW/MEDIUM/HIGH risk by its defect rate. A growing HIGH share across
              recent batches is an early escalation signal — don't wait for it to show up in the yield KPI.
            </InfoTooltip>
          </div>
          <StatusBar segments={riskSegments} />
          <p style={{ fontSize: 12, color: "var(--ink-mute)", marginTop: 18, marginBottom: 0, lineHeight: 1.6 }}>
            {riskCounts.HIGH > 0 ? (
              <>Insight: <b style={{ color: "var(--ink)" }}>{riskCounts.HIGH} of {batches.length}</b> tracked batches
                ({Math.round((riskCounts.HIGH / batches.length) * 100)}%) are currently HIGH risk — prioritize those
                in the Recent Batches table below.</>
            ) : "Insight: no batches are currently flagged HIGH risk."}
          </p>
        </div>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 18 }}>
        <div className="card">
          <div className="widget-head">
            <h3>Defect Rate by Line</h3>
            <InfoTooltip title="Defect Rate by Line" align="right">
              Average defect rate compared across production lines. A line running meaningfully hotter than its
              peers usually points to a line-specific cause (equipment, camera coverage, local process drift) rather
              than a plant-wide issue.
            </InfoTooltip>
          </div>
          {lineItems.length > 0
            ? <RankedBarList items={lineItems} unit="%" accent="var(--danger)" />
            : <p style={{ fontSize: 12.5, color: "var(--ink-mute)" }}>No batch data yet.</p>}
        </div>

        <div className="card">
          <div className="widget-head">
            <h3>Equipment Defect Contribution</h3>
            <InfoTooltip title="Equipment Defect Contribution" align="right">
              Share of all defective cells attributable to each piece of equipment. This is the same signal the
              platform's RootCauseAgent uses — the top contributor is usually where a maintenance or calibration
              action will have the largest yield impact.
            </InfoTooltip>
          </div>
          {equipItems.length > 0 ? (
            <>
              <RankedBarList items={equipItems} unit="%" accent="var(--furnace)" />
              {topEquip && (
                <div className="alert alert-warn" style={{ marginTop: 12, marginBottom: 0 }}>
                  <AlertTriangle className="icon" style={{ flex: "none" }} />
                  <span><b className="mono">{topEquip.label}</b> accounts for {topEquip.value}% of all defects — the highest-leverage equipment to inspect first.</span>
                </div>
              )}
            </>
          ) : <p style={{ fontSize: 12.5, color: "var(--ink-mute)" }}>No equipment data yet.</p>}
        </div>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 18 }}>
        <div className="card">
          <div className="widget-head">
            <h3>Camera Fleet Health</h3>
            <InfoTooltip title="Camera Fleet Health" align="right">
              Live status of every registered inspection camera, grouped by line. Per BR-11, if every camera on a
              line goes offline that line silently falls back to manual inspection — this is the fastest way to notice it.
            </InfoTooltip>
          </div>
          <div className="grid cols-3" style={{ gap: 10 }}>
            <div className="mini-stat">
              <Wifi className="icon" style={{ color: "var(--good-ink)" }} />
              <span className="n" style={{ color: "var(--good-ink)" }}>{camCounts.ONLINE}</span>
              <span className="l">Online</span>
            </div>
            <div className="mini-stat">
              <Camera className="icon" style={{ color: "var(--furnace-ink)" }} />
              <span className="n" style={{ color: "var(--furnace-ink)" }}>{camCounts.DEGRADED}</span>
              <span className="l">Degraded</span>
            </div>
            <div className="mini-stat">
              <WifiOff className="icon" style={{ color: "var(--danger-ink)" }} />
              <span className="n" style={{ color: "var(--danger-ink)" }}>{camCounts.OFFLINE}</span>
              <span className="l">Offline</span>
            </div>
          </div>
          {offlineLines.length > 0 && (
            <div className="alert alert-bad" style={{ marginTop: 12, marginBottom: 0 }}>
              <WifiOff className="icon" style={{ flex: "none" }} />
              <span>
                Line{offlineLines.length > 1 ? "s" : ""} <b className="mono">{offlineLines.join(", ")}</b>: every camera is offline —
                inspections on {offlineLines.length > 1 ? "these lines" : "this line"} fall back to manual review (BR-11 fail-open).
              </span>
            </div>
          )}
        </div>

        <div className="card">
          <div className="widget-head">
            <h3>Recent Activity</h3>
            <InfoTooltip title="Recent Activity" align="right">
              The latest governed actions recorded in the audit log — approvals, camera registrations, taxonomy
              publishes. A quick sanity check that approvals are made by someone other than the requester (BR-10)
              and that the platform isn't going quiet.
            </InfoTooltip>
          </div>
          {recentEvents.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {recentEvents.map((e) => (
                <div key={e.eventId} style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 10, fontSize: 12 }}>
                  <span>
                    <b className="mono">{e.actor}</b>{" "}
                    <span style={{ color: "var(--ink-soft)" }}>{e.action.replace(/_/g, " ")}</span>{" "}
                    <span className="mono" style={{ color: "var(--ink-mute)" }}>{e.targetId}</span>
                  </span>
                  <span className="mono" style={{ color: "var(--ink-mute)", whiteSpace: "nowrap" }}>
                    {new Date(e.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  </span>
                </div>
              ))}
            </div>
          ) : <p style={{ fontSize: 12.5, color: "var(--ink-mute)" }}>No activity recorded yet.</p>}
        </div>
      </div>

      <div className="card">
        <div className="widget-head">
          <h3>Recent Batches</h3>
          <InfoTooltip title="Recent Batches" align="right">
            Every tracked batch with its yield, defect rate, and risk level. HIGH-risk batches get an Investigate
            action that runs the inspection/process/context/root-cause agent pipeline and opens the result.
          </InfoTooltip>
        </div>
        {investigateError && <div className="alert alert-bad" style={{ marginBottom: 10 }}>{investigateError}</div>}
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
                      <button
                        className="btn btn-primary"
                        disabled={investigatingId === b.batchId}
                        onClick={() => investigate(b.batchId)}
                      >
                        {investigatingId === b.batchId ? "Opening…" : "Investigate"}
                      </button>
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
