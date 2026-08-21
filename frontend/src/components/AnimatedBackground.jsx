// Persistent, fixed, full-viewport animated background: dot-grid pan + drifting gradient orbs.
// Sits at z-index:-1 (see .page-bg in tokens.css) so it never needs page content to opt in via z-index.
export default function AnimatedBackground() {
  return (
    <div className="page-bg" aria-hidden="true">
      <div className="bg-grid" />
      <span className="bg-orb bg-orb-a" />
      <span className="bg-orb bg-orb-b" />
      <span className="bg-orb bg-orb-c" />
    </div>
  );
}
