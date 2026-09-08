"""Seed backend/cellmind.db with connected sample data and copy a handful of
real training_data images into backend/static/images/ for cell/investigation photos.

Run:
    python backend/seed.py
"""
import random
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from database import Base, SessionLocal, engine
from models import (
    AuditLogEntry, AutonomyConfig, Batch, Camera, Cell, DefectTaxonomyEntry,
    Equipment, Investigation, ModelVersion, ProcessRecord, Recommendation,
    RetrainingRun, Role, SafetyConstraint, TaxonomyVersion, User,
)

RNG = random.Random(42)

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
SOURCE_IMAGE_ROOT = REPO_ROOT / "training_data" / "Faulty_solar_panel"
STATIC_IMAGES_DIR = BACKEND_DIR / "static" / "images"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
IMAGES_PER_CLASS = 5

# (folder name, taxonomy slug (None = Clean/no defect), severity, defectProbability range)
CLASSES = [
    ("Clean", None, None, (0.02, 0.15)),
    ("Bird-drop", "bird_drop", "MEDIUM", (0.35, 0.70)),
    ("Dusty", "dusty", "LOW", (0.25, 0.55)),
    ("Electrical-damage", "electrical_damage", "HIGH", (0.60, 0.95)),
    ("Physical-Damage", "physical_damage", "HIGH", (0.65, 0.95)),
    ("Snow-Covered", "snow_covered", "MEDIUM", (0.30, 0.60)),
]

