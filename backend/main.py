import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from ml_bridge import classify
from models import (
    AuditLogEntry, AutonomyConfig, Batch, Camera, Cell, DefectTaxonomyEntry,
    Equipment, Investigation, ModelVersion, ProcessRecord, Recommendation,
    RetrainingRun, Role, SafetyConstraint, TaxonomyVersion, User,
)
from schemas import (
    ApprovalDecisionRequest, AutonomyConfigIn, CameraCreateRequest,
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
    db.add(cell); db.commit()

    band = "HIGH" if result["confidence"] >= 0.85 else ("MEDIUM" if result["confidence"] >= 0.6 else "LOW")
    evidence = [{"sourceType": "image", "sourceRef": cell.cell_id,
                 "description": f"Classifier predicts '{result['label']}' with "
                                 f"{round(result['confidence'] * 100)}% confidence "
                                 f"(defect probability {round(result['defectProbability'] * 100)}%)."}]
    return {
        "agentName": "InspectionAgent",
        "result": {"defectProbability": result["defectProbability"], "severity": result["severity"]},
        "confidence": result["confidence"], "confidenceBand": band, "evidence": evidence,
        "dataGaps": [], "oodFlag": cell.ood_flag,
    }


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

    return result


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


# ---------- Simulations ----------

@app.post("/simulations")
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db)):
    batch = db.get(Batch, payload.batch_id)
    if not batch:
        raise HTTPException(404, "batch not found")

    current = batch.defect_rate
    direction = -1 if "reduce" in payload.adjustment.lower() or "decrease" in payload.adjustment.lower() else 1
    improvement = round(min(current * 0.35, max(current - 0.2, 0)), 1) * (1 if direction < 0 else -1)
    predicted = round(max(current - improvement, 0), 1)

    return {
        "batchId": batch.batch_id, "currentDefectRatePct": current, "predictedDefectRatePct": predicted,
        "predictedImprovementPts": round(current - predicted, 1),
        "disclaimer": "Predicted outcome — not a guaranteed result (FR-10).",
    }


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
