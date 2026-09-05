import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScanEye, Loader2 } from "lucide-react";
import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";
import { ELScan } from "../assets/Art.jsx";

async function loadSamples() {
  const batches = await api.listBatches();
  const bySeverity = {};
  for (const batch of batches) {
    if (bySeverity.HIGH && bySeverity.MEDIUM && bySeverity.LOW) break;
    const { items } = await api.batchCells(batch.batchId);
    for (const c of items) {
      if (!bySeverity[c.severity]) bySeverity[c.severity] = c;
    }
  }
  return ["HIGH", "MEDIUM", "LOW"]
    .map((sev) => bySeverity[sev])
    .filter(Boolean)
    .map((c) => ({ cellId: c.cellId, label: `Cell ${c.cellId} · Batch ${c.batchId}`, severity: c.severity }));
}

export default function Inference() {
  const { data: samples, loading: samplesLoading, error: samplesError } = useFetch(loadSamples, []);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [upload, setUpload] = useState(null);

  useEffect(() => {
    if (samples?.length && !selected) setSelected(samples[0]);
  }, [samples]); // eslint-disable-line react-hooks/exhaustive-deps

  async function runInference() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      if (upload) {
        const r = await api.predictImage(upload);
        setResult(r);
      } else {
        const r = await api.inspectCell(selected.cellId);
        setResult(r);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function onFileChosen(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUpload(file);
    setResult(null);
    setError(null);
  }

  function clearUpload() {
    setUpload(null);
    setResult(null);
    setError(null);
  }

  return (
    <>
      <h1 className="page-title">Inference — Run Inspection</h1>
      <p className="page-sub">
        FR-02 / FR-03 — pick a sample EL scan, or upload any panel photo to run it through the
        live fault classifier.
      </p>

      {samplesLoading && <p className="loading">Loading sample cells…</p>}
      {samplesError && <p className="error-box">Failed to load sample cells: {samplesError.message}</p>}
      {samples && (
        <div className="grid cols-3" style={{ marginBottom: 16 }}>
          {samples.map((s) => (
            <div
              key={s.cellId}
              className="card"
              style={{ cursor: "pointer", borderColor: !upload && selected?.cellId === s.cellId ? "var(--accent)" : undefined }}
              onClick={() => { setSelected(s); setUpload(null); setResult(null); }}
            >
              <ELScan width={220} height={140} severity={s.severity} />
              <div style={{ marginTop: 8, fontSize: 12.5, fontWeight: 600 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="card" style={{ marginBottom: 16, borderColor: upload ? "var(--accent)" : undefined }}>
        <label style={{ fontSize: 12.5, fontWeight: 600, display: "block", marginBottom: 8 }}>
          Or upload your own panel photo
        </label>
        <input type="file" accept="image/*" onChange={onFileChosen} />
        {upload && (
          <div style={{ marginTop: 8, fontSize: 12.5, color: "var(--ink-soft)" }}>
            {upload.name} selected
            <button className="btn" onClick={clearUpload} style={{ marginLeft: 10, padding: "2px 10px" }}>
              Clear
            </button>
          </div>
        )}
      </div>

      <button className="btn btn-primary" disabled={busy || (!upload && !selected)} onClick={runInference} style={{ padding: "10px 18px", marginBottom: 16 }}>
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
            {result.oodFlag && (
              <div className="alert alert-bad" style={{ marginBottom: 10 }}>
                Unknown defect pattern detected — manual inspection required (FR-15).
              </div>
            )}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
              <span className="chip chip-bad">DEFECT PROB. {Math.round(result.result.defectProbability * 100)}%</span>
              <span className="chip chip-warn">SEVERITY: {result.result.severity}</span>
              <span className="chip dot chip-good">CONFIDENCE {Math.round(result.confidence * 100)}%</span>
              <span className="chip">{result.confidenceBand}</span>
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
