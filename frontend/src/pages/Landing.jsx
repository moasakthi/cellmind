import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ScanEye, Thermometer, History, Brain, Wrench, FlaskConical, CheckCircle2,
  Camera, RefreshCw, SlidersHorizontal, ListTree, ShieldCheck,
  TrendingUp, Clock3, PackageMinus, Users,
} from "lucide-react";
import { ELScan, SolarPanelGrid, SunMark } from "../assets/Art.jsx";
import ThemeSwitcher from "../components/ThemeSwitcher.jsx";
import AmbientOrbs from "../components/AmbientOrbs.jsx";
import BenefitsSlider from "../components/BenefitsSlider.jsx";

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] } },
};
const stagger = { visible: { transition: { staggerChildren: 0.09 } } };

const AGENTS = [
  ["Inspection", ScanEye], ["Process", Thermometer], ["Context", History], ["Root Cause", Brain],
  ["Optimization", Wrench], ["Simulation", FlaskConical], ["Validation", CheckCircle2],
];
const CAPS = [
  ["FR-18", "Live camera ingestion", Camera],
  ["FR-19", "Governed retraining", RefreshCw],
  ["FR-20", "Configurable autonomy", SlidersHorizontal],
  ["FR-21", "Versioned taxonomy", ListTree],
  ["FR-22", "Role-based access", ShieldCheck],
];

const BENEFITS = [
  {
    tag: "YIELD IMPROVEMENT", icon: TrendingUp, title: "Simulated before it's approved, not hoped for after",
    body: "Every corrective action is scored for expected impact before an engineer signs off. On the B1847/F07 scenario, the recommended fix predicted +2.8 points of yield — validated against the next batch, not assumed.",
  },
  {
    tag: "TIME-TO-ROOT-CAUSE", icon: Clock3, title: "One investigation instead of six systems",
    body: "Inspection images, process telemetry, equipment logs and SOPs are correlated automatically. What used to be a manual chase across disconnected tools becomes one Agent Hub run, evidence attached.",
  },
  {
    tag: "SCRAP REDUCTION", icon: PackageMinus, title: "Catch the furnace variance before the next batch runs",
    body: "F07's defect rate was 25.6% — nearly 9x its neighbors — but invisible until someone looked. Flagging it a batch earlier means fewer cells scrapped for the same recurring cause.",
  },
  {
    tag: "ENGINEERING PRODUCTIVITY", icon: Users, title: "Engineers review evidence, not assemble it",
    body: "The correlation work — which equipment, which parameter, which historical incident — is done by agents. Quality and Process Engineers spend their time on judgment, not data-gathering.",
  },
  {
    tag: "RECURRING DEFECT REDUCTION", icon: ShieldCheck, title: "Validated outcomes close the loop",
    body: "Predicted-vs-actual results feed the retraining pipeline (FR-19), so the same defect pattern is less likely to resurface undetected on a future batch.",
  },
];

