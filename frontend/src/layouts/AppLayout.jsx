import { Activity, ClipboardPlus, Clock3, LayoutDashboard, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/assess", label: "New assessment", icon: ClipboardPlus },
  { to: "/history", label: "Assessment history", icon: Clock3 },
  { to: "/performance", label: "Model performance", icon: Activity },
];

export default function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><Activity size={21} /></span><span>Healthwise<small>Decision support</small></span></div>
        <div className="sidebar-label">WORKSPACE</div>
        <nav aria-label="Primary navigation">
          {links.map(({ to, label, icon: Icon, end }) => <NavLink key={to} to={to} end={end} aria-label={label} title={label} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}><Icon size={18} /><span>{label}</span></NavLink>)}
        </nav>
        <div className="sidebar-bottom"><ShieldCheck size={18} /><span>Educational use only<small>Not a medical diagnosis</small></span></div>
      </aside>
      <div className="main-column">
        <header className="topbar"><span className="topbar-context">Healthcare analytics</span><span className="topbar-badge"><span /> Local demo</span></header>
        <main className="page-content"><Outlet /></main>
        <footer className="footer-note">For educational demonstration only. This tool does not diagnose, treat, or replace advice from a qualified healthcare professional.</footer>
      </div>
    </div>
  );
}
