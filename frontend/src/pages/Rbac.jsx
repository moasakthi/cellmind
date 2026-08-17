import { api } from "../api/client.js";
import { useFetch } from "../api/useFetch.js";

export default function Rbac() {
  const { data: users, loading, error } = useFetch(() => api.listUsers(), []);
  const { data: roles } = useFetch(() => api.listRoles(), []);
  const { data: log } = useFetch(() => api.auditLog(), []);

  if (loading) return <p className="loading">Loading RBAC…</p>;
  if (error) return <p className="error-box">Failed to load RBAC data: {error.message}</p>;

  function roleName(roleId) {
    return roles?.find((r) => r.roleId === roleId)?.roleName ?? roleId;
  }

  return (
    <>
      <h1 className="page-title">RBAC &amp; Audit</h1>
      <p className="page-sub">FR-22, NFR-05</p>

      <div className="grid cols-2" style={{ marginBottom: 14 }}>
        <div className="card">
          <h3>Users</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>User</th><th>Role</th></tr></thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.userId}>
                    <td className="mono">{u.name}</td>
                    <td>{roleName(u.roleId)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="card">
          <h3>Roles → Permissions</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Role</th><th>Permissions</th></tr></thead>
              <tbody>
                {roles?.map((r) => (
                  <tr key={r.roleId}>
                    <td>{r.roleName}</td>
                    <td className="mono" style={{ fontSize: 11 }}>{r.permissions.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Audit Log (tail)</h3>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Target</th></tr></thead>
            <tbody>
              {log?.map((e) => (
                <tr key={e.eventId}>
                  <td className="mono">{new Date(e.timestamp).toLocaleTimeString()}</td>
                  <td className="mono">{e.actor}</td>
                  <td>{e.action}</td>
                  <td className="mono">{e.targetId}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
