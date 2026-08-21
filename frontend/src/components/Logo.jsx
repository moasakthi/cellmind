export default function Logo({ size = 22, className }) {
  return (
    <img
      src="/logo-mark.png"
      alt="CellMind"
      width={size}
      height={size}
      className={className}
      style={{ objectFit: "contain", flex: "none" }}
    />
  );
}
