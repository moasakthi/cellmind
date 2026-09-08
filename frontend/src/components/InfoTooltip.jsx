import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";

const POPUP_WIDTH = 238;

/**
 * Small "i" affordance that reveals what a widget is and the value insight
 * to read from it. Click/keyboard-toggled (not hover-only) so it works for
 * touch and screen-reader users alike.
 *
 * Renders the popup via a portal to document.body, positioned from the
 * button's viewport rect. Cards use backdrop-filter, which creates a new
 * stacking context per card — an absolutely-positioned popup confined to
 * one card's subtree can never out-stack a sibling card painted after it,
 * no matter its z-index. Portaling sidesteps that entirely.
 */
export default function InfoTooltip({ title, children, align = "left" }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState(null);
  const btnRef = useRef(null);
  const popRef = useRef(null);

  function computePos() {
    const r = btnRef.current.getBoundingClientRect();
    let left = align === "right" ? r.right - POPUP_WIDTH : r.left;
    left = Math.min(Math.max(left, 8), window.innerWidth - POPUP_WIDTH - 8);
    setPos({ top: r.bottom + 8, left });
  }

  function toggle() {
    if (!open) computePos();
    setOpen((v) => !v);
  }

  useEffect(() => {
    if (!open) return;
    function onDocDown(e) {
      if (btnRef.current?.contains(e.target)) return;
      if (popRef.current?.contains(e.target)) return;
      setOpen(false);
    }
    function onKey(e) {
      if (e.key === "Escape") setOpen(false);
    }
    function onDismiss() {
      setOpen(false);
    }
    document.addEventListener("mousedown", onDocDown);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onDismiss, true);
    window.addEventListener("resize", onDismiss);
    return () => {
      document.removeEventListener("mousedown", onDocDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onDismiss, true);
      window.removeEventListener("resize", onDismiss);
    };
  }, [open]);

  return (
    <span className="info-wrap">
      <button
        ref={btnRef}
        type="button"
        className="info-btn"
        aria-expanded={open}
        aria-label={`About ${title}`}
        onClick={toggle}
      >
        <Info className="icon" style={{ width: 13, height: 13 }} />
      </button>
      {open && pos && createPortal(
        <div
          ref={popRef}
          className="info-pop"
          role="tooltip"
          style={{ position: "fixed", top: pos.top, left: pos.left }}
        >
          <div className="info-pop-title">{title}</div>
          <div className="info-pop-body">{children}</div>
        </div>,
        document.body
      )}
    </span>
  );
}
