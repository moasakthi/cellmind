import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";

const variants = {
  enter: (dir) => ({ x: dir >= 0 ? 40 : -40, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir) => ({ x: dir >= 0 ? -40 : 40, opacity: 0 }),
};

export default function BenefitsSlider({ slides, interval = 5500 }) {
  const [[index, dir], setState] = useState([0, 0]);
  const hovering = useRef(false);
  const reduceMotion =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function go(nextIndex, direction) {
    setState([((nextIndex % slides.length) + slides.length) % slides.length, direction]);
  }

  useEffect(() => {
    if (reduceMotion) return;
    const id = setInterval(() => {
      if (!hovering.current) go(index + 1, 1);
    }, interval);
    return () => clearInterval(id);
  }, [index, reduceMotion]); // eslint-disable-line react-hooks/exhaustive-deps

  const slide = slides[index];
  const Icon = slide.icon;

  return (
    <div
      onMouseEnter={() => (hovering.current = true)}
      onMouseLeave={() => (hovering.current = false)}
      style={{ maxWidth: 680, margin: "0 auto" }}
    >
      <div className="card" style={{ position: "relative", minHeight: 220, overflow: "hidden", textAlign: "left" }}>
        <div className="mono" style={{ position: "absolute", top: 18, right: 20, fontSize: 11, color: "var(--ink-mute)" }}>
          {String(index + 1).padStart(2, "0")} / {String(slides.length).padStart(2, "0")}
        </div>
        <AnimatePresence mode="wait" custom={dir} initial={false}>
          <motion.div
            key={index}
            custom={dir}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ duration: reduceMotion ? 0 : 0.35, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="icon-badge" style={{ width: 42, height: 42, borderRadius: 12, marginBottom: 16 }}>
              <Icon className="icon" style={{ width: 20, height: 20 }} />
            </div>
            <div className="mono" style={{ fontSize: 10, color: "var(--ink-mute)", letterSpacing: ".06em", marginBottom: 8 }}>
              {slide.tag}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "6px 12px", alignItems: "baseline" }}>
              <span className="chip chip-info" style={{ fontSize: 9.5 }}>FEATURE</span>
              <h3 style={{ fontSize: 16.5, fontWeight: 700, margin: 0, color: "var(--ink)" }}>{slide.feature}</h3>
              <span className="chip chip-good" style={{ fontSize: 9.5 }}>BENEFIT</span>
              <p style={{ fontSize: 14, color: "var(--ink-soft)", margin: 0, maxWidth: "50ch" }}>{slide.benefit}</p>
            </div>
          </motion.div>
        </AnimatePresence>

        {!reduceMotion && (
          <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 2, background: "var(--line-soft)" }}>
            <motion.div
              key={`progress-${index}`}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: interval / 1000, ease: "linear" }}
              style={{ height: "100%", background: "var(--accent-grad)", transformOrigin: "0% 50%" }}
            />
          </div>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 14, marginTop: 18 }}>
        <button
          type="button" aria-label="Previous" className="btn btn-secondary"
          style={{ padding: 8, borderRadius: "50%" }} onClick={() => go(index - 1, -1)}
        >
          <ChevronLeft className="icon" />
        </button>
        <div style={{ display: "flex", gap: 7 }}>
          {slides.map((s, i) => (
            <button
              key={s.tag}
              type="button"
              aria-label={`Go to slide ${i + 1}: ${s.feature}`}
              aria-current={i === index}
              onClick={() => go(i, i > index ? 1 : -1)}
              style={{
                width: i === index ? 20 : 7, height: 7, borderRadius: 100, border: "none", padding: 0, cursor: "pointer",
                background: i === index ? "var(--accent-grad)" : "var(--line)", transition: "width 200ms, background 200ms",
              }}
            />
          ))}
        </div>
        <button
          type="button" aria-label="Next" className="btn btn-secondary"
          style={{ padding: 8, borderRadius: "50%" }} onClick={() => go(index + 1, 1)}
        >
          <ChevronRight className="icon" />
        </button>
      </div>
    </div>
  );
}
