"""Read-only tool functions the chatbot (POST /chat in main.py) can call via
Azure OpenAI function calling.

This file is the entire safety boundary for the chat feature: there is no
create/update/delete tool defined here, anywhere. Each function mirrors an
existing GET endpoint's query logic in main.py, returning a plain dict/list
instead of an HTTP response.
"""
from sqlalchemy.orm import Session

from models import (
    AiInsight, AuditLogEntry, Batch, Camera, Cell, DefectTaxonomyEntry,
    Equipment, Investigation, Recommendation, RetrainingRun,
)
from serialization import row_to_dict, rows_to_dicts


def _list_batches(db, line_id=None, risk_level=None):
    q = db.query(Batch)
    if line_id:
        q = q.filter(Batch.line_id == line_id)
    if risk_level:
        q = q.filter(Batch.risk_level == risk_level)
    return rows_to_dicts(q.all())


def _get_batch(db, batch_id):
    b = db.get(Batch, batch_id)
    return row_to_dict(b) if b else {"error": f"No batch found with id {batch_id!r}."}


def _list_cells_for_batch(db, batch_id, limit=20):
    if not db.get(Batch, batch_id):
        return {"error": f"No batch found with id {batch_id!r}."}
    rows = db.query(Cell).filter(Cell.batch_id == batch_id).limit(limit).all()
    return rows_to_dicts(rows)


def _list_equipment(db):
    rows = db.query(Equipment).all()
    total_defects = sum(e.defective_units for e in rows) or 1
    out = []
    for e in rows:
        d = row_to_dict(e)
        d["defectRatePct"] = round(100 * e.defective_units / e.units_produced, 1) if e.units_produced else 0
        d["shareOfDefectsPct"] = round(100 * e.defective_units / total_defects, 1)
        out.append(d)
    return out


def _list_cameras(db, line_id=None):
    q = db.query(Camera)
    if line_id:
        q = q.filter(Camera.line_id == line_id)
    return rows_to_dicts(q.all())


def _list_investigations(db, limit=10):
    rows = db.query(Investigation).order_by(Investigation.created_at.desc()).limit(limit).all()
    return rows_to_dicts(rows)


def _get_investigation(db, investigation_id):
    inv = db.get(Investigation, investigation_id)
    return row_to_dict(inv) if inv else {"error": f"No investigation found with id {investigation_id!r}."}


def _get_recommendation(db, investigation_id):
    rec = db.query(Recommendation).filter(Recommendation.investigation_id == investigation_id).first()
    return row_to_dict(rec) if rec else {"error": f"No recommendation exists yet for investigation {investigation_id!r}."}


def _list_taxonomy(db):
    return rows_to_dicts(db.query(DefectTaxonomyEntry).all())


def _list_retraining_runs(db, status=None):
    q = db.query(RetrainingRun)
    if status:
        q = q.filter(RetrainingRun.status == status)
    return rows_to_dicts(q.order_by(RetrainingRun.created_at.desc()).all())


def _get_audit_log(db, actor_id=None, action=None, limit=10):
    q = db.query(AuditLogEntry)
    if actor_id:
        q = q.filter(AuditLogEntry.actor == actor_id)
    if action:
        q = q.filter(AuditLogEntry.action == action)
    return rows_to_dicts(q.order_by(AuditLogEntry.timestamp.desc()).limit(limit).all())


def _get_latest_ai_insight(db):
    insight = db.query(AiInsight).order_by(AiInsight.generated_at.desc()).first()
    return row_to_dict(insight) if insight else {"error": "No AI insight has been generated yet."}


_HANDLERS = {
    "list_batches": _list_batches,
    "get_batch": _get_batch,
    "list_cells_for_batch": _list_cells_for_batch,
    "list_equipment": _list_equipment,
    "list_cameras": _list_cameras,
    "list_investigations": _list_investigations,
    "get_investigation": _get_investigation,
    "get_recommendation": _get_recommendation,
    "list_taxonomy": _list_taxonomy,
    "list_retraining_runs": _list_retraining_runs,
    "get_audit_log": _get_audit_log,
    "get_latest_ai_insight": _get_latest_ai_insight,
}


def execute_tool(db: Session, name: str, arguments: dict):
    handler = _HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool {name!r}."}
    try:
        return handler(db, **arguments)
    except TypeError as e:
        return {"error": f"Invalid arguments for {name}: {e}"}


def _schema(name, description, params=None, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": params or {}, "required": required or []},
        },
    }


CHAT_TOOL_SCHEMAS = [
    _schema("list_batches", "List production batches, optionally filtered by line or risk level.",
            {"line_id": {"type": "string", "description": "e.g. L1, L2"},
             "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]}}),
    _schema("get_batch", "Get one batch by id.", {"batch_id": {"type": "string"}}, ["batch_id"]),
    _schema("list_cells_for_batch", "List inspected cells for one batch (defect probability, severity, taxonomy).",
            {"batch_id": {"type": "string"}, "limit": {"type": "integer", "description": "default 20"}}, ["batch_id"]),
    _schema("list_equipment", "List equipment with defect rate and share of total defects."),
    _schema("list_cameras", "List inspection cameras and their health status, optionally filtered by line.",
            {"line_id": {"type": "string"}}),
    _schema("list_investigations", "List the most recent investigations.",
            {"limit": {"type": "integer", "description": "default 10"}}),
    _schema("get_investigation", "Get one investigation's full agent-pipeline results (inspection/process/context/root-cause).",
            {"investigation_id": {"type": "string"}}, ["investigation_id"]),
    _schema("get_recommendation", "Get the recommendation (ranked corrective actions + AI reasoning) for an investigation.",
            {"investigation_id": {"type": "string"}}, ["investigation_id"]),
    _schema("list_taxonomy", "List the defect taxonomy (categories, severities, suggested actions)."),
    _schema("list_retraining_runs", "List model retraining pipeline runs, optionally filtered by status.",
            {"status": {"type": "string", "enum": ["DATA_VALIDATION", "TRAINING", "HOLDOUT_EVAL",
                                                    "STAGED_ROLLOUT", "PENDING_APPROVAL", "PROMOTED",
                                                    "REJECTED", "ROLLED_BACK"]}}),
    _schema("get_audit_log", "List recent governed actions (approvals, camera registrations, AI generations, etc).",
            {"actor_id": {"type": "string"}, "action": {"type": "string"},
             "limit": {"type": "integer", "description": "default 10"}}),
    _schema("get_latest_ai_insight", "Get the most recently generated plant-wide AI insight snapshot."),
]
