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
      style={{ maxWidth: 640, margin: "0 auto" }}
    >
      <div className="card" style={{ position: "relative", minHeight: 190, overflow: "hidden" }}>
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
            <div className="icon-badge" style={{ width: 42, height: 42, borderRadius: 12, marginBottom: 14 }}>
              <Icon className="icon" style={{ width: 20, height: 20 }} />
            </div>
            <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)", letterSpacing: ".05em", marginBottom: 6 }}>
              {slide.tag}
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 700, margin: "0 0 8px", color: "var(--ink)", textTransform: "none", letterSpacing: 0 }}>
              {slide.title}
            </h3>
            <p style={{ fontSize: 14, color: "var(--ink-soft)", margin: 0, maxWidth: "54ch" }}>{slide.body}</p>
          </motion.div>
        </AnimatePresence>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 14, marginTop: 18 }}>
        <button
          type="button" aria-label="Previous benefit" className="btn btn-secondary"
          style={{ padding: 8, borderRadius: "50%" }} onClick={() => go(index - 1, -1)}
        >
          <ChevronLeft className="icon" />
        </button>
        <div style={{ display: "flex", gap: 7 }}>
          {slides.map((s, i) => (
            <button
              key={s.tag}
              type="button"
              aria-label={`Go to benefit ${i + 1}: ${s.title}`}
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
          type="button" aria-label="Next benefit" className="btn btn-secondary"
          style={{ padding: 8, borderRadius: "50%" }} onClick={() => go(index + 1, 1)}
        >
          <ChevronRight className="icon" />
        </button>
      </div>
    </div>
  );
}