export default function Landing() {
  return (
    <div>
      <nav style={{ position: "sticky", top: 0, zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 28px", borderBottom: "1px solid var(--line-soft)", background: "color-mix(in srgb, var(--paper) 75%, transparent)", backdropFilter: "blur(14px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 15 }}><SunMark />CellMind</div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <ThemeSwitcher />
          <Link className="btn btn-primary" to="/login">Sign in</Link>
        </div>
      </nav>

      <header style={{ position: "relative", padding: "110px 28px 70px", maxWidth: 1080, margin: "0 auto", overflow: "hidden" }}>
        <AmbientOrbs />
        <motion.div initial="hidden" animate="visible" variants={stagger} style={{ position: "relative", zIndex: 1, display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 48, alignItems: "center" }}>
          <div>
            <motion.span variants={fadeUp} className="chip chip-info" style={{ marginBottom: 20, display: "inline-block" }}>SYNAPT AGENT HUB</motion.span>
            <motion.h1 variants={fadeUp} style={{ fontSize: "clamp(34px,5.5vw,54px)", fontWeight: 800, letterSpacing: "-.025em", margin: "18px 0", lineHeight: 1.08, textWrap: "balance" }}>
              Don't just detect the defect.<br /><span className="gradient-text">Find why it happened.</span>
            </motion.h1>
            <motion.p variants={fadeUp} style={{ color: "var(--ink-soft)", fontSize: 16.5, maxWidth: "48ch", margin: "0 0 30px" }}>
              CellMind traces a solar-cell defect back to its furnace, explains the evidence, and recommends the fix — before the next batch fails.
            </motion.p>
            <motion.div variants={fadeUp} style={{ display: "flex", gap: 12 }}>
              <Link className="btn btn-primary" to="/login" style={{ padding: "12px 20px", fontSize: 13.5 }}>Sign in to CellMind</Link>
              <a className="btn btn-secondary" href="#agents" style={{ padding: "12px 20px", fontSize: 13.5 }}>How it works</a>
            </motion.div>
          </div>
          <motion.div variants={fadeUp} className="card" style={{ padding: 10 }}>
            <ELScan width={360} height={300} severity="HIGH" />
          </motion.div>
        </motion.div>
      </header>

      <section id="agents" style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto" }}>
        <motion.h2 initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ fontSize: 28, fontWeight: 700, marginBottom: 28, letterSpacing: "-.01em" }}>
          Seven agents, one investigation
        </motion.h2>
        <motion.div
          initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.3 }} variants={stagger}
          style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 14 }}
        >
          {AGENTS.map(([a, Icon], i) => (
            <motion.div key={a} variants={fadeUp} className="card">
              <div className="kpi-head">
                <span className="mono" style={{ fontSize: 11, color: "var(--ink-mute)" }}>{String(i + 1).padStart(2, "0")}</span>
                <span className="icon-badge"><Icon className="icon" /></span>
              </div>
              <div style={{ fontWeight: 700, fontSize: 14, marginTop: 12 }}>{a}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto" }}>
        <motion.h2 initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ fontSize: 28, fontWeight: 700, marginBottom: 28, letterSpacing: "-.01em" }}>
          Beyond one investigation
        </motion.h2>
        <motion.div
          initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.3 }} variants={stagger}
          style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(190px,1fr))", gap: 14 }}
        >
          {CAPS.map(([tag, title, Icon]) => (
            <motion.div key={tag} variants={fadeUp} className="card">
              <span className="icon-badge"><Icon className="icon" /></span>
              <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)", marginTop: 12 }}>{tag}</div>
              <div style={{ fontWeight: 700, fontSize: 14, marginTop: 4 }}>{title}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto", textAlign: "center" }}>
        <motion.span initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="chip chip-info" style={{ marginBottom: 14, display: "inline-block" }}>
          BUSINESS IMPACT
        </motion.span>
        <motion.h2 initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ fontSize: 28, fontWeight: 700, marginBottom: 8, letterSpacing: "-.01em" }}>
          Why manufacturers use CellMind
        </motion.h2>
        <p style={{ color: "var(--ink-mute)", fontSize: 13.5, marginBottom: 34 }}>
          Illustrated with the B1847/F07 scenario walked through above. Actual ROI depends on your volume, scrap cost and yield baseline.
        </p>
        <BenefitsSlider slides={BENEFITS} />
      </section>

      <section style={{ position: "relative", padding: "80px 28px 110px", textAlign: "center", overflow: "hidden" }}>
        <AmbientOrbs variant="wide" />
        <div style={{ position: "relative", zIndex: 1 }}>
          <SolarPanelGrid width={200} height={110} />
          <p style={{ maxWidth: "26ch", margin: "26px auto 24px", fontSize: 24, fontWeight: 700, letterSpacing: "-.01em" }}>
            "Find why it happened — and prevent the next batch from failing."
          </p>
          <Link className="btn btn-primary" to="/login" style={{ padding: "12px 22px", fontSize: 13.5 }}>Sign in to CellMind</Link>
        </div>
      </section>
    </div>
  );
}
