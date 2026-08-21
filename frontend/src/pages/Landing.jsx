import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ScanEye, Thermometer, History, Brain, Wrench, FlaskConical, CheckCircle2,
  Camera, RefreshCw, SlidersHorizontal, ListTree, ShieldCheck,
  BarChart3, ArrowRight, FileSearch, ClipboardList, AlertTriangle,
} from "lucide-react";
import { ELScan, SolarPanelGrid } from "../assets/Art.jsx";
import ThemeSwitcher from "../components/ThemeSwitcher.jsx";
import AnimatedBackground from "../components/AnimatedBackground.jsx";
import BenefitsSlider from "../components/BenefitsSlider.jsx";
import SolarGlitter from "../components/SolarGlitter.jsx";
import Logo from "../components/Logo.jsx";

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] } },
};
const stagger = { visible: { transition: { staggerChildren: 0.09 } } };

const PROBLEM_STEPS = [
  ["Batch produced", ClipboardList],
  ["Final inspection", ScanEye],
  ["Defects found", AlertTriangle],
  ["Manual investigation", FileSearch],
  ["Corrective action", Wrench],
  ["Next batch — same risk", RefreshCw],
];

const SOLUTION_STEPS = ["Detect", "Trace", "Explain", "Optimize", "Prevent", "Learn"];

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
    tag: "AGENT HUB", icon: Brain,
    feature: "Multi-agent root-cause tracing",
    benefit: "Time-to-root-cause collapses from a multi-day manual chase to one Agent Hub run, evidence attached.",
  },
  {
    tag: "EQUIPMENT CORRELATION · FR-05", icon: BarChart3,
    feature: "Rate-normalized defect correlation",
    benefit: "Flags the furnace that's actually high-risk per unit — not just the one running the most volume.",
  },
  {
    tag: "WHAT-IF SIMULATION · FR-10", icon: FlaskConical,
    feature: "Predicted-outcome simulation before approval",
    benefit: "See the expected yield impact of a fix before anything changes on the production floor.",
  },
  {
    tag: "GOVERNED RETRAINING · FR-19", icon: RefreshCw,
    feature: "Drift-triggered, holdout-evaluated retraining",
    benefit: "Models keep improving on real production data without silent, undetected drift.",
  },
  {
    tag: "RBAC + AUTONOMY · FR-20/22", icon: ShieldCheck,
    feature: "Role-scoped approval with segregation of duties",
    benefit: "Every recommendation is approved by the right person — and it's automatically audited, not just logged.",
  },
];

function DeckEyebrow({ n, children }) {
  return (
    <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="deck-eyebrow">
      <span className="num">{n}</span>
      <span className="txt">{children}</span>
    </motion.div>
  );
}

