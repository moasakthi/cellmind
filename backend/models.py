from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String

from database import Base


class Role(Base):
    __tablename__ = "roles"
    role_id = Column("roleId", String, primary_key=True)
    role_name = Column("roleName", String, nullable=False)
    permissions = Column("permissions", JSON, nullable=False, default=list)


class User(Base):
    __tablename__ = "users"
    user_id = Column("userId", String, primary_key=True)
    tenant_id = Column("tenantId", String, nullable=False)
    name = Column("name", String, nullable=False)
    email = Column("email", String, nullable=False)
    role_id = Column("roleId", String, ForeignKey("roles.roleId"), nullable=False)
    sso_subject = Column("ssoSubject", String, nullable=True)
    created_at = Column("createdAt", String, nullable=False)


class Batch(Base):
    __tablename__ = "batches"
    batch_id = Column("batchId", String, primary_key=True)
    tenant_id = Column("tenantId", String, nullable=False)
    production_date = Column("productionDate", String, nullable=False)
    line_id = Column("lineId", String, nullable=False)
    cell_count = Column("cellCount", Integer, nullable=False)
    good_count = Column("goodCount", Integer, nullable=False)
    defect_count = Column("defectCount", Integer, nullable=False)
    yield_pct = Column("yield", Float, nullable=False)
    defect_rate = Column("defectRate", Float, nullable=False)
    risk_level = Column("riskLevel", String, nullable=False)


class Cell(Base):
    __tablename__ = "cells"
    cell_id = Column("cellId", String, primary_key=True)
    batch_id = Column("batchId", String, ForeignKey("batches.batchId"), nullable=False)
    image_path = Column("imagePath", String, nullable=False)
    defect_probability = Column("defectProbability", Float, nullable=False)
    severity = Column("severity", String, nullable=False)
    confidence = Column("confidence", Float, nullable=False)
    ood_flag = Column("oodFlag", Boolean, nullable=False, default=False)
    taxonomy_id = Column("taxonomyId", String, ForeignKey("taxonomy.taxonomyId"), nullable=True)
    voc = Column("voc", Float, nullable=False)
    isc = Column("isc", Float, nullable=False)
    fill_factor = Column("fillFactor", Float, nullable=False)
    efficiency = Column("efficiency", Float, nullable=False)
    series_resistance = Column("seriesResistance", Float, nullable=False)


class ProcessRecord(Base):
    __tablename__ = "process"
    process_id = Column("processId", String, primary_key=True)
    batch_id = Column("batchId", String, ForeignKey("batches.batchId"), nullable=False)
    stage = Column("stage", String, nullable=False)
    equipment_id = Column("equipmentId", String, ForeignKey("equipment.equipmentId"), nullable=False)
    temperature = Column("temperature", Float, nullable=False)
    duration = Column("duration", Float, nullable=False)
    pressure = Column("pressure", Float, nullable=False)
    gas_flow = Column("gasFlow", Float, nullable=False)
    timestamp = Column("timestamp", String, nullable=False)


class Equipment(Base):
    __tablename__ = "equipment"
    equipment_id = Column("equipmentId", String, primary_key=True)
    equipment_type = Column("equipmentType", String, nullable=False)
    operating_hours = Column("operatingHours", Float, nullable=False)
    maintenance_date = Column("maintenanceDate", String, nullable=False)
    status = Column("status", String, nullable=False)
    units_produced = Column("unitsProduced", Integer, nullable=False)
    defective_units = Column("defectiveUnits", Integer, nullable=False)


class Camera(Base):
    __tablename__ = "cameras"
    camera_id = Column("cameraId", String, primary_key=True)
    tenant_id = Column("tenantId", String, nullable=False)
    camera_type = Column("cameraType", String, nullable=False)
    el_capable = Column("elCapable", Boolean, nullable=False, default=False)
    model = Column("model", String, nullable=False)
    line_id = Column("lineId", String, nullable=False)
    station_id = Column("stationId", String, nullable=False)
    stream_url = Column("streamUrl", String, nullable=False)
    status = Column("status", String, nullable=False)
    last_frame_at = Column("lastFrameAt", String, nullable=False)
    retention_days = Column("retentionDays", Integer, nullable=False, default=90)


