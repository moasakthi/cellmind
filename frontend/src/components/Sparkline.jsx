export default function Sparkline({ points, width = 90, height = 28, color = "var(--accent)" }) {
  const max = Math.max(...points), min = Math.min(...points);
  const range = max - min || 1;
  const step = width / (points.length - 1);
  const coords = points.map((p, i) => `${i * step},${height - ((p - min) / range) * height}`).join(" ");
  const last = points[points.length - 1];
  const lastY = height - ((last - min) / range) * height;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={coords} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.85" />
      <circle cx={width} cy={lastY} r="2.5" fill={color} />
    </svg>
  );
}
