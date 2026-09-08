import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from ai_bridge import (
    AIUnavailableError, CHAT_SYSTEM_PROMPT, chat_completion, current_model,
    generate_dashboard_insights, generate_recommendation,
)
from chat_tools import CHAT_TOOL_SCHEMAS, execute_tool
from database import Base, engine, get_db
from ml_bridge import classify
from models import (
    AiInsight, AuditLogEntry, AutonomyConfig, Batch, Camera, Cell, DefectTaxonomyEntry,
    Equipment, Investigation, ModelVersion, ProcessRecord, Recommendation,
    RetrainingRun, Role, SafetyConstraint, TaxonomyVersion, User,
)
from schemas import (
    ApprovalDecisionRequest, AutonomyConfigIn, CameraCreateRequest, ChatRequest,
    InvestigationCreateRequest, LoginRequest, RetrainingRunCreateRequest,
    RoleAssignRequest, SafetyConstraintIn, SimulationRequest,
    TaxonomyVersionCreateRequest,
)
from serialization import row_to_dict, rows_to_dicts

Base.metadata.create_all(bind=engine)

BACKEND_DIR = Path(__file__).parent
STATIC_DIR = BACKEND_DIR / "static"
(STATIC_DIR / "images").mkdir(parents=True, exist_ok=True)

ADMIN_PERMS = {"manage_cameras", "configure_taxonomy", "manage_rbac"}

app = FastAPI(title="CellMind API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def user_name(db, user_id):
    user = db.get(User, user_id)
    return user.name if user else user_id


def user_permissions(db, user_id):
    user = db.get(User, user_id)
    if not user:
        return []
    role = db.get(Role, user.role_id)
    return role.permissions if role else []


def require_permission(db, user_id, permission):
    if permission not in user_permissions(db, user_id):
        raise HTTPException(403, f"{user_name(db, user_id)} lacks the '{permission}' permission.")


def require_admin_permission(db, user_id):
    if not set(user_permissions(db, user_id)) & ADMIN_PERMS:
        raise HTTPException(403, f"{user_name(db, user_id)} lacks Platform Administrator permissions.")


def audit(db, actor, action, target_type, target_id):
    db.add(AuditLogEntry(
        event_id=str(uuid4()), timestamp=now_iso(), actor=actor, tenant_id="t1",
        action=action, target_type=target_type, target_id=str(target_id),
        before_state=None, after_state=None,
    ))
    db.commit()


def paginate(rows, page, page_size):
    total = len(rows)
    start = (page - 1) * page_size
    return {"page": page, "pageSize": page_size, "total": total,
            "items": rows_to_dicts(rows[start:start + page_size])}


def next_taxonomy_version(existing_ids):
    best = 1.3
    for v in existing_ids:
        try:
            best = max(best, float(v.lstrip("vV")))
        except ValueError:
            continue
    return f"v{round(best + 0.1, 1)}"


def synthesize_agents(db: Session, batch: Batch, cell: Optional[Cell]):
    if cell:
        inspection = {
            "agentName": "InspectionAgent",
            "result": {"defectProbability": cell.defect_probability, "severity": cell.severity},
            "confidence": cell.confidence,
            "confidenceBand": "HIGH" if cell.confidence >= 0.85 else "MEDIUM",
            "evidence": [{
                "sourceType": "image", "sourceRef": cell.cell_id,
                "description": f"Defect probability {round(cell.defect_probability * 100)}%, severity {cell.severity.lower()}.",
            }],
            "dataGaps": [],
            "oodFlag": cell.ood_flag,
        }
    else:
        inspection = {
            "agentName": "InspectionAgent", "result": {"defectProbability": None, "severity": None},
            "confidence": 0.3, "confidenceBand": "LOW", "evidence": [],
            "dataGaps": ["No target cell available for this batch."], "oodFlag": False,
        }

    proc_rows = db.query(ProcessRecord).filter(ProcessRecord.batch_id == batch.batch_id).all()
    anomalies = [{"parameter": "temperature", "equipmentId": p.equipment_id,
                  "baseline": 800.0, "value": p.temperature} for p in proc_rows]
    process = {
        "agentName": "ProcessAgent",
        "result": {"anomalies": anomalies},
        "confidence": 0.8 if anomalies else 0.4,
        "confidenceBand": "HIGH" if anomalies else "LOW",
        "evidence": [{"sourceType": "process_param", "sourceRef": f"{p.equipment_id} {p.stage} stage",
                       "description": "Process parameter recorded for this batch."} for p in proc_rows[:2]],
        "dataGaps": [] if proc_rows else ["No process records for this batch."],
        "oodFlag": False,
    }

    similar = (db.query(Batch)
               .filter(Batch.line_id == batch.line_id, Batch.batch_id != batch.batch_id,
                       Batch.risk_level == "HIGH").all())
    context = {
        "agentName": "ContextAgent",
        "result": {"historicalMatches": [b.batch_id for b in similar]},
        "confidence": 0.75 if similar else 0.4,
        "confidenceBand": "MEDIUM" if similar else "LOW",
        "evidence": [{"sourceType": "historical_incident", "sourceRef": f"Batch {b.batch_id}",
                       "description": "Similar high-risk batch on the same line."} for b in similar[:2]],
        "dataGaps": [],
        "oodFlag": False,
    }

    equip_ids = {p.equipment_id for p in proc_rows}
    root_cause_result, evidence = None, []
    if equip_ids:
        equips = db.query(Equipment).filter(Equipment.equipment_id.in_(equip_ids)).all()
        worst = max(equips, key=lambda e: (e.defective_units / e.units_produced if e.units_produced else 0),
                    default=None)
        if worst and worst.units_produced:
            rate = round(100 * worst.defective_units / worst.units_produced, 1)
            root_cause_result = {"probableCause": f"{worst.equipment_id} process variation",
                                  "equipmentRate": rate, "equipmentShare": rate}
            evidence.append({"sourceType": "equipment", "sourceRef": worst.equipment_id,
                              "description": f"Defect rate {rate}% on {worst.equipment_id}."})
    root_cause = {
        "agentName": "RootCauseAgent",
        "result": root_cause_result or {"probableCause": "Insufficient data", "equipmentRate": None, "equipmentShare": None},
        "confidence": 0.85 if root_cause_result else 0.3,
        "confidenceBand": "HIGH" if root_cause_result else "LOW",
        "evidence": evidence,
        "dataGaps": [] if root_cause_result else ["No equipment/process correlation available."],
        "oodFlag": False,
    }

    return {"inspection": inspection, "process": process, "context": context, "rootCause": root_cause}


# ---------- Auth ----------

@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(email)).first()
    if not user or not payload.password:
        raise HTTPException(401, "Invalid email or password.")
    role = db.get(Role, user.role_id)
    return {"accessToken": f"mock-{user.user_id}", "tokenType": "Bearer", "expiresIn": 3600,
            "user": {**row_to_dict(user), "role": row_to_dict(role)}}