class Investigation(Base):
    __tablename__ = "investigations"
    investigation_id = Column("investigationId", String, primary_key=True)
    batch_id = Column("batchId", String, ForeignKey("batches.batchId"), nullable=False)
    cell_id = Column("cellId", String, ForeignKey("cells.cellId"), nullable=True)
    status = Column("status", String, nullable=False)
    agents = Column("agents", JSON, nullable=False, default=dict)
    created_at = Column("createdAt", String, nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"
    recommendation_id = Column("recommendationId", String, primary_key=True)
    investigation_id = Column("investigationId", String, ForeignKey("investigations.investigationId"), nullable=False)
    authored_by = Column("authoredBy", String, nullable=False)
    autonomy_level = Column("autonomyLevel", String, nullable=False)
    ranked_actions = Column("rankedActions", JSON, nullable=False, default=list)
    filtered_actions = Column("filteredActions", JSON, nullable=False, default=list)
    simulation = Column("simulation", JSON, nullable=True)
    approval = Column("approval", JSON, nullable=True)
    reasoning = Column("reasoning", String, nullable=True)
    created_at = Column("createdAt", String, nullable=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    model_version_id = Column("modelVersionId", String, primary_key=True)
    model_name = Column("modelName", String, nullable=False)
    version = Column("version", String, nullable=False)
    tenant_id = Column("tenantId", String, nullable=False)
    trained_on_date = Column("trainedOnDate", String, nullable=False)
    holdout_metric = Column("holdoutMetric", Float, nullable=False)
    status = Column("status", String, nullable=False)
    approved_by = Column("approvedBy", String, ForeignKey("users.userId"), nullable=True)


class RetrainingRun(Base):
    __tablename__ = "retraining_runs"
    run_id = Column("runId", String, primary_key=True)
    model_version_id = Column("modelVersionId", String, ForeignKey("model_versions.modelVersionId"), nullable=False)
    model_name = Column("modelName", String, nullable=False)
    requested_by = Column("requestedBy", String, ForeignKey("users.userId"), nullable=False)
    trigger_type = Column("triggerType", String, nullable=False)
    status = Column("status", String, nullable=False)
    holdout_result = Column("holdoutResult", Float, nullable=True)
    canary_result = Column("canaryResult", Float, nullable=True)
    created_at = Column("createdAt", String, nullable=False)


class DefectTaxonomyEntry(Base):
    __tablename__ = "taxonomy"
    taxonomy_id = Column("taxonomyId", String, primary_key=True)
    category = Column("category", String, nullable=False)
    subtype = Column("subtype", String, nullable=False)
    severity = Column("severity", String, nullable=False)
    root_cause_family = Column("rootCauseFamily", String, nullable=False)
    suggested_action = Column("suggestedAction", String, nullable=False)
    taxonomy_version = Column("taxonomyVersion", String, ForeignKey("taxonomy_versions.versionId"), nullable=False)


class TaxonomyVersion(Base):
    __tablename__ = "taxonomy_versions"
    version_id = Column("versionId", String, primary_key=True)
    published_at = Column("publishedAt", String, nullable=False)
    published_by = Column("publishedBy", String, ForeignKey("users.userId"), nullable=False)
    changelog = Column("changelog", String, nullable=False)
    compatibility_issues = Column("compatibilityIssues", JSON, nullable=False, default=list)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"
    event_id = Column("eventId", String, primary_key=True)
    timestamp = Column("timestamp", String, nullable=False)
    actor = Column("actor", String, ForeignKey("users.userId"), nullable=False)
    tenant_id = Column("tenantId", String, nullable=False)
    action = Column("action", String, nullable=False)
    target_type = Column("targetType", String, nullable=False)
    target_id = Column("targetId", String, nullable=False)
    before_state = Column("beforeState", JSON, nullable=True)
    after_state = Column("afterState", JSON, nullable=True)


class AutonomyConfig(Base):
    __tablename__ = "autonomy_config"
    line_id = Column("lineId", String, primary_key=True)
    autonomy_level = Column("autonomyLevel", String, nullable=False)
    fail_closed_override = Column("failClosedOverride", Boolean, nullable=False, default=False)
    updated_by = Column("updatedBy", String, ForeignKey("users.userId"), nullable=False)


class SafetyConstraint(Base):
    __tablename__ = "safety_constraints"
    constraint_id = Column("constraintId", String, primary_key=True)
    line_id = Column("lineId", String, nullable=False)
    description = Column("description", String, nullable=False)
    rule_expression = Column("ruleExpression", String, nullable=False)


class AiInsight(Base):
    __tablename__ = "ai_insights"
    insight_id = Column("insightId", String, primary_key=True)
    tenant_id = Column("tenantId", String, nullable=False)
    generated_at = Column("generatedAt", String, nullable=False)
    generated_by = Column("generatedBy", String, nullable=True)
    model = Column("model", String, nullable=False)
    summary = Column("summary", String, nullable=False)
    confidence_band = Column("confidenceBand", String, nullable=False)
    findings = Column("findings", JSON, nullable=False, default=list)
