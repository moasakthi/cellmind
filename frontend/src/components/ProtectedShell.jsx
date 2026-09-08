import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, ScanEye, Search, ClipboardCheck, Camera, RefreshCw, ListTree, ShieldCheck, LogOut } from "lucide-react";
import { useAuth } from "../auth/AuthContext.jsx";
import ThemeSwitcher from "./ThemeSwitcher.jsx";
import PageFade from "./PageFade.jsx";
import Logo from "./Logo.jsx";
import ChatWidget from "./ChatWidget.jsx";

const NAV = [
  { to: "/app", label: "Dashboard", end: true, icon: LayoutDashboard },
  { to: "/app/inference", label: "Inference", icon: ScanEye },
  { to: "/app/investigation", label: "Investigation", icon: Search },
  { to: "/app/recommendation", label: "Recommendations", icon: ClipboardCheck },
  { to: "/app/cameras", label: "Cameras", icon: Camera, permission: "manage_cameras" },
  { to: "/app/retraining", label: "Retraining", icon: RefreshCw, permission: "approve_retrain" },
  { to: "/app/taxonomy", label: "Taxonomy", icon: ListTree, permission: "configure_taxonomy" },
  { to: "/app/rbac", label: "RBAC & Audit", icon: ShieldCheck, permission: "manage_rbac" },
];

export default function ProtectedShell() {
  const { user, has, logout } = useAuth();
  const visible = NAV.filter((item) => !item.permission || has(item.permission));

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="brand">
          <Logo size={26} />
          <span className="brand-lockup">
            <span className="brand-word"><span className="cell">Cell</span><span className="mind">Mind</span></span>
            <span className="brand-tagline">Intelligent Yield Optimization</span>
          </span>
        </div>
        {visible.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => (isActive ? "active" : "")}>
              <Icon className="icon" /> {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div>
        <div className="topbar">
          <span style={{ fontSize: 13, color: "var(--ink-mute)" }}>
            Tenant: <b style={{ color: "var(--ink)" }}>Meridian Solar — Plant 2</b>
          </span>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <span className="chip chip-info">{user?.name} · {user?.role?.roleName}</span>
            <ThemeSwitcher />
            <button className="btn btn-secondary" onClick={logout}><LogOut className="icon" />Sign out</button>
          </div>
        </div>
        <main className="content">
          <PageFade>
            <Outlet />
          </PageFade>
        </main>
      </div>

      <ChatWidget />
    </div>
  );
}
