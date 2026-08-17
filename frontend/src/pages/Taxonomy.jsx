import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";

function sevChip(sev) {
  const cls = sev === "HIGH" ? "chip-bad" : sev === "MEDIUM" ? "chip-warn" : "chip-neutral";
  return <span className={`chip ${cls}`}>{sev}</span>;
}

export default function Taxonomy() {
  const { data: entries, loading, error } = useFetch(() => api.listTaxonomy(), []);
  const { data: versions } = useFetch(() => api.listTaxonomyVersions(), []);

  if (loading) return <p className="loading">Loading taxonomy…</p>;
  if (error) return <p className="error-box">Failed to load taxonomy: {error.message}</p>;

  return (
    <>
      <h1 className="page-title">Defect Taxonomy</h1>
      <p className="page-sub">FR-21 — version {versions?.[0]?.versionId ?? "…"}</p>

      <div className="card">
        <h3>Categories</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Category</th><th>Subtype</th><th>Severity</th><th>Root-Cause Family</th></tr></thead>
            <tbody>
              {entries.map((t) => (
                <tr key={t.taxonomyId} className={t.severity === "HIGH" ? "hi" : ""}>
                  <td>{t.category}</td>
                  <td>{t.subtype}</td>
                  <td>{sevChip(t.severity)}</td>
                  <td>{t.rootCauseFamily}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
