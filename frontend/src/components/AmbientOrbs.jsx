export default function AmbientOrbs({ variant = "default" }) {
  const sets = {
    default: [
      { top: "-10%", left: "-8%", width: 420, height: 420, background: "var(--accent)", delay: "0s" },
      { top: "10%", right: "-10%", width: 380, height: 380, background: "var(--accent-2)", delay: "-6s" },
    ],
    wide: [
      { top: "-15%", left: "5%", width: 520, height: 520, background: "var(--accent)", delay: "0s" },
      { top: "20%", right: "-6%", width: 460, height: 460, background: "var(--accent-2)", delay: "-8s" },
      { bottom: "-20%", left: "30%", width: 400, height: 400, background: "var(--accent)", delay: "-3s" },
    ],
  };
  return (
    <div className="orb-field" aria-hidden="true">
      {sets[variant].map((o, i) => (
        <span
          key={i}
          className="orb"
          style={{
            top: o.top, left: o.left, right: o.right, bottom: o.bottom,
            width: o.width, height: o.height, background: o.background, animationDelay: o.delay,
          }}
        />
      ))}
    </div>
  );
}
