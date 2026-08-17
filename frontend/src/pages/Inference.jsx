import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScanEye, Loader2 } from "lucide-react";
import { api } from "../api/client.js";
import { ELScan } from "../assets/Art.jsx";

const SAMPLES = [
  { cellId: "C392", label: "Cell C392 · Batch B1847", severity: "HIGH" },
  { cellId: "C393", label: "Cell C393 · Batch B1847", severity: "LOW" },
  { cellId: "C201", label: "Cell C201 · Batch B1846", severity: "LOW" },
];

export default function Inference() {
  const [selected, setSelected] = useState(SAMPLES[0]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function runInference() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const r = await api.inspectCell(selected.cellId);
      await new Promise((res) => setTimeout(res, 600)); // let the pipeline feel real
      setResult(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1 className="page-title">Inference — Run Inspection</h1>
      <p className="page-sub">FR-02 / FR-03 — pick a sample EL scan and call the live inspection endpoint.</p>

      <div className="grid cols-3" style={{ marginBottom: 16 }}>
        {SAMPLES.map((s) => (
          <div
            key={s.cellId}
            className="card"
            style={{ cursor: "pointer", borderColor: selected.cellId === s.cellId ? "var(--accent)" : undefined }}
            onClick={() => { setSelected(s); setResult(null); }}
          >
            <ELScan width={220} height={140} severity={s.severity} />
            <div style={{ marginTop: 8, fontSize: 12.5, fontWeight: 600 }}>{s.label}</div>
          </div>
        ))}
      </div>

      <button className="btn btn-primary" disabled={busy} onClick={runInference} style={{ padding: "10px 18px", marginBottom: 16 }}>
        {busy ? <Loader2 className="icon" style={{ animation: "spin 1s linear infinite" }} /> : <ScanEye className="icon" />}
        {busy ? "Running Inspection Agent…" : "Run inference"}
      </button>
      <style>{"@keyframes spin{to{transform:rotate(360deg)}}"}</style>

      {error && <div className="alert alert-bad">{error}</div>}

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="card"
          >
            <h3>Inspection Agent Result</h3>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
              <span className="chip chip-bad">DEFECT PROB. {Math.round(result.result.defectProbability * 100)}%</span>
              <span className="chip chip-warn">SEVERITY: {result.result.severity}</span>
              <span className="chip dot chip-good">CONFIDENCE {Math.round(result.confidence * 100)}%</span>
            </div>
            {result.evidence.map((e, i) => (
              <div key={i} style={{ fontSize: 12.5, color: "var(--ink-soft)" }}>{e.description}</div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
