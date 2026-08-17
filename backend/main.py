import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DATA = Path(__file__).parent / "data"


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


db = {name: load(name) for name in [
    "batches", "cells", "process", "equipment", "cameras",
    "investigations", "recommendations", "retraining_runs",
    "taxonomy", "taxonomy_versions", "users", "roles", "audit_log",
]}

app = FastAPI(title="CellMind Mock API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


def find(collection, key, value):
    for row in db[collection]:
        if row[key] == value:
            return row
    return None


def audit(actor, action, target_type, target_id):
    db["audit_log"].insert(0, {
        "eventId": str(uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor, "tenantId": "t1", "action": action,
        "targetType": target_type, "targetId": target_id,
        "beforeState": None, "afterState": None,
    })


def user_name(user_id):
    u = find("users", "userId", user_id)
    return u["name"] if u else user_id


def user_permissions(user_id):
    u = find("users", "userId", user_id)
    if not u:
        return []
    role = find("roles", "roleId", u["roleId"])
    return role["permissions"] if role else []


def require_permission(user_id, permission):
    if permission not in user_permissions(user_id):
        raise HTTPException(403, f"{user_name(user_id)} lacks the '{permission}' permission.")


@app.post("/auth/login")
def login(payload: dict):
    email = (payload.get("email") or "").strip().lower()
    u = next((x for x in db["users"] if x["email"].lower() == email), None)
    if not u or not payload.get("password"):
        raise HTTPException(401, "Invalid email or password.")
    role = find("roles", "roleId", u["roleId"])
    return {"accessToken": f"mock-{u['userId']}", "tokenType": "Bearer", "expiresIn": 3600,
            "user": {**u, "role": role}}


@app.get("/users/me")
def me(as_user: str = "u-jalvarez"):
    u = find("users", "userId", as_user)
    if not u:
        raise HTTPException(404, "unknown user")
    role = find("roles", "roleId", u["roleId"])
    return {**u, "role": role}


@app.get("/rbac/users")
def list_users():
    return db["users"]


@app.get("/rbac/roles")
def list_roles():
    return db["roles"]


@app.get("/batches")
def list_batches():
    return db["batches"]


@app.get("/batches/{batch_id}")
def get_batch(batch_id: str):
    b = find("batches", "batchId", batch_id)
    if not b:
        raise HTTPException(404, "batch not found")
    return b


@app.get("/batches/{batch_id}/cells")
def batch_cells(batch_id: str):
    return [c for c in db["cells"] if c["batchId"] == batch_id]


@app.get("/batches/{batch_id}/process")
def batch_process(batch_id: str):
    return [p for p in db["process"] if p["batchId"] == batch_id]


@app.get("/cells")
def list_cells():
    return db["cells"]


@app.post("/cells/{cell_id}/inspect")
def inspect_cell(cell_id: str):
    cell = find("cells", "cellId", cell_id)
    if not cell:
        raise HTTPException(404, "cell not found")
    prob = cell["defectProbability"]
    if prob >= 0.5:
        evidence = [
            {"sourceType": "image", "sourceRef": cell["cellId"],
             "description": f"Defect probability {round(prob * 100)}% — pattern consistent with {cell['severity'].lower()}-severity taxonomy entry."},
        ]
        band = "HIGH" if cell["confidence"] >= 0.85 else "MEDIUM"
    else:
        evidence = [{"sourceType": "image", "sourceRef": cell["cellId"], "description": "No defect pattern above threshold."}]
        band = "HIGH"
    return {
        "agentName": "InspectionAgent", "result": {"defectProbability": prob, "severity": cell["severity"]},
        "confidence": cell["confidence"], "confidenceBand": band, "evidence": evidence,
        "dataGaps": [], "oodFlag": cell.get("oodFlag", False),
    }


@app.get("/equipment")
def list_equipment():
    out = []
    for e in db["equipment"]:
        rate = round(100 * e["defectiveUnits"] / e["unitsProduced"], 1) if e["unitsProduced"] else 0
        out.append({**e, "defectRatePct": rate})
    total_defects = sum(e["defectiveUnits"] for e in db["equipment"]) or 1
    for row in out:
        row["shareOfDefectsPct"] = round(100 * row["defectiveUnits"] / total_defects, 1)
    return out


@app.get("/cameras")
def list_cameras():
    return db["cameras"]


@app.post("/cameras")
def create_camera(payload: dict):
    require_permission(payload.get("actingUserId", "u-rchen"), "manage_cameras")
    if payload.get("cameraType") == "EL" and not payload.get("elCapable"):
        raise HTTPException(422, "EL-capability must be confirmed before this camera can serve EL inspection (REQ-18.1).")
    cam = {
        "cameraId": payload.get("cameraId") or f"CAM-{uuid4().hex[:6].upper()}",
        "tenantId": "t1", "cameraType": payload.get("cameraType", "VISUAL"),
        "elCapable": bool(payload.get("elCapable", False)), "model": payload.get("model", ""),
        "lineId": payload.get("lineId"), "stationId": payload.get("stationId"),
        "streamUrl": payload.get("streamUrl"), "status": "ONLINE",
        "lastFrameAt": datetime.now(timezone.utc).isoformat(),
        "retentionDays": payload.get("retentionDays", 90),
    }
    db["cameras"].insert(0, cam)
    audit(payload.get("actingUserId", "u-rchen"), "register_camera", "camera", cam["cameraId"])
    return cam


@app.get("/cameras/{camera_id}/health")
def camera_health(camera_id: str):
    cam = find("cameras", "cameraId", camera_id)
    if not cam:
        raise HTTPException(404, "camera not found")
    return {"cameraId": cam["cameraId"], "status": cam["status"], "lastFrameAt": cam["lastFrameAt"],
            "consecutiveMissedHeartbeats": 3 if cam["status"] != "ONLINE" else 0}


@app.get("/investigations")
def list_investigations():
    return db["investigations"]


@app.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: str):
    inv = find("investigations", "investigationId", investigation_id)
    if not inv:
        raise HTTPException(404, "investigation not found")
    return inv


@app.get("/recommendations/{investigation_id}")
def get_recommendation(investigation_id: str):
    rec = find("recommendations", "investigationId", investigation_id)
    if not rec:
        raise HTTPException(404, "no recommendation for this investigation")
    return rec


@app.post("/recommendations/{recommendation_id}/approve")
def approve_recommendation(recommendation_id: str, payload: dict):
    rec = find("recommendations", "recommendationId", recommendation_id)
    if not rec:
        raise HTTPException(404, "recommendation not found")
    acting = payload.get("actingUserId", "u-jalvarez")
    if not any(p.startswith("approve_") for p in user_permissions(acting)):
        raise HTTPException(403, f"{user_name(acting)}'s role cannot approve recommendations.")
    rec["approval"] = {
        "approvalId": str(uuid4()), "targetType": "recommendation", "targetId": recommendation_id,
        "requestedBy": "system", "approver": acting, "decision": payload.get("decision", "approved"),
        "rationaleOverride": payload.get("rationaleOverride"),
        "decidedAt": datetime.now(timezone.utc).isoformat(),
    }
    audit(acting, "approve_recommendation", "recommendation", recommendation_id)
    return rec["approval"]


@app.get("/retraining/runs")
def list_runs():
    return db["retraining_runs"]


@app.get("/retraining/runs/{run_id}")
def get_run(run_id: str):
    run = find("retraining_runs", "runId", run_id)
    if not run:
        raise HTTPException(404, "run not found")
    return run


@app.post("/retraining/runs/{run_id}/approve")
def approve_run(run_id: str, payload: dict):
    run = find("retraining_runs", "runId", run_id)
    if not run:
        raise HTTPException(404, "run not found")
    acting = payload.get("actingUserId", "u-jalvarez")
    require_permission(acting, "approve_retrain")
    if acting == run["requestedBy"]:
        raise HTTPException(409, f"Approver ({user_name(acting)}) must be different from requester (BR-10).")
    decision = payload.get("decision", "approved")
    run["status"] = "PROMOTED" if decision == "approved" else "REJECTED"
    audit(acting, "approve_retrain", "retraining_run", run_id)
    return run


@app.get("/taxonomy")
def list_taxonomy():
    return db["taxonomy"]


@app.get("/taxonomy/versions")
def list_taxonomy_versions():
    return db["taxonomy_versions"]


@app.get("/audit-log")
def audit_log(limit: int = 50):
    return db["audit_log"][:limit]


@app.get("/")
def root():
    return {"service": "CellMind Mock API", "docs": "/docs"}