NEW_TAXONOMY_ENTRIES = [
    {"taxonomyId": "bird_drop", "category": "Bird dropping", "subtype": "Surface soiling",
     "severity": "MEDIUM", "rootCauseFamily": "Environmental fouling",
     "suggestedAction": "Schedule panel cleaning"},
    {"taxonomyId": "dusty", "category": "Dust accumulation", "subtype": "Surface soiling",
     "severity": "LOW", "rootCauseFamily": "Environmental fouling",
     "suggestedAction": "Schedule panel cleaning"},
    {"taxonomyId": "electrical_damage", "category": "Electrical damage", "subtype": "Hot-spot / burn",
     "severity": "HIGH", "rootCauseFamily": "Electrical fault",
     "suggestedAction": "De-energize line and inspect wiring/bypass diodes"},
    {"taxonomyId": "physical_damage", "category": "Physical damage", "subtype": "Crack / impact",
     "severity": "HIGH", "rootCauseFamily": "Mechanical impact",
     "suggestedAction": "Inspect for structural glass/frame damage and replace if required"},
    {"taxonomyId": "snow_covered", "category": "Snow coverage", "subtype": "Seasonal obstruction",
     "severity": "MEDIUM", "rootCauseFamily": "Environmental obstruction",
     "suggestedAction": "Monitor; no corrective action needed until snow clears"},
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def days_ago(n):
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def reset_database():
    if Path(engine.url.database).exists():
        Path(engine.url.database).unlink()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def reset_static_images():
    if STATIC_IMAGES_DIR.exists():
        shutil.rmtree(STATIC_IMAGES_DIR)
    STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def copy_sample_images():
    """Copy IMAGES_PER_CLASS real photos per class into backend/static/images/.

    Returns {class_folder_name: ["/static/images/xxx.jpg", ...]}.
    """
    copied = {}
    for class_name, _, _, _ in CLASSES:
        src_dir = SOURCE_IMAGE_ROOT / class_name
        files = sorted(
            f for f in src_dir.iterdir()
            if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
        )[:IMAGES_PER_CLASS]
        web_paths = []
        slug = class_name.lower().replace(" ", "-")
        for i, f in enumerate(files, start=1):
            dest_name = f"{slug}-{i:02d}{f.suffix.lower()}"
            shutil.copyfile(f, STATIC_IMAGES_DIR / dest_name)
            web_paths.append(f"/static/images/{dest_name}")
        copied[class_name] = web_paths
        print(f"  {class_name}: copied {len(web_paths)} images")
    return copied


def degraded_electrical_params(defect_probability):
    return {
        "voc": round(0.64 - 0.05 * defect_probability + RNG.uniform(-0.01, 0.01), 3),
        "isc": round(9.3 - 0.5 * defect_probability + RNG.uniform(-0.1, 0.1), 2),
        "fill_factor": round(0.80 - 0.15 * defect_probability + RNG.uniform(-0.01, 0.01), 3),
        "efficiency": round(22.0 - 4.0 * defect_probability + RNG.uniform(-0.2, 0.2), 1),
        "series_resistance": round(0.003 + 0.01 * defect_probability + RNG.uniform(-0.0005, 0.0005), 4),
    }


def seed(db):
    print("Copying sample images from training_data/ ...")
    images_by_class = copy_sample_images()

    # ---- Roles & Users (one user per role) ----
    print("Seeding roles & users ...")
    roles = [
        {"roleId": "role_viewer", "roleName": "Viewer", "permissions": ["view_data"]},
        {"roleId": "role_quality_engineer", "roleName": "Quality Engineer",
         "permissions": ["view_data", "request_retrain", "approve_quality_action"]},
        {"roleId": "role_process_engineer", "roleName": "Process Engineer",
         "permissions": ["view_data", "approve_process_action"]},
        {"roleId": "role_equipment_engineer", "roleName": "Equipment Engineer",
         "permissions": ["view_data", "approve_equipment_action"]},
        {"roleId": "role_plant_manager", "roleName": "Plant/Operations Manager", "permissions": ["view_data"]},
        {"roleId": "role_platform_admin", "roleName": "Platform Administrator",
         "permissions": ["manage_cameras", "configure_taxonomy", "manage_rbac"]},
        {"roleId": "role_ml_ops_lead", "roleName": "ML Operations Lead",
         "permissions": ["view_data", "request_retrain", "approve_retrain"]},
    ]
    for r in roles:
        db.add(Role(role_id=r["roleId"], role_name=r["roleName"], permissions=r["permissions"]))

    users = [
        {"userId": "u-qnair", "name": "Q. Nair", "email": "q.nair@meridiansolar.example", "roleId": "role_quality_engineer"},
        {"userId": "u-jalvarez", "name": "J. Alvarez", "email": "j.alvarez@meridiansolar.example", "roleId": "role_ml_ops_lead"},
        {"userId": "u-rchen", "name": "R. Chen", "email": "r.chen@meridiansolar.example", "roleId": "role_platform_admin"},
        {"userId": "u-tokafor", "name": "T. Okafor", "email": "t.okafor@meridiansolar.example", "roleId": "role_equipment_engineer"},
        {"userId": "u-mwright", "name": "M. Wright", "email": "m.wright@meridiansolar.example", "roleId": "role_plant_manager"},
        {"userId": "u-dsingh", "name": "D. Singh", "email": "d.singh@meridiansolar.example", "roleId": "role_process_engineer"},
        {"userId": "u-fsalem", "name": "F. Salem", "email": "f.salem@meridiansolar.example", "roleId": "role_viewer"},
    ]
    for u in users:
        db.add(User(user_id=u["userId"], tenant_id="t1", name=u["name"], email=u["email"],
                     role_id=u["roleId"], sso_subject=None, created_at=days_ago(200)))
    db.flush()

    # ---- Taxonomy ----
    print("Seeding taxonomy ...")
    db.add(TaxonomyVersion(version_id="v1.3", published_at=days_ago(50), published_by="u-rchen",
                            changelog="Added Finger interruption print-defect subtype.", compatibility_issues=[]))
    db.add(TaxonomyVersion(version_id="v1.4", published_at=days_ago(3), published_by="u-rchen",
                            changelog="Added visual surface-fault categories (bird dropping, dust, electrical "
                                      "damage, physical damage, snow coverage) sourced from the visual-inspection "
                                      "training set.", compatibility_issues=[]))
    existing_taxonomy = [
        {"taxonomyId": "micro_crack_edge", "category": "Micro-crack", "subtype": "Edge-induced", "severity": "MEDIUM",
         "rootCauseFamily": "Firing thermal shock", "suggestedAction": "Review firing ramp rate", "taxonomyVersion": "v1.3"},
        {"taxonomyId": "micro_crack_handling", "category": "Micro-crack", "subtype": "Handling", "severity": "LOW",
         "rootCauseFamily": "Handling stress", "suggestedAction": "Inspect handling equipment", "taxonomyVersion": "v1.3"},
        {"taxonomyId": "finger_interruption", "category": "Finger interruption", "subtype": "Print defect", "severity": "HIGH",
         "rootCauseFamily": "Metallization process", "suggestedAction": "Review screen-print alignment", "taxonomyVersion": "v1.3"},
    ]
    for t in existing_taxonomy:
        db.add(DefectTaxonomyEntry(taxonomy_id=t["taxonomyId"], category=t["category"], subtype=t["subtype"],
                                    severity=t["severity"], root_cause_family=t["rootCauseFamily"],
                                    suggested_action=t["suggestedAction"], taxonomy_version=t["taxonomyVersion"]))
    for t in NEW_TAXONOMY_ENTRIES:
        db.add(DefectTaxonomyEntry(taxonomy_id=t["taxonomyId"], category=t["category"], subtype=t["subtype"],
                                    severity=t["severity"], root_cause_family=t["rootCauseFamily"],
                                    suggested_action=t["suggestedAction"], taxonomy_version="v1.4"))
    db.flush()

    # ---- Equipment ----
    print("Seeding equipment ...")
    equipment = [
        {"equipmentId": "F07", "equipmentType": "firing_furnace", "operatingHours": 14320.5,
         "maintenanceDate": "2026-06-01", "status": "active", "unitsProduced": 2400, "defectiveUnits": 615},
        {"equipmentId": "F03", "equipmentType": "firing_furnace", "operatingHours": 9820.0,
         "maintenanceDate": "2026-07-15", "status": "active", "unitsProduced": 3100, "defectiveUnits": 91},
        {"equipmentId": "D02", "equipmentType": "diffusion_furnace", "operatingHours": 11200.0,
         "maintenanceDate": "2026-05-20", "status": "active", "unitsProduced": 2800, "defectiveUnits": 140},
        {"equipmentId": "P01", "equipmentType": "screen_printer", "operatingHours": 6400.0,
         "maintenanceDate": "2026-07-01", "status": "active", "unitsProduced": 2600, "defectiveUnits": 210},
    ]
    for e in equipment:
        db.add(Equipment(equipment_id=e["equipmentId"], equipment_type=e["equipmentType"],
                          operating_hours=e["operatingHours"], maintenance_date=e["maintenanceDate"],
                          status=e["status"], units_produced=e["unitsProduced"], defective_units=e["defectiveUnits"]))

    # ---- Cameras (L1 all OFFLINE -> demonstrates BR-11 fail-open on /investigations) ----
    print("Seeding cameras (L1 deliberately offline, for BR-11 demo) ...")
    cameras = [
        {"cameraId": "CAM-EL-07", "cameraType": "EL", "elCapable": True, "model": "Synapt EL-Cap 4K",
         "lineId": "L2", "stationId": "S3", "streamUrl": "rtsps://plant2-l2s3.local/el07", "status": "DEGRADED", "retentionDays": 90},
        {"cameraId": "CAM-VIS-11", "cameraType": "VISUAL", "elCapable": False, "model": "Generic IP Cam",
         "lineId": "L2", "stationId": "S3", "streamUrl": "rtsps://plant2-l2s3.local/vis11", "status": "ONLINE", "retentionDays": 30},
        {"cameraId": "CAM-VIS-12", "cameraType": "VISUAL", "elCapable": False, "model": "Generic IP Cam",
         "lineId": "L2", "stationId": "S4", "streamUrl": "rtsps://plant2-l2s4.local/vis12", "status": "ONLINE", "retentionDays": 30},
        {"cameraId": "CAM-EL-01", "cameraType": "EL", "elCapable": True, "model": "Synapt EL-Cap 4K",
         "lineId": "L1", "stationId": "S1", "streamUrl": "rtsps://plant1-l1s1.local/el01", "status": "OFFLINE", "retentionDays": 90},
        {"cameraId": "CAM-VIS-02", "cameraType": "VISUAL", "elCapable": False, "model": "Generic IP Cam",
         "lineId": "L1", "stationId": "S1", "streamUrl": "rtsps://plant1-l1s1.local/vis02", "status": "OFFLINE", "retentionDays": 30},
    ]
    for c in cameras:
        db.add(Camera(camera_id=c["cameraId"], tenant_id="t1", camera_type=c["cameraType"], el_capable=c["elCapable"],
                       model=c["model"], line_id=c["lineId"], station_id=c["stationId"], stream_url=c["streamUrl"],
                       status=c["status"], last_frame_at=days_ago(0 if c["status"] == "ONLINE" else 5),
                       retention_days=c["retentionDays"]))

    # ---- Batches ----
    print("Seeding batches & cells ...")
    lines = ["L2", "L2", "L2", "L2", "L2", "L1", "L1", "L1"]
    batches = []
    for i, line in enumerate(lines):
        batch_id = f"B{1840 + i * 7}"
        cell_count = RNG.randint(8000, 11000)
        defect_rate = round(RNG.uniform(3.0, 12.0), 1)
        defect_count = round(cell_count * defect_rate / 100)
        good_count = cell_count - defect_count
        risk_level = "HIGH" if defect_rate >= 8 else ("MEDIUM" if defect_rate >= 5 else "LOW")
        batch = {"batchId": batch_id, "lineId": line, "productionDate": days_ago(60 - i * 6)[:10],
                 "cellCount": cell_count, "goodCount": good_count, "defectCount": defect_count,
                 "yield": round(100 - defect_rate, 1), "defectRate": defect_rate, "riskLevel": risk_level}
        batches.append(batch)
        db.add(Batch(batch_id=batch_id, tenant_id="t1", production_date=batch["productionDate"], line_id=line,
                      cell_count=cell_count, good_count=good_count, defect_count=defect_count,
                      yield_pct=batch["yield"], defect_rate=defect_rate, risk_level=risk_level))
    db.flush()

    # ---- Cells (image-backed sample of inspected cells per batch) ----
    cell_counter = 1000
    all_cells = []  # (cell_id, batch, class_name, defect_probability, taxonomy_slug)
    for batch in batches:
        n_cells = RNG.randint(8, 12)
        for _ in range(n_cells):
            class_name, taxonomy_slug, severity, prob_range = RNG.choices(
                CLASSES, weights=[45, 12, 13, 10, 8, 12], k=1,
            )[0]
            image_pool = images_by_class[class_name]
            image_path = RNG.choice(image_pool)
            defect_probability = round(RNG.uniform(*prob_range), 2)
            params = degraded_electrical_params(defect_probability)
            cell_id = f"C{cell_counter}"
            cell_counter += 1
            confidence = round(RNG.uniform(0.82, 0.98), 2)
            db.add(Cell(
                cell_id=cell_id, batch_id=batch["batchId"], image_path=image_path,
                defect_probability=defect_probability, severity=severity or "LOW", confidence=confidence,
                ood_flag=False, taxonomy_id=taxonomy_slug, **params,
            ))
            all_cells.append({"cellId": cell_id, "batch": batch, "className": class_name,
                               "taxonomySlug": taxonomy_slug, "defectProbability": defect_probability,
                               "severity": severity or "LOW", "confidence": confidence, "imagePath": image_path,
                               "oodFlag": False})
    db.flush()

    # ---- Process records ----
    print("Seeding process records ...")
    stages = [("firing", "F07"), ("firing", "F03"), ("diffusion", "D02"), ("print", "P01")]
    for batch in batches:
        for stage, equipment_id in RNG.sample(stages, k=2):
            db.add(ProcessRecord(
                process_id=f"p-{uuid4().hex[:8]}", batch_id=batch["batchId"], stage=stage,
                equipment_id=equipment_id, temperature=round(RNG.uniform(780, 850), 1),
                duration=round(RNG.uniform(20, 45), 1), pressure=round(RNG.uniform(0.95, 1.05), 2),
                gas_flow=round(RNG.uniform(12, 20), 1), timestamp=batch["productionDate"] + "T08:00:00Z",
            ))

    # ---- Model versions & retraining runs ----
    print("Seeding model versions & retraining runs ...")
    model_versions = [
        {"modelVersionId": "mv-23", "version": "2.3", "status": "retired", "holdoutMetric": 0.89, "approvedBy": "u-jalvarez"},
        {"modelVersionId": "mv-24", "version": "2.4", "status": "production", "holdoutMetric": 0.91, "approvedBy": "u-jalvarez"},
        {"modelVersionId": "mv-25", "version": "2.5", "status": "staged", "holdoutMetric": 0.93, "approvedBy": None},
        {"modelVersionId": "mv-26", "version": "2.6", "status": "staged", "holdoutMetric": 0.0, "approvedBy": None},
    ]
    for mv in model_versions:
        db.add(ModelVersion(model_version_id=mv["modelVersionId"], model_name="el-inspection-cv", version=mv["version"],
                             tenant_id="t1", trained_on_date=days_ago(30)[:10], holdout_metric=mv["holdoutMetric"],
                             status=mv["status"], approved_by=mv["approvedBy"]))

    runs = [
        {"runId": "RUN-2198", "modelVersionId": "mv-24", "requestedBy": "u-qnair", "triggerType": "scheduled",
         "status": "PROMOTED", "holdoutResult": 0.91, "canaryResult": 0.01, "createdAt": days_ago(19)},
        {"runId": "RUN-2210", "modelVersionId": "mv-25", "requestedBy": "u-qnair", "triggerType": "drift_alert",
         "status": "PENDING_APPROVAL", "holdoutResult": 0.93, "canaryResult": None, "createdAt": days_ago(7)},
        {"runId": "RUN-2214", "modelVersionId": "mv-26", "requestedBy": "u-qnair", "triggerType": "taxonomy_change",
         "status": "DATA_VALIDATION", "holdoutResult": None, "canaryResult": None, "createdAt": days_ago(2)},
        {"runId": "RUN-2205", "modelVersionId": "mv-23", "requestedBy": "u-qnair", "triggerType": "manual",
         "status": "REJECTED", "holdoutResult": 0.84, "canaryResult": None, "createdAt": days_ago(12)},
    ]
    for r in runs:
        db.add(RetrainingRun(run_id=r["runId"], model_version_id=r["modelVersionId"], model_name="el-inspection-cv",
                              requested_by=r["requestedBy"], trigger_type=r["triggerType"], status=r["status"],
                              holdout_result=r["holdoutResult"], canary_result=r["canaryResult"], created_at=r["createdAt"]))

    # ---- Investigations & Recommendations (from real defective cells) ----
    print("Seeding investigations & recommendations ...")
    defective = [c for c in all_cells if c["taxonomySlug"] or c["className"] != "Clean"]
    sample_cells = RNG.sample(defective, k=min(6, len(defective)))
    action_templates = [
        ("Adjust firing profile", "Low", 2.4, 0, 0.10),
        ("Perform equipment maintenance", "Medium", 4.1, 2, 0.20),
        ("Replace component", "High", 4.8, 8, 0.35),
    ]

    for i, c in enumerate(sample_cells):
        batch = c["batch"]
        inv_id = f"inv-{uuid4().hex[:8]}"
        worst_equipment = max(equipment, key=lambda e: e["defectiveUnits"] / e["unitsProduced"])
        rate = round(100 * worst_equipment["defectiveUnits"] / worst_equipment["unitsProduced"], 1)

        agents = {
            "inspection": {
                "agentName": "InspectionAgent",
                "result": {"defectProbability": c["defectProbability"], "severity": c["severity"]},
                "confidence": c["confidence"], "confidenceBand": "HIGH" if c["confidence"] >= 0.85 else "MEDIUM",
                "evidence": [{"sourceType": "image", "sourceRef": c["cellId"],
                               "description": f"Defect probability {round(c['defectProbability']*100)}%, "
                                              f"pattern consistent with {c['className'].lower()}."}],
                "dataGaps": [], "oodFlag": False,
            },
            "process": {
                "agentName": "ProcessAgent",
                "result": {"anomalies": [{"parameter": "temperature", "equipmentId": worst_equipment["equipmentId"],
                                           "baseline": 800.0, "value": round(RNG.uniform(805, 845), 1)}]},
                "confidence": 0.82, "confidenceBand": "HIGH",
                "evidence": [{"sourceType": "process_param", "sourceRef": f"{worst_equipment['equipmentId']} firing stage",
                               "description": "Temperature variance above configured baseline."}],
                "dataGaps": [], "oodFlag": False,
            },
            "context": {
                "agentName": "ContextAgent",
                "result": {"historicalMatches": [b["batchId"] for b in batches if b["riskLevel"] == "HIGH"
                                                   and b["batchId"] != batch["batchId"]][:2]},
                "confidence": 0.8, "confidenceBand": "MEDIUM",
                "evidence": [{"sourceType": "historical_incident", "sourceRef": f"Batch {b['batchId']}",
                               "description": "Similar high-risk batch on the same line."}
                              for b in batches if b["riskLevel"] == "HIGH" and b["batchId"] != batch["batchId"]][:1],
                "dataGaps": [], "oodFlag": False,
            },
            "rootCause": {
                "agentName": "RootCauseAgent",
                "result": {"probableCause": f"{worst_equipment['equipmentId']} process variation",
                           "equipmentRate": rate, "equipmentShare": rate},
                "confidence": 0.9, "confidenceBand": "HIGH",
                "evidence": [{"sourceType": "equipment", "sourceRef": worst_equipment["equipmentId"],
                               "description": f"Defect rate {rate}% traced to {worst_equipment['equipmentId']}."}],
                "dataGaps": [], "oodFlag": False,
            },
        }
        db.add(Investigation(investigation_id=inv_id, batch_id=batch["batchId"], cell_id=c["cellId"],
                              status="COMPLETE", agents=agents, created_at=days_ago(10 - i)))

        ranked = [
            {"actionId": f"act-{uuid4().hex[:6]}", "rank": rank + 1, "title": title, "cost": cost,
             "expectedImprovementPct": pct, "downtimeHours": dt, "riskScore": risk,
             "preSelected": rank == 0, "filtered": False, "filterReason": None}
            for rank, (title, cost, pct, dt, risk) in enumerate(action_templates)
        ]
        filtered = []
        if i == 0:
            blocked = ranked.pop()
            blocked["filtered"], blocked["filterReason"] = True, "Replace-component action blocked outside a declared maintenance window."
            filtered.append(blocked)

        approval = None
        if i % 2 == 0:
            approval = {"approvalId": str(uuid4()), "targetType": "recommendation", "targetId": None,
                        "requestedBy": "system:RootCauseAgent", "approver": "u-jalvarez", "decision": "approved",
                        "rationaleOverride": None, "decidedAt": days_ago(9 - i)}

        rec_id = f"rec-{uuid4().hex[:6]}"
        if approval:
            approval["targetId"] = rec_id
        reasoning = (
            f"{worst_equipment['equipmentId']} shows a {rate}% defect rate, the highest of any equipment "
            f"referenced in this investigation's process data. Combined with the {c['className'].lower()} "
            f"pattern observed on cell {c['cellId']} and the above-baseline firing temperature recorded for "
            f"this batch, {worst_equipment['equipmentId']} process variation is the probable contributing "
            f"factor (BR-04: presented as probable, not proven)."
        )
        db.add(Recommendation(
            recommendation_id=rec_id, investigation_id=inv_id, authored_by="system:RootCauseAgent",
            autonomy_level="B", ranked_actions=ranked, filtered_actions=filtered,
            simulation={"currentDefectRatePct": batch["defectRate"],
                        "predictedDefectRatePct": round(batch["defectRate"] * 0.7, 1),
                        "predictedImprovementPts": round(batch["defectRate"] * 0.3, 1),
                        "disclaimer": "Predicted outcome — not a guaranteed result (FR-10)."},
            approval=approval, reasoning=reasoning, created_at=days_ago(10 - i),
        ))

    # ---- Autonomy config & safety constraints ----
    print("Seeding autonomy config & safety constraints ...")
    db.add(AutonomyConfig(line_id="L1", autonomy_level="A", fail_closed_override=False, updated_by="u-rchen"))
    db.add(AutonomyConfig(line_id="L2", autonomy_level="B", fail_closed_override=False, updated_by="u-rchen"))
    db.add(SafetyConstraint(constraint_id="sc-001", line_id="L2", description="No unattended component replacement",
                             rule_expression="action.type != 'replace_component' OR maintenance_window.active"))
    db.add(SafetyConstraint(constraint_id="sc-002", line_id="L2", description="Cap single-step temperature adjustment",
                             rule_expression="action.parameter != 'firing_temperature' OR abs(action.delta) <= 15"))

    # ---- Audit log ----
    print("Seeding audit log ...")
    audit_rows = [
        {"eventId": "e1", "timestamp": days_ago(9), "actor": "u-jalvarez", "action": "approve_recommendation",
         "targetType": "recommendation", "targetId": "rec-3391"},
        {"eventId": "e2", "timestamp": days_ago(20), "actor": "u-rchen", "action": "register_camera",
         "targetType": "camera", "targetId": "CAM-EL-07"},
        {"eventId": "e3", "timestamp": days_ago(19), "actor": "u-jalvarez", "action": "approve_retrain",
         "targetType": "retraining_run", "targetId": "RUN-2198"},
        {"eventId": "e4", "timestamp": days_ago(3), "actor": "u-rchen", "action": "publish_taxonomy_version",
         "targetType": "taxonomy_version", "targetId": "v1.4"},
        {"eventId": "e5", "timestamp": days_ago(12), "actor": "u-jalvarez", "action": "approve_retrain",
         "targetType": "retraining_run", "targetId": "RUN-2205"},
    ]
    for a in audit_rows:
        db.add(AuditLogEntry(event_id=a["eventId"], timestamp=a["timestamp"], actor=a["actor"], tenant_id="t1",
                              action=a["action"], target_type=a["targetType"], target_id=a["targetId"],
                              before_state=None, after_state=None))

    db.commit()

    return {
        "roles": len(roles), "users": len(users), "taxonomy": len(existing_taxonomy) + len(NEW_TAXONOMY_ENTRIES),
        "equipment": len(equipment), "cameras": len(cameras), "batches": len(batches), "cells": len(all_cells),
        "model_versions": len(model_versions), "retraining_runs": len(runs), "investigations": len(sample_cells),
        "recommendations": len(sample_cells), "audit_log": len(audit_rows),
    }


def main():
    print("Resetting database and static image directory ...")
    reset_database()
    reset_static_images()

    db = SessionLocal()
    try:
        counts = seed(db)
    finally:
        db.close()

    print("\nSeed complete. Row counts:")
    for table, count in counts.items():
        print(f"  {table}: {count}")
    print(f"\nDatabase: {engine.url.database}")
    print(f"Images:   {STATIC_IMAGES_DIR}")


if __name__ == "__main__":
    main()