export default function Landing() {
  return (
    <div>
      <AnimatedBackground />

      <nav style={{ position: "sticky", top: 0, zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 28px", borderBottom: "1px solid var(--line-soft)", background: "color-mix(in srgb, var(--paper) 75%, transparent)", backdropFilter: "blur(14px)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Logo size={26} />
          <span className="brand-lockup">
            <span className="brand-word"><span className="cell">Cell</span><span className="mind">Mind</span></span>
            <span className="brand-tagline">Intelligent Yield Optimization</span>
          </span>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <ThemeSwitcher />
          <Link className="btn btn-primary" to="/login">Sign in</Link>
        </div>
      </nav>

      {/* COVER */}
      <header style={{ padding: "110px 28px 70px", maxWidth: 1080, margin: "0 auto" }}>
        <motion.div initial="hidden" animate="visible" variants={stagger} style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 48, alignItems: "center" }}>
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
              <a className="btn btn-secondary" href="#problem" style={{ padding: "12px 20px", fontSize: 13.5 }}>See the pitch <ArrowRight className="icon" /></a>
            </motion.div>
          </div>
          <motion.div variants={fadeUp} className="card" style={{ padding: 10 }}>
            <ELScan width={360} height={300} severity="HIGH" />
          </motion.div>
        </motion.div>
      </header>

      {/* 01 — PROBLEM */}
      <section id="problem" style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto" }}>
        <DeckEyebrow n="01">The Problem</DeckEyebrow>
        <motion.h2 initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ fontSize: 28, fontWeight: 700, marginBottom: 10, letterSpacing: "-.01em", maxWidth: "22ch" }}>
          Root-cause analysis is a manual chase across six disconnected systems
        </motion.h2>
        <p style={{ color: "var(--ink-mute)", fontSize: 14, marginBottom: 32, maxWidth: "60ch" }}>
          By the time an engineer confirms a cause by hand, the batch that caused it is already finished — and the next one is running the same risk.
        </p>
        <motion.div
          initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.3 }} variants={stagger}
          style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 12 }}
        >
          {PROBLEM_STEPS.map(([label, Icon], i) => (
            <motion.div key={label} variants={fadeUp} className="card" style={{ textAlign: "center", padding: 16 }}>
              <span className="icon-badge" style={{ margin: "0 auto 10px" }}><Icon className="icon" /></span>
              <div style={{ fontSize: 12.5, fontWeight: 600 }}>{label}</div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* 02 — SOLUTION */}
      <section style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto" }}>
        <DeckEyebrow n="02">The Solution</DeckEyebrow>
        <motion.h2 initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ fontSize: 28, fontWeight: 700, marginBottom: 28, letterSpacing: "-.01em", maxWidth: "26ch" }}>
          One closed loop, run by agents, reviewed by engineers
        </motion.h2>
        <motion.div
          initial="hidden" whileInView="visible" viewport={{ once: true, amount: 0.3 }} variants={stagger}
          style={{ display: "flex", gap: 0, overflowX: "auto" }}
        >
          {SOLUTION_STEPS.map((label, i) => (
            <motion.div key={label} variants={fadeUp} style={{ display: "flex", alignItems: "center", flex: "none" }}>
              <div className="card" style={{ padding: "14px 20px", textAlign: "center", minWidth: 110 }}>
                <div className="mono" style={{ fontSize: 10, color: "var(--ink-mute)" }}>{i + 1}</div>
                <div style={{ fontWeight: 700, fontSize: 13.5, marginTop: 4 }}>{label}</div>
              </div>
              {i < SOLUTION_STEPS.length - 1 && <ArrowRight className="icon" style={{ margin: "0 8px", color: "var(--ink-mute)" }} />}
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* 03 — HOW IT WORKS */}
      <section id="agents" style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto" }}>
        <DeckEyebrow n="03">How It Works</DeckEyebrow>
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

      {/* 04 — CAPABILITIES */}
      <section style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto" }}>
        <DeckEyebrow n="04">Built For The Floor</DeckEyebrow>
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

      {/* 05 — FEATURES & BENEFITS CAROUSEL */}
      <section style={{ padding: "70px 28px", maxWidth: 1080, margin: "0 auto", textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center" }}><DeckEyebrow n="05">Features &amp; Benefits</DeckEyebrow></div>
        <motion.h2 initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ fontSize: 28, fontWeight: 700, marginBottom: 8, letterSpacing: "-.01em" }}>
          Why manufacturers use CellMind
        </motion.h2>
        <p style={{ color: "var(--ink-mute)", fontSize: 13.5, marginBottom: 34 }}>
          Five capabilities, each mapped to the outcome it drives. Illustrated with the B1847/F07 scenario above —
          actual ROI depends on your volume, scrap cost and yield baseline.
        </p>
        <div style={{ position: "relative", maxWidth: 680, margin: "0 auto" }}>
          <div className="sun-glow" />
          <SolarGlitter />
          <div style={{ position: "relative", zIndex: 1 }}>
            <BenefitsSlider slides={BENEFITS} />
          </div>
        </div>
      </section>

      {/* 06 — THE ASK */}
      <section style={{ padding: "80px 28px 110px", textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center" }}><DeckEyebrow n="06">The Ask</DeckEyebrow></div>
        <SolarPanelGrid width={200} height={110} />
        <p style={{ maxWidth: "26ch", margin: "26px auto 24px", fontSize: 24, fontWeight: 700, letterSpacing: "-.01em" }}>
          "Find why it happened — and prevent the next batch from failing."
        </p>
        <Link className="btn btn-primary" to="/login" style={{ padding: "12px 22px", fontSize: 13.5 }}>Sign in to CellMind</Link>
      </section>
    </div>
  );
}