@app.get("/auth/sso/callback")
def sso_callback(code: str, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(401, "No SSO-linked user available.")
    role = db.get(Role, user.role_id)
    return {"accessToken": f"mock-{user.user_id}", "tokenType": "Bearer", "expiresIn": 3600,
            "user": {**row_to_dict(user), "role": role and row_to_dict(role)}}


@app.get("/users/me")
def me(as_user: str = "u-jalvarez", db: Session = Depends(get_db)):
    user = db.get(User, as_user)
    if not user:
        raise HTTPException(404, "unknown user")
    role = db.get(Role, user.role_id)
    return {**row_to_dict(user), "role": row_to_dict(role)}


# ---------- Batches ----------

@app.get("/batches")
def list_batches(line_id: Optional[str] = Query(None, alias="lineId"),
                  risk_level: Optional[str] = Query(None, alias="riskLevel"),
                  db: Session = Depends(get_db)):
    q = db.query(Batch)
    if line_id:
        q = q.filter(Batch.line_id == line_id)
    if risk_level:
        q = q.filter(Batch.risk_level == risk_level)
    return rows_to_dicts(q.all())


@app.get("/batches/{batch_id}")
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    return row_to_dict(batch)


@app.get("/batches/{batch_id}/cells")
def batch_cells(batch_id: str, page: int = 1, page_size: int = Query(25, alias="pageSize"),
                 db: Session = Depends(get_db)):
    rows = db.query(Cell).filter(Cell.batch_id == batch_id).all()
    return paginate(rows, page, page_size)


@app.get("/batches/{batch_id}/process")
def batch_process(batch_id: str, db: Session = Depends(get_db)):
    return rows_to_dicts(db.query(ProcessRecord).filter(ProcessRecord.batch_id == batch_id).all())


# ---------- Cells ----------

@app.get("/cells/{cell_id}")
def get_cell(cell_id: str, db: Session = Depends(get_db)):
    cell = db.get(Cell, cell_id)
    if not cell:
        raise HTTPException(404, "cell not found")
    return row_to_dict(cell)


def confidence_band(confidence: float) -> str:
    return "HIGH" if confidence >= 0.85 else ("MEDIUM" if confidence >= 0.6 else "LOW")


def build_inspection_response(result: dict, ref_id: str) -> dict:
    """Shared InspectionAgent-style response for both the seeded-cell and
    uploaded-photo classification paths (FR-02, FR-14, FR-15)."""
    if result["oodFlag"]:
        description = ("Unknown defect pattern detected — manual inspection required "
                        f"(top-class confidence {round(result['confidence'] * 100)}% is below the "
                        "out-of-distribution threshold; FR-15).")
    else:
        description = (f"Classifier predicts '{result['label']}' with "
                        f"{round(result['confidence'] * 100)}% confidence "
                        f"(defect probability {round(result['defectProbability'] * 100)}%).")

    return {
        "agentName": "InspectionAgent",
        "result": {"defectProbability": result["defectProbability"], "severity": result["severity"],
                    "label": result["label"]},
        "confidence": result["confidence"], "confidenceBand": confidence_band(result["confidence"]),
        "evidence": [{"sourceType": "image", "sourceRef": ref_id, "description": description}],
        "dataGaps": [], "oodFlag": result["oodFlag"],
    }


@app.post("/cells/{cell_id}/inspect")
def inspect_cell(cell_id: str, db: Session = Depends(get_db)):
    cell = db.get(Cell, cell_id)
    if not cell:
        raise HTTPException(404, "cell not found")

    image_path = BACKEND_DIR / cell.image_path.lstrip("/")
    try:
        result = classify(image_path)
    except FileNotFoundError:
        raise HTTPException(503, "Fault classifier model not available — run `python ml/train.py` "
                                  "in ml/ to generate artifacts/best_model.pt.")
    except OSError:
        raise HTTPException(422, "Image quality insufficient — unable to read EL scan (FR-03).")

    cell.defect_probability = result["defectProbability"]
    cell.severity = result["severity"]
    cell.confidence = result["confidence"]
    cell.taxonomy_id = result["taxonomyId"]
    cell.ood_flag = result["oodFlag"]
    db.add(cell); db.commit()

    return build_inspection_response(result, cell.cell_id)


@app.post("/inference/predict")
async def predict_uploaded_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(422, "Uploaded file must be an image.")

    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        result = classify(tmp_path)
    except FileNotFoundError:
        raise HTTPException(503, "Fault classifier model not available — run `python ml/train.py` "
                                  "in ml/ to generate artifacts/best_model.pt.")
    except OSError:
        raise HTTPException(422, "Image quality insufficient — unable to read uploaded image (FR-03).")
    finally:
        tmp_path.unlink(missing_ok=True)

    return build_inspection_response(result, file.filename or "upload")


# ---------- Process & Equipment ----------

@app.get("/equipment")
def list_equipment(db: Session = Depends(get_db)):
    rows = db.query(Equipment).all()
    out = []
    total_defects = sum(e.defective_units for e in rows) or 1
    for e in rows:
        d = row_to_dict(e)
        d["defectRatePct"] = round(100 * e.defective_units / e.units_produced, 1) if e.units_produced else 0
        d["shareOfDefectsPct"] = round(100 * e.defective_units / total_defects, 1)
        out.append(d)
    return out


@app.get("/equipment/{equipment_id}")
def get_equipment(equipment_id: str, db: Session = Depends(get_db)):
    equipment = db.get(Equipment, equipment_id)
    if not equipment:
        raise HTTPException(404, "equipment not found")
    return row_to_dict(equipment)


# ---------- Cameras ----------

@app.get("/cameras")
def list_cameras(db: Session = Depends(get_db)):
    return rows_to_dicts(db.query(Camera).all())


@app.post("/cameras", status_code=201)
def create_camera(payload: CameraCreateRequest, db: Session = Depends(get_db)):
    acting = payload.acting_user_id or "u-rchen"
    require_permission(db, acting, "manage_cameras")
    if payload.camera_type == "EL" and not payload.el_capable:
        raise HTTPException(422, "EL-capability must be confirmed before this camera can serve EL inspection (REQ-18.1).")
    camera = Camera(
        camera_id=f"CAM-{uuid4().hex[:6].upper()}", tenant_id="t1", camera_type=payload.camera_type,
        el_capable=payload.el_capable, model=payload.model, line_id=payload.line_id,
        station_id=payload.station_id, stream_url=payload.stream_url, status="ONLINE",
        last_frame_at=now_iso(), retention_days=payload.retention_days,
    )
    db.add(camera); db.commit(); db.refresh(camera)
    audit(db, acting, "register_camera", "camera", camera.camera_id)
    return row_to_dict(camera)


@app.get("/cameras/{camera_id}")
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, "camera not found")
    return row_to_dict(camera)


