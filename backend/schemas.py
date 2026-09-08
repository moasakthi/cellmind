from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ActingUserMixin(CamelModel):
    acting_user_id: Optional[str] = Field(None, alias="actingUserId")


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class CameraCreateRequest(ActingUserMixin):
    camera_type: str = Field(alias="cameraType")
    el_capable: bool = Field(False, alias="elCapable")
    model: str = ""
    stream_url: str = Field(alias="streamUrl")
    line_id: str = Field(alias="lineId")
    station_id: str = Field(alias="stationId")
    retention_days: int = Field(90, alias="retentionDays")


class InvestigationCreateRequest(CamelModel):
    batch_id: str = Field(alias="batchId")
    cell_id: Optional[str] = Field(None, alias="cellId")


class ApprovalDecisionRequest(ActingUserMixin):
    decision: str
    rationale_override: Optional[str] = Field(None, alias="rationaleOverride")


class SimulationRequest(CamelModel):
    batch_id: str = Field(alias="batchId")
    parameter: str
    adjustment: str


class RetrainingRunCreateRequest(ActingUserMixin):
    model_name: str = Field(alias="modelName")
    trigger_type: str = Field(alias="triggerType")


class TaxonomyEntryIn(CamelModel):
    taxonomy_id: str = Field(alias="taxonomyId")
    category: str
    subtype: str
    severity: str
    root_cause_family: str = Field(alias="rootCauseFamily")
    suggested_action: str = Field(alias="suggestedAction")
    taxonomy_version: str = Field(alias="taxonomyVersion")


class TaxonomyVersionCreateRequest(ActingUserMixin):
    changelog: str
    based_on_version_id: Optional[str] = Field(None, alias="basedOnVersionId")
    entries: list[TaxonomyEntryIn] = []


class RoleAssignRequest(ActingUserMixin):
    role_id: str = Field(alias="roleId")


class AutonomyConfigIn(ActingUserMixin):
    line_id: str = Field(alias="lineId")
    autonomy_level: str = Field(alias="autonomyLevel")
    fail_closed_override: bool = Field(False, alias="failClosedOverride")


class SafetyConstraintIn(ActingUserMixin):
    constraint_id: Optional[str] = Field(None, alias="constraintId")
    line_id: str = Field(alias="lineId")
    description: str
    rule_expression: str = Field(alias="ruleExpression")


class ChatMessage(CamelModel):
    role: str
    content: str


class ChatRequest(CamelModel):
    messages: list[ChatMessage]
