# -*- coding: utf-8 -*-
"""Generates the 3-slide CellMind hackathon pitch deck (round 1)."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------- palette ----------
NAVY      = RGBColor(0x0B, 0x1E, 0x33)   # background
NAVY_2    = RGBColor(0x11, 0x2A, 0x46)   # panel
ACCENT    = RGBColor(0x3D, 0xD6, 0xC0)   # teal accent
ACCENT_2  = RGBColor(0xF2, 0xA6, 0x3D)   # amber accent (warning/defect)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
GREY      = RGBColor(0xAF, 0xC0, 0xD3)
LINE      = RGBColor(0x24, 0x3B, 0x57)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


def add_slide():
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    bg.shadow.inherit = False
    s.shapes._spTree.remove(bg._element)
    s.shapes._spTree.insert(2, bg._element)
    return s


def txt(slide, l, t, w, h, text, size, color=WHITE, bold=False, align=PP_ALIGN.LEFT,
        font="Segoe UI", italic=False, line_spacing=1.0, anchor=None):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    if anchor:
        tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = color
        r.font.name = font
    return box


def rect(slide, l, t, w, h, color, line_color=None, radius=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shape_type, l, t, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    if line_color:
        sh.line.color.rgb = line_color
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if radius:
        try:
            sh.adjustments[0] = 0.06
        except Exception:
            pass
    return sh


def bullet_block(slide, l, t, w, h, items, size=14, color=WHITE, gap=6, bold_lead=False):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.12
        if isinstance(item, tuple):
            lead, rest = item
            r1 = p.add_run(); r1.text = lead
            r1.font.size = Pt(size); r1.font.bold = True
            r1.font.color.rgb = ACCENT; r1.font.name = "Segoe UI"
            r2 = p.add_run(); r2.text = rest
            r2.font.size = Pt(size); r2.font.bold = False
            r2.font.color.rgb = color; r2.font.name = "Segoe UI"
        else:
            r = p.add_run(); r.text = "\u25B8  " + item
            r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = "Segoe UI"
    return box


def footer(slide, page):
    txt(slide, Inches(0.5), Inches(7.13), Inches(6), Inches(0.3),
        "CellMind  |  AI Quality Inspection for Solar Manufacturing", 9.5, GREY)
    txt(slide, Inches(12.2), Inches(7.13), Inches(0.7), Inches(0.3),
        f"{page} / 3", 9.5, GREY, align=PP_ALIGN.RIGHT)
    rect(slide, Inches(0), Inches(0), Inches(0.12), SLIDE_H, ACCENT)


def kicker(slide, text_):
    rect(slide, Inches(0.55), Inches(0.5), Inches(0.5), Inches(0.06), ACCENT)
    txt(slide, Inches(0.55), Inches(0.62), Inches(8), Inches(0.4), text_.upper(), 13, ACCENT, bold=True)


# =========================================================
# SLIDE 1 — PROBLEM + SOLUTION
# =========================================================
s1 = add_slide()
kicker(s1, "The Problem \u2192 The Solution")
txt(s1, Inches(0.55), Inches(0.95), Inches(11.5), Inches(0.9),
    "CellMind", 44, WHITE, bold=True)
txt(s1, Inches(0.55), Inches(1.62), Inches(11.5), Inches(0.5),
    "AI-powered quality inspection for solar panel manufacturing lines", 18, ACCENT)

# Problem panel
rect(s1, Inches(0.55), Inches(2.25), Inches(5.9), Inches(4.55), NAVY_2, LINE, radius=True)
txt(s1, Inches(0.9), Inches(2.5), Inches(5.2), Inches(0.4), "THE PROBLEM", 14, ACCENT_2, bold=True)
bullet_block(s1, Inches(0.9), Inches(2.95), Inches(5.2), Inches(3.7), [
    "Solar capacity is scaling fast, but panel QA is still largely manual \u2014 slow, inconsistent, and expensive at production volume.",
    "Undetected defects (micro-cracks, electrical damage, dust/bird-drop buildup, snow coverage) silently cut panel efficiency and can create fire/safety risk.",
    "Manual inspectors catch defects late \u2014 after cells are already boxed or installed \u2014 driving costly rework and warranty claims.",
    "Existing vision-AI demos classify a photo but stop there: no confidence safeguards, no root-cause context, no fit into a real factory workflow.",
], size=13.5, color=WHITE, gap=10)

# Solution panel
rect(s1, Inches(6.75, ) , Inches(2.25), Inches(6.03), Inches(4.55), NAVY_2, LINE, radius=True)
txt(s1, Inches(7.1), Inches(2.5), Inches(5.4), Inches(0.4), "THE SOLUTION", 14, ACCENT, bold=True)
bullet_block(s1, Inches(7.1), Inches(2.95), Inches(5.4), Inches(3.7), [
    ("Real trained CNN. ", "A ResNet18 classifier, fine-tuned on real solar-panel imagery, detects 6 defect classes in seconds per panel."),
    ("Confidence-gated automation. ", "Low-confidence predictions are auto-flagged for human review instead of guessing \u2014 AI that knows what it doesn't know."),
    ("Full factory workflow, not a toy demo. ", "Batches, lines, cameras, investigations, retraining, RBAC, and audit logs \u2014 built to plug into a real production line."),
    ("Root-cause reasoning. ", "Explains *why* a defect likely occurred (line, equipment, camera context) \u2014 not just what it is."),
], size=13.5, color=WHITE, gap=10)

footer(s1, 1)

# =========================================================
# SLIDE 2 — HOW IT WORKS / UNIQUENESS
# =========================================================
s2 = add_slide()
kicker(s2, "How It Works")
txt(s2, Inches(0.55), Inches(0.95), Inches(11.5), Inches(0.7),
    "Inside CellMind: Architecture & Differentiation", 30, WHITE, bold=True)

# Pipeline strip
pipeline = [
    ("1", "Camera / Upload", "Panel image captured on the line or uploaded via API"),
    ("2", "ResNet18 CNN", "2-phase transfer learning: frozen-backbone warmup \u2192 full fine-tune, cosine LR decay"),
    ("3", "Confidence Check", "High confidence \u2192 auto-classify.  Low confidence \u2192 flagged \u201cunknown pattern, manual review\u201d"),
    ("4", "Root-Cause Agents", "Inspection \u2192 Process \u2192 Context \u2192 Root-Cause agents explain the defect's likely origin"),
    ("5", "Action & Learning", "Investigation logged, severity scored, feeding future retraining runs"),
]
n = len(pipeline)
gap = Inches(0.18)
total_w = Inches(12.23)
box_w = Emu(int((total_w - gap * (n - 1)) / n))
x = Inches(0.55)
y = Inches(1.85)
box_h = Inches(1.75)
for i, (num, title, desc) in enumerate(pipeline):
    card = rect(s2, x, y, box_w, box_h, NAVY_2, LINE, radius=True)
    txt(s2, x + Inches(0.15), y + Inches(0.1), box_w - Inches(0.3), Inches(0.4), num, 20, ACCENT, bold=True)
    txt(s2, x + Inches(0.15), y + Inches(0.52), box_w - Inches(0.3), Inches(0.5), title, 12.5, WHITE, bold=True)
    txt(s2, x + Inches(0.15), y + Inches(0.98), box_w - Inches(0.3), Inches(0.7), desc, 9.5, GREY, line_spacing=1.05)
    if i < n - 1:
        arrow = s2.shapes.add_shape(MSO_SHAPE.CHEVRON, x + box_w - Emu(30000), y + box_h/2 - Inches(0.12), Inches(0.24), Inches(0.24))
        arrow.fill.solid(); arrow.fill.fore_color.rgb = ACCENT; arrow.line.fill.background(); arrow.shadow.inherit=False
    x = x + box_w + gap

# Metrics + uniqueness row
metrics_y = Inches(3.85)
rect(s2, Inches(0.55), metrics_y, Inches(3.9), Inches(2.95), NAVY_2, LINE, radius=True)
txt(s2, Inches(0.85), metrics_y + Inches(0.2), Inches(3.3), Inches(0.35), "MODEL, ON REAL DATA", 13, ACCENT_2, bold=True)
stat_pairs = [("82.4%", "Test accuracy"), ("0.822", "Macro F1-score"), ("6", "Defect classes detected")]
sy = metrics_y + Inches(0.65)
for val, label in stat_pairs:
    txt(s2, Inches(0.85), sy, Inches(1.6), Inches(0.55), val, 26, WHITE, bold=True)
    txt(s2, Inches(0.85), sy + Inches(0.58), Inches(3.3), Inches(0.3), label, 11.5, GREY)
    sy += Inches(0.75)

rect(s2, Inches(4.65), metrics_y, Inches(3.95), Inches(2.95), NAVY_2, LINE, radius=True)
txt(s2, Inches(4.95), metrics_y + Inches(0.2), Inches(3.4), Inches(0.35), "WHAT MAKES IT UNIQUE", 13, ACCENT, bold=True)
bullet_block(s2, Inches(4.95), metrics_y + Inches(0.62), Inches(3.5), Inches(2.2), [
    "Safety-first OOD detection \u2014 refuses to force a wrong call",
    "Explains root cause, not just a label",
    "End-to-end factory workflow: batches, retraining, audit trail",
    "Honest, real-data metrics \u2014 not a mocked demo",
], size=12, gap=8)

rect(s2, Inches(8.85), metrics_y, Inches(3.93), Inches(2.95), NAVY_2, LINE, radius=True)
txt(s2, Inches(9.15), metrics_y + Inches(0.2), Inches(3.4), Inches(0.35), "TECH STACK", 13, ACCENT_2, bold=True)
bullet_block(s2, Inches(9.15), metrics_y + Inches(0.62), Inches(3.45), Inches(2.2), [
    ("Frontend  ", "React + Vite"),
    ("Backend  ", "FastAPI + SQLite"),
    ("ML  ", "PyTorch, ResNet18 (transfer learning)"),
    ("API  ", "~30 REST endpoints incl. live inference"),
], size=12, gap=8)

footer(s2, 2)

# =========================================================
# SLIDE 3 — IMPACT + UNIQUENESS + VISION
# =========================================================
s3 = add_slide()
kicker(s3, "Impact & What's Next")
txt(s3, Inches(0.55), Inches(0.95), Inches(11.5), Inches(0.7),
    "Why It Matters \u2014 and Where It's Going", 30, WHITE, bold=True)

# Impact stats row
impact_stats = [
    ("5\u201325%", "Efficiency loss caused by\nundetected panel defects"),
    ("Minutes", "Inspection time per panel,\nvs. manual visual checks"),
    ("Shift-left QA", "Defects caught in production,\nnot after installation"),
    ("Human + AI", "Confidence gating keeps a person\nin the loop \u2014 trustable automation"),
]
x = Inches(0.55)
card_w = Inches(2.955)
gapx = Inches(0.15)
y = Inches(1.85)
for val, label in impact_stats:
    rect(s3, x, y, card_w, Inches(1.5), NAVY_2, LINE, radius=True)
    txt(s3, x + Inches(0.15), y + Inches(0.18), card_w - Inches(0.3), Inches(0.55), val, 24, ACCENT, bold=True)
    txt(s3, x + Inches(0.15), y + Inches(0.8), card_w - Inches(0.3), Inches(0.65), label, 10.5, GREY, line_spacing=1.1)
    x += card_w + gapx

# Two column: uniqueness recap + roadmap
col_y = Inches(3.6)
rect(s3, Inches(0.55), col_y, Inches(6.03), Inches(3.2), NAVY_2, LINE, radius=True)
txt(s3, Inches(0.9), col_y + Inches(0.22), Inches(5.3), Inches(0.4), "NOT ANOTHER IMAGE CLASSIFIER DEMO", 13.5, ACCENT, bold=True)
bullet_block(s3, Inches(0.9), col_y + Inches(0.72), Inches(5.4), Inches(2.4), [
    ("Safety over accuracy theatre \u2014 ", "when the model is unsure, it says so, instead of a confident-sounding wrong answer."),
    ("Root cause, not just a label \u2014 ", "multi-agent reasoning links a defect back to the line, equipment, or camera behind it."),
    ("Deployment-ready shape \u2014 ", "RBAC, audit logs, retraining runs and investigations mean this fits a real factory, not just a Kaggle notebook."),
], size=12.5, gap=10)

rect(s3, Inches(6.75), col_y, Inches(6.03), Inches(3.2), NAVY_2, LINE, radius=True)
txt(s3, Inches(7.1), col_y + Inches(0.22), Inches(5.3), Inches(0.4), "ROADMAP", 13.5, ACCENT_2, bold=True)
bullet_block(s3, Inches(7.1), col_y + Inches(0.72), Inches(5.4), Inches(2.4), [
    "Grad-CAM visual explainability \u2014 highlight the exact defect region on the panel",
    "Live camera-stream integration on the production line",
    "Predictive maintenance: flag equipment before defect rates spike, using trend data already captured",
], size=12.5, gap=10)

footer(s3, 3)

prs.save(r"C:\Users\swathy.c\Downloads\cellmind\CellMind_Hackathon_Pitch.pptx")
print("Saved.")