@app.get("/cameras/{camera_id}/health")
def camera_health(camera_id: str, db: Session = Depends(get_db)):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, "camera not found")
    return {"cameraId": camera.camera_id, "status": camera.status, "lastFrameAt": camera.last_frame_at,
            "consecutiveMissedHeartbeats": 3 if camera.status != "ONLINE" else 0}


# ---------- Investigations ----------

@app.get("/investigations")
def list_investigations(page: int = 1, page_size: int = Query(25, alias="pageSize"),
                         db: Session = Depends(get_db)):
    rows = db.query(Investigation).order_by(Investigation.created_at.desc()).all()
    return paginate(rows, page, page_size)


@app.post("/investigations", status_code=202)
def create_investigation(payload: InvestigationCreateRequest, db: Session = Depends(get_db)):
    batch = db.get(Batch, payload.batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")

    cameras = db.query(Camera).filter(Camera.line_id == batch.line_id).all()
    if cameras and all(c.status == "OFFLINE" for c in cameras):
        raise HTTPException(503, "Agent Hub unavailable — production is not blocked by this response (BR-11, REQ-20.4).")

    cell = None
    if payload.cell_id:
        cell = db.get(Cell, payload.cell_id)
        if not cell:
            raise HTTPException(404, "cell not found")
    else:
        cell = (db.query(Cell).filter(Cell.batch_id == batch.batch_id)
                .order_by(Cell.defect_probability.desc()).first())

    agents = synthesize_agents(db, batch, cell)
    status = "COMPLETE" if cell and agents["rootCause"]["result"]["probableCause"] != "Insufficient data" else "PARTIAL"

    inv = Investigation(
        investigation_id=f"inv-{uuid4().hex[:8]}", batch_id=batch.batch_id,
        cell_id=cell.cell_id if cell else None, status=status, agents=agents, created_at=now_iso(),
    )
    db.add(inv); db.commit(); db.refresh(inv)
    return row_to_dict(inv)


@app.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(404, "investigation not found")
    return row_to_dict(inv)


# ---------- Recommendations ----------

@app.get("/recommendations/{investigation_id}")
def get_recommendation(investigation_id: str, db: Session = Depends(get_db)):
    rec = db.query(Recommendation).filter(Recommendation.investigation_id == investigation_id).first()
    if not rec:
        raise HTTPException(404, "no recommendation for this investigation")
    return row_to_dict(rec)


def _referenced_equipment_ids(agents: dict) -> set:
    ids = set()
    for agent in agents.values():
        for ev in agent.get("evidence", []):
            if ev.get("sourceType") == "equipment":
                ids.add(ev["sourceRef"])
        result = agent.get("result") or {}
        for anomaly in result.get("anomalies", []) if isinstance(result, dict) else []:
            if "equipmentId" in anomaly:
                ids.add(anomaly["equipmentId"])
    return ids


@app.post("/investigations/{investigation_id}/recommendation")
def generate_investigation_recommendation(investigation_id: str,
                                           acting_user_id: Optional[str] = Query(None, alias="actingUserId"),
                                           db: Session = Depends(get_db)):
    inv = db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(404, "investigation not found")
    batch = db.get(Batch, inv.batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    acting = acting_user_id or "u-jalvarez"

    cell = db.get(Cell, inv.cell_id) if inv.cell_id else None
    taxonomy_entry = db.get(DefectTaxonomyEntry, cell.taxonomy_id) if cell and cell.taxonomy_id else None
    equipment_ids = _referenced_equipment_ids(inv.agents)
    equipment_rows = (db.query(Equipment).filter(Equipment.equipment_id.in_(equipment_ids)).all()
                       if equipment_ids else [])

    context = {
        "batch": {"batchId": batch.batch_id, "lineId": batch.line_id, "yieldPct": batch.yield_pct,
                  "defectRatePct": batch.defect_rate, "riskLevel": batch.risk_level},
        "agents": inv.agents,
        "taxonomyCategory": taxonomy_entry.category if taxonomy_entry else None,
        "taxonomySuggestedAction": taxonomy_entry.suggested_action if taxonomy_entry else None,
        "equipment": [{"equipmentId": e.equipment_id, "equipmentType": e.equipment_type,
                        "defectRatePct": round(100 * e.defective_units / e.units_produced, 1)
                                          if e.units_produced else 0} for e in equipment_rows],
    }

    try:
        result = generate_recommendation(context)
    except AIUnavailableError as e:
        raise HTTPException(503, f"AI recommendation engine unavailable: {e}")

    autonomy_cfg = db.get(AutonomyConfig, batch.line_id)
    autonomy_level = autonomy_cfg.autonomy_level if autonomy_cfg else "A"

    ranked_actions = [
        {"actionId": f"act-{uuid4().hex[:6]}", "rank": i + 1, "title": a.get("title", "Untitled action"),
         "cost": a.get("cost", "Medium"), "expectedImprovementPct": a.get("expectedImprovementPct", 0),
         "downtimeHours": a.get("downtimeHours", 0), "riskScore": a.get("riskScore", 0.2),
         "preSelected": i == 0 and autonomy_level == "B", "filtered": False, "filterReason": None}
        for i, a in enumerate(result.get("actions", [])[:4])
    ]
    simulation = compute_simulation(batch, reduce=True)
    reasoning = result.get("rootCauseNarrative")

    existing = db.query(Recommendation).filter(Recommendation.investigation_id == investigation_id).first()
    if existing:
        existing.authored_by = "system:AIRecommendationAgent"
        existing.autonomy_level = autonomy_level
        existing.ranked_actions = ranked_actions
        existing.filtered_actions = []
        existing.simulation = simulation
        existing.reasoning = reasoning
        existing.created_at = now_iso()
        rec = existing
    else:
        rec = Recommendation(
            recommendation_id=f"rec-{uuid4().hex[:6]}", investigation_id=investigation_id,
            authored_by="system:AIRecommendationAgent", autonomy_level=autonomy_level,
            ranked_actions=ranked_actions, filtered_actions=[], simulation=simulation,
            approval=None, reasoning=reasoning, created_at=now_iso(),
        )
    db.add(rec); db.commit(); db.refresh(rec)
    audit(db, acting, "generate_ai_recommendation", "recommendation", rec.recommendation_id)
    return row_to_dict(rec)


@app.post("/recommendations/{recommendation_id}/approve")
def approve_recommendation(recommendation_id: str, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    rec = db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(404, "recommendation not found")

    acting = payload.acting_user_id or "u-jalvarez"
    if not any(p.startswith("approve_") for p in user_permissions(db, acting)):
        raise HTTPException(403, f"{user_name(db, acting)}'s role cannot approve recommendations.")
    if acting == rec.authored_by:
        raise HTTPException(409, "Requester and approver must be distinct users (BR-10).")

    approval = {
        "approvalId": str(uuid4()), "targetType": "recommendation", "targetId": recommendation_id,
        "requestedBy": rec.authored_by, "approver": acting, "decision": payload.decision,
        "rationaleOverride": payload.rationale_override, "decidedAt": now_iso(),
    }
    rec.approval = approval
    db.add(rec); db.commit()
    audit(db, acting, "approve_recommendation", "recommendation", recommendation_id)
    return approval


# ---------- AI Insights ----------

@app.post("/insights")
def generate_insights(acting_user_id: Optional[str] = Query(None, alias="actingUserId"),
                       db: Session = Depends(get_db)):
    acting = acting_user_id or "u-jalvarez"

    batches = db.query(Batch).all()
    equipment_rows = db.query(Equipment).all()
    cameras = db.query(Camera).all()
    recent_audit = db.query(AuditLogEntry).order_by(AuditLogEntry.timestamp.desc()).limit(8).all()

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for b in batches:
        risk_counts[b.risk_level] = risk_counts.get(b.risk_level, 0) + 1

    total_defects = sum(e.defective_units for e in equipment_rows) or 1
    equipment_summary = [
        {"equipmentId": e.equipment_id,
         "defectRatePct": round(100 * e.defective_units / e.units_produced, 1) if e.units_produced else 0,
         "shareOfDefectsPct": round(100 * e.defective_units / total_defects, 1)}
        for e in equipment_rows
    ]

    lines = {}
    for b in batches:
        lines.setdefault(b.line_id, []).append(b.defect_rate)
    line_summary = [{"lineId": lid, "avgDefectRatePct": round(sum(rates) / len(rates), 1), "batchCount": len(rates)}
                     for lid, rates in lines.items()]

    cam_by_line = {}
    for c in cameras:
        cam_by_line.setdefault(c.line_id, []).append(c.status)
    offline_lines = [lid for lid, statuses in cam_by_line.items() if statuses and all(s == "OFFLINE" for s in statuses)]

    context = {
        "batches": [{"batchId": b.batch_id, "lineId": b.line_id, "yieldPct": b.yield_pct,
                     "defectRatePct": b.defect_rate, "riskLevel": b.risk_level} for b in batches],
        "riskDistribution": risk_counts,
        "defectRateByLine": line_summary,
        "equipmentDefectContribution": equipment_summary,
        "cameraFleet": {
            "counts": {s: sum(1 for c in cameras if c.status == s) for s in ("ONLINE", "DEGRADED", "OFFLINE")},
            "linesWithAllCamerasOffline": offline_lines,
        },
        "recentActivity": [{"actor": a.actor, "action": a.action, "targetId": a.target_id, "timestamp": a.timestamp}
                            for a in recent_audit],
    }

    try:
        result = generate_dashboard_insights(context)
    except AIUnavailableError as e:
        raise HTTPException(503, f"AI insights unavailable: {e}")

    insight = AiInsight(
        insight_id=f"ins-{uuid4().hex[:8]}", tenant_id="t1", generated_at=now_iso(), generated_by=acting,
        model=current_model(), summary=result.get("summary", ""),
        confidence_band=result.get("confidenceBand", "LOW"), findings=result.get("findings", []),
    )
    db.add(insight); db.commit(); db.refresh(insight)
    audit(db, acting, "generate_ai_insights", "ai_insight", insight.insight_id)
    return row_to_dict(insight)


@app.get("/insights/latest")
def latest_insights(db: Session = Depends(get_db)):
    insight = db.query(AiInsight).order_by(AiInsight.generated_at.desc()).first()
    if not insight:
        raise HTTPException(404, "no AI insights generated yet")
    return row_to_dict(insight)


MAX_CHAT_TOOL_ROUNDS = 5


@app.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in payload.messages]

    try:
        for _ in range(MAX_CHAT_TOOL_ROUNDS):
            result = chat_completion(messages, tools=CHAT_TOOL_SCHEMAS)
            messages.append(result["message"])
            if not result["tool_calls"]:
                return {"role": "assistant", "content": result["content"] or ""}
            for call in result["tool_calls"]:
                try:
                    args = json.loads(call["arguments"]) if call["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                tool_result = execute_tool(db, call["name"], args)
                messages.append({
                    "role": "tool", "tool_call_id": call["id"],
                    "content": json.dumps(tool_result, default=str),
                })
    except AIUnavailableError as e:
        raise HTTPException(503, f"CellMind Assistant unavailable: {e}")

    return {"role": "assistant", "content": "I wasn't able to complete that request — try rephrasing or asking something more specific."}


# ---------- Simulations ----------

def compute_simulation(batch: Batch, reduce: bool = True) -> dict:
    current = batch.defect_rate
    improvement = round(min(current * 0.35, max(current - 0.2, 0)), 1) * (1 if reduce else -1)
    predicted = round(max(current - improvement, 0), 1)
    return {
        "batchId": batch.batch_id, "currentDefectRatePct": current, "predictedDefectRatePct": predicted,
        "predictedImprovementPts": round(current - predicted, 1),
        "disclaimer": "Predicted outcome — not a guaranteed result (FR-10).",
    }


@app.post("/simulations")
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db)):
    batch = db.get(Batch, payload.batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")
    reduce = "reduce" in payload.adjustment.lower() or "decrease" in payload.adjustment.lower()
    return compute_simulation(batch, reduce=reduce)


# ---------- Retraining ----------

@app.get("/retraining/runs")
def list_runs(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(RetrainingRun)
    if status:
        q = q.filter(RetrainingRun.status == status)
    return rows_to_dicts(q.order_by(RetrainingRun.created_at.desc()).all())


@app.post("/retraining/runs", status_code=201)
def create_run(payload: RetrainingRunCreateRequest, db: Session = Depends(get_db)):
    acting = payload.acting_user_id or "u-qnair"
    require_permission(db, acting, "request_retrain")

    MIN_LABELED_CELLS = 40
    labeled_count = db.query(Cell).filter(Cell.taxonomy_id.isnot(None)).count()
    if labeled_count < MIN_LABELED_CELLS:
        raise HTTPException(422, f"Below minimum labeled-data volume (REQ-19.2): "
                                  f"{labeled_count}/{MIN_LABELED_CELLS} labeled cells.")

    latest = (db.query(ModelVersion).filter(ModelVersion.model_name == payload.model_name)
              .order_by(ModelVersion.trained_on_date.desc()).first())
    next_version_num = round(float(latest.version) + 0.1, 1) if latest else 1.0
    model_version = ModelVersion(
        model_version_id=f"mv-{uuid4().hex[:6]}", model_name=payload.model_name,
        version=str(next_version_num), tenant_id="t1", trained_on_date=now_iso()[:10],
        holdout_metric=0.0, status="staged", approved_by=None,
    )
    db.add(model_version)

    run = RetrainingRun(
        run_id=f"RUN-{uuid4().hex[:4].upper()}", model_version_id=model_version.model_version_id,
        model_name=payload.model_name, requested_by=acting, trigger_type=payload.trigger_type,
        status="DATA_VALIDATION", holdout_result=None, canary_result=None, created_at=now_iso(),
    )
    db.add(run); db.commit(); db.refresh(run)
    audit(db, acting, "request_retrain", "retraining_run", run.run_id)
    return row_to_dict(run)


@app.get("/retraining/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(RetrainingRun, run_id)
    if not run:
        raise HTTPException(404, "run not found")
    return row_to_dict(run)


@app.post("/retraining/runs/{run_id}/approve")
def approve_run(run_id: str, payload: ApprovalDecisionRequest, db: Session = Depends(get_db)):
    run = db.get(RetrainingRun, run_id)
    if not run:
        raise HTTPException(404, "run not found")

    acting = payload.acting_user_id or "u-jalvarez"
    require_permission(db, acting, "approve_retrain")
    if acting == run.requested_by:
        raise HTTPException(409, f"Approver ({user_name(db, acting)}) must be different from requester (BR-10).")

    run.status = "PROMOTED" if payload.decision == "approved" else "REJECTED"
    if run.status == "PROMOTED":
        new_version = db.get(ModelVersion, run.model_version_id)
        if new_version:
            prior_production = (db.query(ModelVersion)
                                 .filter(ModelVersion.model_name == new_version.model_name,
                                         ModelVersion.status == "production").all())
            for v in prior_production:
                v.status = "retired"
                db.add(v)
            new_version.status = "production"
            new_version.approved_by = acting
            db.add(new_version)
    db.add(run); db.commit()

    approval = {
        "approvalId": str(uuid4()), "targetType": "retraining_run", "targetId": run_id,
        "requestedBy": run.requested_by, "approver": acting, "decision": payload.decision,
        "rationaleOverride": payload.rationale_override, "decidedAt": now_iso(),
    }
    audit(db, acting, "approve_retrain", "retraining_run", run_id)
    return approval


@app.post("/retraining/runs/{run_id}/rollback")
def rollback_run(run_id: str, acting_user_id: str = "u-jalvarez", db: Session = Depends(get_db)):
    run = db.get(RetrainingRun, run_id)
    if not run:
        raise HTTPException(404, "run not found")
    require_permission(db, acting_user_id, "approve_retrain")

    current = db.get(ModelVersion, run.model_version_id)
    if not current:
        raise HTTPException(404, "model version not found")
    prior = (db.query(ModelVersion)
             .filter(ModelVersion.model_name == current.model_name, ModelVersion.status == "retired")
             .order_by(ModelVersion.trained_on_date.desc()).first())
    if not prior:
        prior = (db.query(ModelVersion)
                 .filter(ModelVersion.model_name == current.model_name,
                         ModelVersion.model_version_id != current.model_version_id,
                         ModelVersion.trained_on_date < current.trained_on_date)
                 .order_by(ModelVersion.trained_on_date.desc()).first())
    if not prior:
        raise HTTPException(404, "no prior model version available to roll back to")

    current.status = "retired"
    prior.status = "production"
    db.add_all([current, prior]); db.commit(); db.refresh(prior)
    run.status = "ROLLED_BACK"
    db.add(run); db.commit()
    audit(db, acting_user_id, "rollback_model", "model_version", prior.model_version_id)
    return row_to_dict(prior)


# ---------- Taxonomy ----------

@app.get("/taxonomy")
def list_taxonomy(version: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(DefectTaxonomyEntry)
    if version:
        q = q.filter(DefectTaxonomyEntry.taxonomy_version == version)
    return rows_to_dicts(q.all())


@app.get("/taxonomy/{taxonomy_id}")
def get_taxonomy_entry(taxonomy_id: str, db: Session = Depends(get_db)):
    entry = db.get(DefectTaxonomyEntry, taxonomy_id)
    if not entry:
        raise HTTPException(404, "taxonomy entry not found")
    return row_to_dict(entry)


@app.get("/taxonomy/versions")
def list_taxonomy_versions(db: Session = Depends(get_db)):
    return rows_to_dicts(db.query(TaxonomyVersion).all())


@app.post("/taxonomy/versions", status_code=201)
def create_taxonomy_version(payload: TaxonomyVersionCreateRequest, db: Session = Depends(get_db)):
    acting = payload.acting_user_id or "u-rchen"
    require_permission(db, acting, "configure_taxonomy")

    existing_ids = [v.version_id for v in db.query(TaxonomyVersion).all()]
    version_id = next_taxonomy_version(existing_ids)
    tv = TaxonomyVersion(version_id=version_id, published_at=now_iso(), published_by=acting,
                          changelog=payload.changelog, compatibility_issues=[])
    db.add(tv)

    for e in payload.entries:
        entry = db.get(DefectTaxonomyEntry, e.taxonomy_id)
        if entry:
            entry.category, entry.subtype, entry.severity = e.category, e.subtype, e.severity
            entry.root_cause_family, entry.suggested_action = e.root_cause_family, e.suggested_action
            entry.taxonomy_version = version_id
            db.add(entry)
        else:
            db.add(DefectTaxonomyEntry(
                taxonomy_id=e.taxonomy_id, category=e.category, subtype=e.subtype, severity=e.severity,
                root_cause_family=e.root_cause_family, suggested_action=e.suggested_action,
                taxonomy_version=version_id,
            ))
    db.commit(); db.refresh(tv)
    audit(db, acting, "publish_taxonomy_version", "taxonomy_version", version_id)
    return row_to_dict(tv)


# ---------- RBAC ----------

@app.get("/rbac/roles")
def list_roles(db: Session = Depends(get_db)):
    return rows_to_dicts(db.query(Role).all())


@app.get("/rbac/users")
def list_users(db: Session = Depends(get_db)):
    return rows_to_dicts(db.query(User).all())


@app.post("/rbac/users/{user_id}/role")
def assign_role(user_id: str, payload: RoleAssignRequest, db: Session = Depends(get_db)):
    acting = payload.acting_user_id or "u-rchen"
    require_permission(db, acting, "manage_rbac")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "user not found")
    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(404, "role not found")

    user.role_id = payload.role_id
    db.add(user); db.commit(); db.refresh(user)
    audit(db, acting, "change_role", "user", user_id)
    return {**row_to_dict(user), "role": row_to_dict(role)}


# ---------- Autonomy & Safety ----------

@app.get("/autonomy-config/{line_id}")
def get_autonomy_config(line_id: str, db: Session = Depends(get_db)):
    cfg = db.get(AutonomyConfig, line_id)
    if not cfg:
        raise HTTPException(404, "no autonomy config for this line")
    return row_to_dict(cfg)


@app.put("/autonomy-config/{line_id}")
def update_autonomy_config(line_id: str, payload: AutonomyConfigIn, db: Session = Depends(get_db)):
    if payload.autonomy_level == "C":
        raise HTTPException(422, "autonomyLevel 'C' (closed-loop) is not permitted regardless of caller role (REQ-20.5).")

    acting = payload.acting_user_id or "u-rchen"
    require_admin_permission(db, acting)

    cfg = db.get(AutonomyConfig, line_id)
    if not cfg:
        cfg = AutonomyConfig(line_id=line_id, autonomy_level=payload.autonomy_level,
                              fail_closed_override=payload.fail_closed_override, updated_by=acting)
    else:
        cfg.autonomy_level = payload.autonomy_level
        cfg.fail_closed_override = payload.fail_closed_override
        cfg.updated_by = acting
    db.add(cfg); db.commit(); db.refresh(cfg)
    audit(db, acting, "update_autonomy_config", "autonomy_config", line_id)
    return row_to_dict(cfg)


@app.get("/safety-constraints")
def list_safety_constraints(line_id: Optional[str] = Query(None, alias="lineId"), db: Session = Depends(get_db)):
    q = db.query(SafetyConstraint)
    if line_id:
        q = q.filter(SafetyConstraint.line_id == line_id)
    return rows_to_dicts(q.all())


@app.post("/safety-constraints", status_code=201)
def create_safety_constraint(payload: SafetyConstraintIn, db: Session = Depends(get_db)):
    acting = payload.acting_user_id or "u-rchen"
    require_admin_permission(db, acting)

    constraint_id = payload.constraint_id or f"sc-{uuid4().hex[:6]}"
    sc = SafetyConstraint(constraint_id=constraint_id, line_id=payload.line_id,
                           description=payload.description, rule_expression=payload.rule_expression)
    db.add(sc); db.commit(); db.refresh(sc)
    audit(db, acting, "create_safety_constraint", "safety_constraint", constraint_id)
    return row_to_dict(sc)


# ---------- Audit ----------

@app.get("/audit-log")
def audit_log(actor_id: Optional[str] = Query(None, alias="actorId"), action: Optional[str] = None,
              since: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(AuditLogEntry)
    if actor_id:
        q = q.filter(AuditLogEntry.actor == actor_id)
    if action:
        q = q.filter(AuditLogEntry.action == action)
    if since:
        q = q.filter(AuditLogEntry.timestamp >= since)
    rows = q.order_by(AuditLogEntry.timestamp.desc()).limit(limit).all()
    return rows_to_dicts(rows)


@app.get("/")
def root():
    return {"service": "CellMind API", "docs": "/docs"}
