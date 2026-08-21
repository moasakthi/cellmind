// Decorative sun/sky sparkle field for the Features & Benefits slider.
// Fixed, deterministic positions (no Math.random on render) so it never reshuffles on re-render.
const SPARKLES = [
  { top: "-4%", left: "4%", size: 20, color: "gold", delay: "0s", duration: "2.4s" },
  { top: "8%", left: "-3%", size: 13, color: "sky", delay: "-1.1s", duration: "3.1s" },
  { top: "70%", left: "-5%", size: 17, color: "gold", delay: "-0.4s", duration: "2.8s" },
  { top: "92%", left: "6%", size: 12, color: "cream", delay: "-2s", duration: "2.2s" },
  { top: "-6%", left: "28%", size: 12, color: "sky", delay: "-0.8s", duration: "2.6s" },
  { top: "-8%", left: "72%", size: 15, color: "gold", delay: "-1.6s", duration: "3.3s" },
  { top: "6%", left: "102%", size: 18, color: "sky", delay: "-0.2s", duration: "2.9s" },
  { top: "48%", left: "104%", size: 13, color: "cream", delay: "-2.3s", duration: "2.5s" },
  { top: "88%", left: "98%", size: 16, color: "gold", delay: "-1.3s", duration: "3s" },
  { top: "96%", left: "62%", size: 12, color: "sky", delay: "-0.6s", duration: "2.7s" },
  { top: "100%", left: "34%", size: 14, color: "cream", delay: "-1.8s", duration: "3.2s" },
  { top: "34%", left: "-7%", size: 11, color: "sky", delay: "-2.5s", duration: "2.3s" },
];

const COLOR_HEX = { gold: "#FFC24B", sky: "#5FD0F3", cream: "#FFDE9E" };

function SparkleMark({ size, color }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M12 0 L16 8 L24 12 L16 16 L12 24 L8 16 L0 12 L8 8 Z" fill={color} />
    </svg>
  );
}

export default function SolarGlitter() {
  return (
    <div className="glitter-field" aria-hidden="true">
      {SPARKLES.map((s, i) => {
        const hex = COLOR_HEX[s.color];
        return (
          <span
            key={i}
            className="glitter"
            style={{
              top: s.top, left: s.left, animationDelay: s.delay, animationDuration: s.duration,
              filter: `drop-shadow(0 0 6px ${hex})`,
            }}
          >
            <SparkleMark size={s.size} color={hex} />
          </span>
        );
      })}
    </div>
  );
}
