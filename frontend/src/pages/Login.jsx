import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { FlaskConical, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "../auth/AuthContext.jsx";
import { ELScan } from "../assets/Art.jsx";
import AmbientOrbs from "../components/AmbientOrbs.jsx";
import Logo from "../components/Logo.jsx";

const ICONS = { "Quality Engineer": Sparkles, "ML Operations Lead": FlaskConical, "Platform Administrator": ShieldCheck };

const QUICK = [
  { email: "q.nair@meridiansolar.example", name: "Q. Nair", role: "Quality Engineer" },
  { email: "j.alvarez@meridiansolar.example", name: "J. Alvarez", role: "ML Operations Lead" },
  { email: "r.chen@meridiansolar.example", name: "R. Chen", role: "Platform Administrator" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function doLogin(loginEmail, loginPassword) {
    setBusy(true);
    setError(null);
    try {
      await login(loginEmail, loginPassword);
      navigate(location.state?.from?.pathname || "/app", { replace: true });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "grid", gridTemplateColumns: "1fr 1fr" }}>
      <div style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center", padding: 32, overflow: "hidden" }}>
        <AmbientOrbs />
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 360 }}
        >
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 28, textDecoration: "none", color: "var(--ink)" }}>
            <Logo size={26} />
            <span className="brand-lockup">
              <span className="brand-word"><span className="cell">Cell</span><span className="mind">Mind</span></span>
              <span className="brand-tagline">Intelligent Yield Optimization</span>
            </span>
          </Link>
          <h1 style={{ fontSize: 22, margin: "0 0 6px" }}>Sign in</h1>
          <p style={{ color: "var(--ink-mute)", fontSize: 13, margin: "0 0 22px" }}>RBAC-scoped access — your role controls what you can approve.</p>

          <form onSubmit={(e) => { e.preventDefault(); doLogin(email, password); }} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="q.nair@meridiansolar.example" required />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="anything (mock auth)" required />
            </div>
            {error && <div className="alert alert-bad">{error}</div>}
            <button className="btn btn-primary" disabled={busy} style={{ padding: "10px 14px", marginTop: 4 }}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div style={{ margin: "22px 0 10px", fontSize: 11, color: "var(--ink-mute)", textTransform: "uppercase", letterSpacing: ".05em" }}>
            Quick login (demo roles)
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {QUICK.map((u) => {
              const Icon = ICONS[u.role];
              return (
                <button
                  key={u.email}
                  type="button"
                  className="btn btn-secondary"
                  style={{ justifyContent: "space-between", display: "flex" }}
                  disabled={busy}
                  onClick={() => { setEmail(u.email); doLogin(u.email, "demo"); }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}><Icon className="icon" />{u.name}</span>
                  <span className="mono" style={{ fontSize: 11, color: "var(--ink-mute)" }}>{u.role}</span>
                </button>
              );
            })}
          </div>
        </motion.div>
      </div>

      <div style={{ background: "var(--ink)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative", overflow: "hidden" }}>
        <motion.div
          initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          style={{ background: "#FFFFFF", borderRadius: 14, padding: "12px 20px", marginBottom: 32, boxShadow: "0 12px 32px rgba(0,0,0,.35)" }}
        >
          <img src="/logo-transparent.png" alt="CellMind — Intelligent Yield Optimization" style={{ height: 44, width: "auto", display: "block" }} />
        </motion.div>
        <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
          <ELScan width={320} height={320} severity="HIGH" />
        </motion.div>
        <div style={{ position: "absolute", bottom: 28, left: 28, right: 28, color: "#B7C0C7", fontSize: 12.5 }}>
          Live EL scan render — Batch B1847, Cell C392. Defect probability 87%, confidence 91%.
        </div>
      </div>
    </div>
  );
}
