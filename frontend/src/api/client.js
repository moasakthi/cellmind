const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || `Request failed: ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

async function upload(path, file) {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${BASE}${path}`, { method: "POST", body });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || `Request failed: ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  login: (email, password) => request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: (asUser) => request(`/users/me${asUser ? `?as_user=${asUser}` : ""}`),
  listUsers: () => request("/rbac/users"),
  listRoles: () => request("/rbac/roles"),
  inspectCell: (cellId) => request(`/cells/${cellId}/inspect`, { method: "POST" }),
  predictImage: (file) => upload("/inference/predict", file),

  listBatches: () => request("/batches"),
  getBatch: (id) => request(`/batches/${id}`),
  batchCells: (id) => request(`/batches/${id}/cells`),
  batchProcess: (id) => request(`/batches/${id}/process`),

  listEquipment: () => request("/equipment"),

  listCameras: () => request("/cameras"),
  createCamera: (payload) => request("/cameras", { method: "POST", body: JSON.stringify(payload) }),
  cameraHealth: (id) => request(`/cameras/${id}/health`),

  getInvestigation: (id) => request(`/investigations/${id}`),
  getRecommendation: (investigationId) => request(`/recommendations/${investigationId}`),
  approveRecommendation: (id, payload) =>
    request(`/recommendations/${id}/approve`, { method: "POST", body: JSON.stringify(payload) }),

  listRuns: () => request("/retraining/runs"),
  approveRun: (id, payload) =>
    request(`/retraining/runs/${id}/approve`, { method: "POST", body: JSON.stringify(payload) }),

  listTaxonomy: () => request("/taxonomy"),
  listTaxonomyVersions: () => request("/taxonomy/versions"),

  auditLog: () => request("/audit-log"),
};
