# Detailed Design Document (DDD)

## CellMind – AI-Powered Solar Cell Manufacturing Intelligence

**Document Version:** 1.1
**Document Type:** Detailed Design Document (Technical/Low-Level Design)
**Reference Document:** BRD.MD v1.2
**Target Industry:** Solar Cell Manufacturing
**Primary IP:** Synapt Agent Hub
**Supporting IP:** Synapt Data Transformation, Synapt Context Substrate

**Change Log:**

* v1.0 — Initial detailed design derived from BRD.MD v1.2, covering architecture, agent orchestration, data, API, security/RBAC, retraining pipeline, camera/RTSP ingestion, autonomy/safety design, and deployment.
* v1.1 — Added Motion & Interaction Design (§16.1): Framer Motion across the product UI (restrained) and the public landing page (rich, React Bits-supplemented); specified the landing page as a separate, data-independent static surface.

---

# 1. Introduction

## 1.1 Purpose

This document translates the CellMind Business Requirements Document (BRD.MD v1.2) into an implementable technical design: system architecture, component responsibilities, data schema, API contracts, agent orchestration logic, and the detailed design of the five extended capabilities (RTSP/camera ingestion, real-time model retraining, autonomous decision support, defect taxonomy, RBAC).

## 1.2 Scope

Covers design for all functional requirements FR-01–FR-22, non-functional requirements NFR-01–NFR-05, and business rules BR-01–BR-11 defined in the BRD. Follows the same delivery tiering as BRD Section 43 (Hackathon Demo / Pilot / Enterprise) — this document designs for the Enterprise end-state and calls out explicitly, per component, what is simplified or stubbed for the Hackathon Demo tier.

## 1.3 References

* BRD.MD v1.2 — Business Requirements Document (authoritative source for all FR/NFR/BR numbers referenced throughout this document).

## 1.4 Definitions / Acronyms

| Term | Meaning |
|---|---|
| Agent Hub | Synapt Agent Hub — the multi-agent orchestration runtime |
| Context Substrate | Synapt Context Substrate — enterprise memory (SOPs, incidents, history) |
| EL | Electroluminescence (a biased, dark-chamber cell-imaging technique) |
| OOD | Out-of-distribution (an input unlike anything the model was trained on) |
| SoD | Segregation of Duties |
| RBAC | Role-Based Access Control |
| MLOps | Machine Learning Operations (the retraining/deployment pipeline) |

---

# 2. Design Goals, Principles & Constraints

## 2.1 Design Goals

1. Every AI output must be explainable and evidence-linked (NFR-02) — no component may return a bare score without supporting evidence references.
2. No component may silently fabricate data for a missing input (BR-03) — missing data must propagate as reduced confidence, not a default/guessed value.
3. No component may take a production-affecting action without a logged, distinct human approver (BR-05, BR-10).
4. The system must degrade gracefully: camera loss, agent failure, model failure or timeout must never block production (BR-11) unless a line is explicitly configured fail-closed.
5. Every extended capability (camera ingestion, retraining, autonomy, taxonomy, RBAC) must be buildable at Hackathon-Demo fidelity without redesign at Pilot/Enterprise fidelity — only configuration and scale should change (BRD Section 43 delivery tiers).

## 2.2 Architectural Principles

* **Composable agents, not a monolith.** Each Agent Hub agent is a stateless unit with a fixed input/output contract, independently testable and independently swappable (e.g., the Inspection Agent's underlying model can change without touching the Root Cause Agent).
* **Evidence flows with the data, not just the verdict.** Every agent output carries `evidence[]` alongside its `result` — this is enforced at the schema level (Section 4.4), not left to convention.
* **Approval gates are first-class objects**, not a status flag on an existing row. A `RetrainingRun` or `Recommendation` is only ever promoted/approved through an `Approval` record that names a distinct approver (Section 8.3), giving BR-10 a concrete enforcement point rather than a policy note.
* **Configuration over code for autonomy and safety.** Autonomy level, safety constraints and rollout thresholds are stored as versioned configuration (Section 8), not hard-coded, so the same codebase serves Level A and Level B without a release.

## 2.3 Constraints

* Production parameters are never written to by CellMind (BR-07); all actuation is manual, by an engineer, outside this system.
* Level C (closed-loop) is designed for at the data-model level (an `autonomy_level` enum already includes `C`) but the code path that would execute it is intentionally unimplemented until the FR-20 gating criteria are met — this is a deliberate design stub, not an oversight.

---

# 3. System Architecture

## 3.1 Architecture Overview

```text
                         ┌───────────────────────────┐
                         │   React Dashboard (Web)    │
                         └─────────────┬─────────────┘
                                       │ HTTPS / REST + WebSocket
                                       ▼
                         ┌───────────────────────────┐
                         │   API Gateway (FastAPI)    │
                         │  AuthN (JWT) · AuthZ (RBAC)│
                         └─────────────┬─────────────┘
                                       │
        ┌───────────────┬─────────────┼─────────────┬───────────────┐
        ▼               ▼             ▼             ▼               ▼
 ┌─────────────┐ ┌───────────────┐ ┌─────────┐ ┌───────────┐ ┌──────────────┐
 │  Camera /   │ │ Synapt Agent  │ │ Taxonomy│ │ Retraining│ │ RBAC/Identity│
 │ RTSP Ingest │ │      Hub      │ │ Service │ │ Orchestr. │ │   Service    │
 └──────┬──────┘ └───────┬───────┘ └────┬────┘ └─────┬─────┘ └──────┬───────┘
        │                │              │            │              │
        │        ┌───────┴────────┐     │            │              │
        │        ▼                ▼     │            │              │
        │   ┌─────────┐      ┌─────────┐│            │              │
        │   │CV Model │      │ML Models││            │              │
        │   │(Inspect)│      │(Process)││            │              │
        │   └────┬────┘      └────┬────┘│            │              │
        │        │                │     │            │              │
        │        └───────┬────────┘     │            │              │
        │                ▼              │            │              │
        │       ┌──────────────────┐    │            │              │
        │       │ Synapt Context   │◄───┘            │              │
        │       │   Substrate      │                 │              │
        │       │ (SOPs/incidents/ │                 │              │
        │       │  history, vector │                 │              │
        │       │  + relational)   │                 │              │
        │       └────────┬─────────┘                 │              │
        └────────────────┼───────────────────────────┼──────────────┘
                          ▼                           ▼
                 ┌──────────────────────────────────────────┐
                 │              Data Layer                   │
                 │  PostgreSQL │ Object Store │ Model Registry│
                 │  (relational) │ (frames/images) │ (MLflow) │
                 └──────────────────────────────────────────┘
                          │
                          ▼
                 ┌──────────────────────────────────────────┐
                 │        Audit Log & Observability          │
                 │   (structured logs, metrics, traces)      │
                 └──────────────────────────────────────────┘
```

## 3.2 Component Responsibilities

| Component | Responsibility | Primary FR/NFR |
|---|---|---|
| React Dashboard | Batch views, investigation UI, camera/taxonomy/RBAC admin, retraining console, approval actions | FR-01, FR-12, all admin FRs |
| API Gateway (FastAPI) | Request routing, JWT validation, RBAC permission checks, request/response schema validation | FR-22, NFR-04 |
| Camera / RTSP Ingest | Stream connection, frame sampling, health checks, EL-capability validation, retention enforcement | FR-18 |
| Synapt Agent Hub | Orchestrates the 7-agent investigation pipeline; owns the investigation state machine | FR-06, FR-07, Section 4 |
| CV Model Service | EL image inference: defect probability, severity, confidence, OOD flag | FR-02, FR-03, FR-15 |
| Process ML Service | Process-parameter anomaly detection, equipment correlation (rate-normalized) | FR-04, FR-05 |
| Synapt Context Substrate | Retrieval of SOPs, historical batches/incidents, prior corrective actions (structured + vector search) | FR-08 |
| Optimization/Simulation Service | Corrective-action generation, cost/impact scoring, what-if simulation, ranking | FR-09, FR-10, FR-11 |
| Retraining Orchestrator | Drift monitoring, labeling workflow, training pipeline, holdout evaluation, staged rollout, rollback | FR-19 |
| Taxonomy Service | CRUD + versioning of defect taxonomy, model-compatibility check | FR-21 |
| RBAC / Identity Service | Roles, permissions, SSO federation, tenant scoping, SoD enforcement | FR-22, BR-10 |
| Audit Log Service | Append-only log of all sensitive operations | NFR-05 |
| Data Layer | PostgreSQL (system of record), object store (frames/images), model registry (artifacts) | — |

## 3.3 Deployment Tiers

Mirrors BRD Section 43. The architecture above is the Enterprise target; lower tiers subset it rather than redesign it:

| Tier | What's real | What's simulated/stubbed |
|---|---|---|
| Hackathon Demo | Single CV model, single camera/recorded stream, single-node Postgres, 2 RBAC roles, local auth | Retraining pipeline runs against a pre-staged run (no live training job); SSO stubbed; single tenant only |
| Pilot | Real ingestion at pilot-line scale, scheduled retraining pipeline, basic SSO | Level C untouched; taxonomy limited to pilot defect types |
| Enterprise | Multi-line/multi-camera, continuous retraining, full RBAC/SSO/multi-tenant, full taxonomy | Level C remains gated by FR-20 criteria regardless of tier |

---

# 4. Synapt Agent Hub — Orchestration & Agent Design

## 4.1 Orchestration Model

The Agent Hub executes the investigation workflow as a directed graph, not a rigid linear script — this lets independent agents run concurrently while still enforcing the dependencies the BRD's evidence model requires (e.g., Root Cause Agent cannot run until both Inspection and Process agents have returned).

```text
Inspection Agent ──┐
                    ├──► Context Agent ──► Root Cause Agent ──► Optimization Agent ──► Simulation Agent ──► [Human Approval] ──► Validation Agent
Process Agent ──────┘
```

* Inspection Agent and Process Agent run in parallel (independent data sources).
* Context Agent starts once either upstream agent returns a preliminary signal (it can begin historical retrieval keyed on batch/equipment ID before full evidence is in), but Root Cause Agent blocks until Inspection, Process and Context have all returned.
* Optimization Agent and Simulation Agent run sequentially (simulation scores the actions optimization proposes).
* Validation Agent runs asynchronously, triggered by the *next* batch's inspection results referencing the approved action — not part of the synchronous investigation request.

## 4.2 Agent Catalog

| Agent | Input | Output | Notes |
|---|---|---|---|
| Inspection Agent | EL image / camera frame | `defect_probability`, `severity`, `confidence`, `ood_flag` | Wraps CV Model Service; enforces FR-03 image-quality gate before inference |
| Process Agent | Batch process parameters | `anomalies[]` (parameter, baseline, deviation) | Wraps Process ML Service |
| Context Agent | Batch/equipment ID, defect category | `historical_matches[]`, `sop_refs[]` | Queries Synapt Context Substrate |
| Root Cause Agent | Outputs of the three agents above | `probable_causes[]` with `confidence`, `evidence[]` | Implements FR-06/FR-07; never emits a cause without ≥1 evidence item (see Section 4.4) |
| Optimization Agent | `probable_causes[]` | `candidate_actions[]` with cost/impact estimate | Implements FR-09/FR-11 |
| Simulation Agent | `candidate_actions[]` | `predicted_outcome` per action | Implements FR-10; always labels output as a prediction, never a guarantee |
| Validation Agent | Approved action + subsequent batch outcome | `predicted_vs_actual` variance | Implements FR-13; writes to `Incident.outcome` |

## 4.3 Investigation Sequence (Hackathon Demo Scenario)

```text
User               API Gateway        Agent Hub                 Data Layer
 │  select batch        │                 │                         │
 │─────────────────────►│                 │                         │
 │                       │──investigate───►│                         │
 │                       │                 │──run Inspection+Process─►│
 │                       │                 │◄────results─────────────│
 │                       │                 │──run Context────────────►│
 │                       │                 │◄────history──────────────│
 │                       │                 │──run RootCause───────────►│
 │                       │                 │◄────probable cause────────│
 │                       │                 │──run Optimization+Sim────►│
 │                       │◄──ranked options + prediction──────────────│
 │◄──displayed to user───│                 │                         │
 │  approve action       │                 │                         │
 │─────────────────────►│──record Approval (approver ≠ author, BR-10)►│
 │                       │                 │                         │
 │        (next batch)   │                 │──run Validation──────────►│
 │                       │◄──outcome comparison──────────────────────│
```

## 4.4 Agent Message Contract

Every agent, regardless of type, returns the same envelope shape so the Root Cause Agent (and the UI) can treat evidence uniformly:

```text
AgentResult {
  agent_name: string
  result: object            // agent-specific payload
  confidence: float [0-1]
  evidence: EvidenceItem[]  // never empty when confidence > "low" threshold (FR-14)
  data_gaps: string[]       // e.g. ["firing_temperature missing"] — drives confidence reduction, BR-03
  ood_flag: bool            // true if input unlike training distribution (FR-15)
}

EvidenceItem {
  source_type: enum(image, process_param, equipment, historical_incident, sop)
  source_ref: string        // e.g. "Batch B1632", "SOP-114"
  description: string
}
```

This contract is what makes NFR-02 (Explainability) and BR-04 (probable-cause framing, not proven causality) enforceable in code rather than only in prose: the UI renders `evidence[]` directly and a Root Cause Agent output with an empty `evidence[]` is rejected at the schema layer before it reaches a user.

---

# 5. Core Functional Design (FR-01–FR-17)

| FR | Design Summary |
|---|---|
| FR-01 Batch Management | `Batch` table + `/batches` API; dashboard aggregates `good_count`/`defect_count`/`yield` computed on write (trigger or application-layer aggregation), not recomputed per-read, to hit the <3s dashboard NFR-01 target. |
| FR-02 Solar Cell Inspection | CV Model Service (EfficientNet-B0/ResNet18) behind an inference endpoint; returns `defect_probability`, `severity`, `confidence`. |
| FR-03 Image Quality Validation | A lightweight pre-check (blur/exposure/dimension heuristics, e.g. Laplacian-variance blur detection) runs before the CV model; a failing check short-circuits inference and returns the BRD's fixed rejection message rather than a low-confidence classification. |
| FR-04 Process Monitoring | Process ML Service flags parameters outside configured baseline ranges (per-parameter thresholds stored in `ProcessBaseline` config, not hard-coded, so plants can tune without a release). |
| FR-05 Equipment Correlation | Correlation query joins `Cell.defect_probability` against `Process.equipment_id` and **`Batch`/`Process` unit-produced counts**, computing `defect_rate = defective/units_produced` alongside `share_of_defects`, per BRD's rate-normalization fix — both values returned so the UI never shows share-of-defects without its rate counterpart. |
| FR-06 Root-Cause Analysis | Root Cause Agent combines the four evidence sources via a weighted-evidence scoring function (Section 5.1) and always frames the result as a "probable contributing factor" string template, never a "confirmed cause" template (BR-04 enforced at the template layer). |
| FR-07 Evidence-Based Explanation | UI evidence panel renders directly from `AgentResult.evidence[]` (Section 4.4) — no separate "explanation" is authored after the fact. |
| FR-08 Historical Context | Context Agent performs a hybrid query: structured filter (same equipment/defect category) + vector-similarity search over incident/SOP embeddings in the Context Substrate, returning top-k matches with a similarity score shown to the user. |
| FR-09 Corrective Action Generation | Optimization Agent enumerates candidate actions from an `ActionCatalog` config (per probable-cause-family → applicable actions), each annotated with a cost tier and a historical expected-improvement estimate drawn from `Incident.outcome` records. |
| FR-10 What-If Simulation | Simulation Agent applies the same process-anomaly model in "counterfactual" mode: re-scores the batch's process data with one parameter adjusted, and reports the resulting predicted defect rate; UI always prefixes the result with "Predicted" (never "Result"). |
| FR-11 Action Optimization | Ranking function: `score = w1·expected_yield_improvement − w2·normalized_cost − w3·downtime − w4·risk`, weights configurable per deployment (business-priority config), consumed identically by FR-11 ranking and FR-20 autonomy (Section 8). |
| FR-12 Human-in-the-Loop | No API path exists that writes to `Process`/`Equipment` tables from an agent or automated job — those tables are read-only to the AI layer by construction, not just by convention. |
| FR-13 Validation | Validation Agent is triggered by the next batch's ingestion event referencing the same equipment/action; writes `predicted_vs_actual` variance to `Incident.outcome`. |
| FR-14 Confidence & Uncertainty | Confidence thresholds (`high`/`medium`/`low`/`conflicting`) are a config table (`ConfidenceThresholds`), evaluated identically across all agents so behavior in the BRD's confidence table is centrally enforced, not reimplemented per agent. |
| FR-15 OOD Detection | CV Model Service computes an embedding-distance or softmax-entropy OOD score alongside the classification; above a configured threshold, `ood_flag=true` short-circuits to the "unknown defect pattern" response regardless of raw classification confidence. |
| FR-16 Missing Data Handling | Each agent populates `data_gaps[]` (Section 4.4) instead of defaulting a missing field to zero/normal; Root Cause Agent's confidence calculation subtracts a penalty per gap rather than treating a gap as a neutral value. |
| FR-17 Conflicting Evidence | Root Cause Agent detects conflict when evidence sources disagree beyond a configured divergence threshold (e.g., image says high-defect, process says normal, no historical match) and returns the "evidence conflict" response instead of a ranked cause. |

## 5.1 Root-Cause Evidence Scoring (detail for FR-06/FR-14)

```text
confidence = base_confidence(model_scores)
             − Σ(gap_penalty for each entry in data_gaps)
             − conflict_penalty (if FR-17 conflict detected)

if confidence >= HIGH_THRESHOLD:      → "AI recommendation available"
elif confidence >= MEDIUM_THRESHOLD:  → "Recommend engineering review"
elif conflict_detected:               → "Manual investigation required"
else:                                 → "Insufficient evidence"
```

Thresholds live in `ConfidenceThresholds` config (Section 6.2), matching BRD FR-14's requirement that "exact thresholds shall be configurable."

---

# 6. Camera / RTSP Ingestion Design (FR-18)

## 6.1 Component Design

```text
RTSP/Camera Source ──► Stream Connector ──► Frame Sampler ──► Frame Queue ──► CV Model Service
        │                     │                                    │
        │                     ▼                                    ▼
        │              Health Monitor                        Retention Enforcer
        │              (heartbeat, reconnect)                 (per-policy purge)
        ▼
  Camera Registry (camera_id, type, EL-capable flag, line/station, credentials ref)
```

* **Registration & EL-capability gate.** A camera is registered with `camera_type ∈ {EL, visual}`. Only cameras explicitly flagged `el_capable=true` (with recorded capture-condition metadata — bias voltage present, dark-chamber confirmed) may be bound to an EL inspection station; a generic `visual`/RTSP camera registered without that flag is rejected at bind-time from EL use, directly implementing the BRD's requirement not to assume a generic feed is EL-sufficient.
* **Transport security.** Stream Connector only accepts `rtsps://` (RTSP over TLS) or a stream reachable solely via a segmented/VPN network; credentials are stored in a secrets vault referenced by `credentials_ref`, never persisted in the `Camera` row itself.
* **Frame sampling.** Default 1 frame / 5 seconds per stream, configurable per camera; an anomaly signal from the Process Agent can trigger a temporary burst-sampling mode (e.g., 1 fps for 60s) for a given station.
* **Health monitoring.** Heartbeat check every 30s; three consecutive misses → `status=DEGRADED`; sustained failure → `status=OFFLINE` with an alert to the Platform Administrator. Reconnection is automatic with exponential backoff; frames are neither fabricated nor backfilled for the gap.
* **Retention.** Sampled frames retained per a configurable policy (default 90 days) in object storage; raw continuous video is never persisted by default. A scheduled job purges frames past retention.

## 6.2 Failure Behavior

Per BR-11 (fail-open), a disconnected camera does not halt the line: the station falls back to manual/upload-based inspection, and the dashboard surfaces `Stream Health: DEGRADED/OFFLINE` rather than silently reporting "no defects found."

---

# 7. Real-Time Model Retraining / MLOps Design (FR-19)

## 7.1 Pipeline Stages

```text
 (1) Trigger           (2) Label Collection      (3) Data Validation
 ─────────────         ────────────────────      ───────────────────
 Scheduled / Drift  ──►  Engineer-confirmed   ──►  Schema check
 alert / Manual          labels (primary) +        Class-balance check
 request                 auto-labels (flagged      Minimum-volume guardrail
                          low-trust)

 (4) Training          (5) Holdout Evaluation    (6) Staged Rollout
 ─────────────         ────────────────────      ───────────────────
 Versioned run     ──►  Compare vs current   ──►  Canary traffic %
 → Model Registry       production baseline        + live monitoring

 (7) Approval Gate                    (8) Promotion / Rollback
 ─────────────────                    ─────────────────────────
 ML Operations Lead reviews       ──► Promote: new production version
 holdout + canary metrics             Reject/Rollback: revert to prior
 Requester ≠ Approver (BR-10)          version, retained for this purpose
```

## 7.2 Guardrails (Design Detail)

| Guardrail | Enforcement Point |
|---|---|
| Minimum labeled-data volume | Stage 3 — pipeline halts before training if volume < configured minimum |
| Holdout performance threshold | Stage 5 — candidate must meet/exceed a configured delta vs. baseline (e.g., F1 ≥ baseline − 0 pts) to proceed to staged rollout |
| Auto-label trust weighting | Stage 2 — auto-labeled examples are down-weighted in the training objective and excluded from the holdout set entirely (holdout is always human-confirmed labels) |
| Requester ≠ Approver | Stage 7 — enforced at the API layer: the `/retraining/runs/{id}/approve` endpoint rejects the request if `approver_user_id == requested_by_user_id` (BR-10) |
| Automatic rollback trigger | Stage 6/8 — if canary error rate regresses beyond a configured threshold during the monitoring window, the system auto-reverts to the prior version and notifies the ML Operations Lead; this is the one retraining action allowed to execute without a human approval step, precisely because it is a revert-to-known-good, not a promotion |
| Tenant isolation | Stage 2/4 — training jobs and resulting `ModelVersion` rows are scoped by `tenant_id`; cross-tenant training data access requires an explicit `cross_tenant_share` authorization record |

## 7.3 Drift Detection

A scheduled job compares rolling production-inference confidence/accuracy (where ground truth becomes available via Validation Agent outcomes) against a baseline window; a statistically significant drop (e.g., >X points sustained over N days) raises a `DriftAlert`, which is the primary automatic trigger for Stage 1 above.

---

# 8. Autonomous Decision Support & Safety Design (FR-20)

## 8.1 Autonomy Levels — State Machine

```text
                ┌─────────────────────┐
                │   Level A            │  Recommend-only: ranked list shown,
                │   (Recommend-only)   │  nothing pre-selected
                └──────────┬───────────┘
                           │ config change (Platform Administrator)
                           ▼
                ┌─────────────────────┐
                │   Level B            │  Auto-suggest: top recommendation
                │ (Auto-suggest +      │  pre-selected, requires explicit
                │  human approval)     │  approval from an authorized role
                └──────────┬───────────┘
                           │ blocked — see FR-20 gating criteria
                           ▼
                ┌─────────────────────┐
                │   Level C            │  Closed-loop: NOT implemented.
                │  (Closed-loop,       │  Enum value exists in schema for
                │   future)            │  forward compatibility only.
                └─────────────────────┘
```

`autonomy_level` is per-line configuration (`AutonomyConfig` table), defaulting to Level A. The transition to Level B requires a Platform Administrator change plus the safety-constraint set (below) to be populated for that line; there is intentionally no code path that transitions to Level C — enabling it requires a release, not a configuration change, so the FR-20 gating criteria (safety case, independent validation, sign-off) cannot be bypassed by a config toggle.

## 8.2 Safety Constraint Engine

Each candidate action from the Optimization Agent (Section 5) passes through a rules check before being shown:

```text
for action in candidate_actions:
    for constraint in SafetyConstraints[line_id]:
        if constraint.violated_by(action):
            action.filtered = true
            action.filter_reason = constraint.description
```

Example constraints: max allowable single-step temperature adjustment, no "replace component" auto-suggestion outside a declared maintenance window, no recommendation affecting two furnaces simultaneously without Equipment Engineer review. Filtered actions are logged (not silently dropped) so a Quality/Process Engineer can see what was excluded and why.

## 8.3 Approval & Audit Design

Every recommendation shown at Level B produces a `Recommendation` row with `authored_by = 'system'`. An approval action creates an `Approval` row referencing `recommendation_id`, `approver_user_id`, `decision`, `rationale_override` (if the engineer modified rather than approved as-is). This satisfies FR-20's "logged with rationale, evidence, and any operator override" requirement as a queryable record, not a log line.

## 8.4 Fail-Open Design (BR-11)

If the Optimization/Simulation Agent or Agent Hub itself is unreachable when a batch investigation is requested, the API Gateway returns a degraded-mode response (`investigation_status: "unavailable"`) and the dashboard falls back to displaying raw inspection results without ranked recommendations — production is never gated on this response, consistent with BR-11's default fail-open behavior. A per-line `fail_closed_override` config flag exists for customers who explicitly want the opposite behavior.

---

# 9. Defect Taxonomy Design (FR-21)

## 9.1 Structure & Versioning

```text
DefectTaxonomyEntry (taxonomy_id, category, subtype, severity, root_cause_family, suggested_action, taxonomy_version)
TaxonomyVersion (version_id, published_at, published_by, changelog, based_on_version_id)
TaxonomyMigration (from_category_id, to_category_id, taxonomy_version_from, taxonomy_version_to)
```

New versions are additive by default (old `taxonomy_id`s remain valid and queryable); a breaking change (category removed/merged) requires a `TaxonomyMigration` row so historical `Cell`/`Incident` records can be reclassified without data loss.

## 9.2 Model-Compatibility Check (dependency on FR-19)

On publishing a new `TaxonomyVersion`, a compatibility job compares the CV Model Service's output class list against the new version's categories:

```text
for model_class in CVModel.output_classes:
    if model_class not in NewTaxonomyVersion.categories:
        flag_for_ml_ops_review(model_class)
```

Any flagged mismatch is surfaced to the ML Operations Lead as a `RetrainingRun` candidate reason (`trigger_type = 'taxonomy_change'`), directly wiring FR-21's taxonomy governance into FR-19's retraining pipeline rather than leaving the dependency implicit.

## 9.3 Industry Alignment

The seed taxonomy for v1 is populated from established PV-industry EL-defect classification references (per BRD Assumption 11) rather than authored from scratch; this is a content/data-population task, not a code design concern, but is tracked here so the dependency is visible before FR-21 is considered "done."

---

# 10. RBAC & Security Design (FR-22, NFR-04)

## 10.1 AuthN/AuthZ Flow

```text
User ──login──► RBAC/Identity Service ──(local | SSO/LDAP/SAML)──► JWT issued
                                                                      │
User ──request + JWT──► API Gateway ──validate signature──► extract  │
                                       role + tenant_id ◄─────────────┘
                                       │
                                       ▼
                              Permission check: does role
                              have permission for this route?
                                       │
                              allow ──────────► handler
                              deny  ──────────► 403 + audit log entry
```

## 10.2 Role–Permission Matrix (design-level; full matrix maintained in `RolePermission` table)

| Role | View Data | Request Retrain | Approve Retrain | Approve Recommendation | Manage Cameras | Configure Taxonomy | Manage RBAC |
|---|---|---|---|---|---|---|---|
| Viewer | ✓ | | | | | | |
| Quality Engineer | ✓ | ✓ (flag candidate) | | ✓ (quality actions) | | | |
| Process Engineer | ✓ | ✓ | | ✓ (process actions) | | | |
| Equipment Engineer | ✓ | | | ✓ (equipment actions) | | | |
| Plant/Operations Manager | ✓ | | | | | | |
| Platform Administrator | ✓ | | | | ✓ | ✓ | ✓ |
| ML Operations Lead | ✓ | ✓ | ✓ | | | | |

Note the deliberate asymmetry: Platform Administrator can configure the system but cannot approve a retraining run, and ML Operations Lead can approve retraining but cannot touch RBAC/camera/taxonomy config — this is the Section 2/BRD role split (7.6/7.7) expressed as a permission table, not just a persona description.

## 10.3 Segregation-of-Duties Enforcement (BR-10)

Implemented as a query-time check, not a UI-only restriction, on both approval endpoints:

```text
POST /retraining/runs/{id}/approve
  reject if current_user.id == RetrainingRun.requested_by_user_id

POST /recommendations/{id}/approve
  reject if current_user.id == Recommendation.authored_by_user_id  (n/a when system-authored)
  reject if current_user.role not in allowed_roles_for(action.category)
```

## 10.4 Multi-Tenant Isolation

Every row in `Batch`, `Cell`, `Process`, `Camera`, `ModelVersion`, `DefectTaxonomyEntry` and `User` carries `tenant_id`. All queries are scoped by the requesting user's `tenant_id` at the ORM/query-builder layer (a single shared query helper, not per-endpoint filtering) so a missed filter fails closed rather than leaking cross-tenant data.

## 10.5 Audit Logging

`AuditLog(event_id, timestamp, actor_user_id, tenant_id, action, target_type, target_id, before_state, after_state)` — written for every RBAC change, retraining approval, recommendation approval, and taxonomy publish. Append-only (no update/delete permission at the DB role level).

---

# 11. Data Design

## 11.1 Entity Overview

```text
Tenant ──< User ──< Role (via RolePermission)
Tenant ──< Batch ──< Cell
Batch ──< Process
Batch ──< Incident >── Equipment
Equipment ──< Camera (via line/station mapping)
Cell ── DefectTaxonomyEntry (classified_as)
ModelVersion ── RetrainingRun ── Approval
Recommendation ── Approval
DefectTaxonomyEntry ──< TaxonomyMigration
AuditLog (references any entity via target_type/target_id)
```

## 11.2 Physical Schema (key tables)

```text
Tenant(tenant_id PK, name, created_at)

User(user_id PK, tenant_id FK, name, email, role_id FK, sso_subject, created_at)
Role(role_id PK, role_name)
Permission(permission_id PK, permission_name)
RolePermission(role_id FK, permission_id FK)

Batch(batch_id PK, tenant_id FK, production_date, line_id, cell_count, good_count, defect_count, yield)

Cell(cell_id PK, batch_id FK, image_path, defect_probability, severity, confidence,
     ood_flag, taxonomy_id FK, voc, isc, fill_factor, efficiency, series_resistance)

Process(process_id PK, batch_id FK, stage, equipment_id FK, temperature, duration,
        pressure, gas_flow, timestamp)

Equipment(equipment_id PK, equipment_type, operating_hours, maintenance_date, status)

Incident(incident_id PK, batch_id FK, equipment_id FK, defect_type, probable_cause,
         corrective_action, predicted_outcome, actual_outcome, created_at)

Camera(camera_id PK, tenant_id FK, camera_type, el_capable, model, line_id, station_id,
       stream_url, credentials_ref, status, last_frame_at, retention_days)

ModelVersion(model_version_id PK, model_name, version, tenant_id FK, trained_on_date,
             holdout_metric, status, approved_by FK User)

RetrainingRun(run_id PK, model_version_id FK, requested_by FK User, trigger_type,
              status, holdout_result, canary_result, created_at)

Approval(approval_id PK, target_type, target_id, requested_by FK User, approver FK User,
         decision, rationale_override, decided_at)
       -- CHECK (requested_by <> approver)

Recommendation(recommendation_id PK, investigation_id FK, authored_by, ranked_actions_json,
               autonomy_level, filtered_actions_json, created_at)

DefectTaxonomyEntry(taxonomy_id PK, category, subtype, severity, root_cause_family,
                     suggested_action, taxonomy_version)
TaxonomyVersion(version_id PK, published_at, published_by FK User, changelog)
TaxonomyMigration(from_category_id FK, to_category_id FK, from_version FK, to_version FK)

AutonomyConfig(line_id PK, autonomy_level, fail_closed_override, updated_by FK User)
SafetyConstraint(constraint_id PK, line_id FK, description, rule_expression)

AuditLog(event_id PK, timestamp, actor FK User, tenant_id FK, action, target_type,
         target_id, before_state, after_state)
```

The `Approval` table's `CHECK (requested_by <> approver)` constraint is the database-level backstop for BR-10 — the API-layer check in Section 10.3 is the primary enforcement, but the constraint ensures no code path (including a future one) can bypass it.

---

# 12. API Design

## 12.1 Conventions

* REST over HTTPS, JSON bodies, `Authorization: Bearer <JWT>` on every call except `/auth/*`.
* All list endpoints support tenant-scoped pagination; all responses that include an AI result embed the `AgentResult` evidence envelope (Section 4.4) rather than a bare score.

## 12.2 Endpoint Catalog

| Method | Path | Purpose | Required Permission |
|---|---|---|---|
| POST | /auth/login | Local credential login | — |
| GET | /auth/sso/callback | SSO/SAML/LDAP federation callback | — |
| GET | /batches | List batches (tenant-scoped) | view_data |
| GET | /batches/{id} | Batch detail + quality metrics | view_data |
| POST | /cells/{id}/inspect | Trigger inspection on an uploaded/sampled image | view_data |
| GET | /cameras | List registered cameras | view_data |
| POST | /cameras | Register a camera (EL-capability metadata required for EL use) | manage_cameras |
| GET | /cameras/{id}/health | Stream health status | view_data |
| POST | /investigations | Trigger the Agent Hub pipeline for a batch/cell | view_data |
| GET | /investigations/{id} | Investigation status + evidence | view_data |
| GET | /recommendations/{investigation_id} | Ranked corrective actions | view_data |
| POST | /recommendations/{id}/approve | Approve/override a recommendation | approve_recommendation (role-scoped) |
| POST | /simulations | Run a what-if simulation | view_data |
| GET | /retraining/runs | List retraining runs | view_data |
| POST | /retraining/runs | Request a retraining run | request_retrain |
| POST | /retraining/runs/{id}/approve | Approve/reject promotion (BR-10 enforced) | approve_retrain |
| POST | /retraining/runs/{id}/rollback | Manual rollback | approve_retrain |
| GET | /taxonomy | List taxonomy entries | view_data |
| POST | /taxonomy/versions | Publish a new taxonomy version | configure_taxonomy |
| GET | /rbac/roles | List roles/permissions | manage_rbac |
| POST | /rbac/users/{id}/role | Assign a role | manage_rbac |
| GET | /audit-log | Query audit log | manage_rbac |

---

# 13. Error Handling & Resilience

| Scenario | Design Response |
|---|---|
| Camera/RTSP disconnect | Health Monitor marks DEGRADED/OFFLINE (Section 6.2); station falls back to manual upload; production unaffected (BR-11) |
| Agent failure/timeout | Agent Hub marks that agent's contribution `data_gaps += ["<agent> unavailable"]`; downstream confidence reduced (FR-16), investigation still returns partial results rather than failing entirely |
| Model inference failure | API Gateway returns a typed error; UI shows "inspection temporarily unavailable," not a fabricated result |
| Missing critical process data | Propagated as `data_gaps[]` (Section 4.4/5.1), never defaulted (BR-03) |
| Conflicting evidence | Root Cause Agent short-circuits to the FR-17 conflict response |
| Unknown/OOD defect pattern | CV Model Service `ood_flag` short-circuits to FR-15 response regardless of raw confidence |
| Retraining data insufficient | Pipeline halts at Stage 3 (Section 7.2), no partial/low-quality promotion possible |
| Retrained model regresses in canary | Automatic rollback (Section 7.2), notification to ML Operations Lead |
| RBAC misconfiguration / unauthorized attempt | Deny + audit log entry (Section 10.5); no silent allow |

Standard resilience patterns applied at the API Gateway and inter-service layer: request timeouts on every agent call, retry-with-backoff for transient camera/network errors only (not for validation failures), and a circuit breaker around the CV/Process model services so a model outage degrades gracefully instead of cascading into Agent Hub timeouts.

---

# 14. Non-Functional Design

## 14.1 Performance (NFR-01)

| Target | Design Approach |
|---|---|
| Image analysis <5s | CV inference behind a warm model server (no cold-start per request); pre-check (FR-03) short-circuits before the more expensive inference call |
| Agent investigation <30s | Parallelized Inspection/Process stage (Section 4.1) removes the largest serial bottleneck |
| Dashboard response <3s | Batch-level metrics pre-aggregated on write (Section 5), not computed per dashboard load |
| Camera ingestion | Frame Sampler decouples camera frame rate from CV inference throughput via the Frame Queue, so a burst doesn't stall ingestion |
| Retraining cycle <24h | Pipeline stages (Section 7.1) run as an orchestrated batch job, not on the interactive request path |

## 14.2 Observability

* Structured logs correlated by `investigation_id` / `run_id` across every agent and service hop.
* Metrics: per-agent latency, model inference latency, camera stream uptime, retraining cycle duration, drift-alert frequency, RBAC denial rate.
* Tracing: a single trace spans the full investigation sequence (Section 4.3) so a slow/failing agent is identifiable without log-grepping across services.

## 14.3 Reliability & Auditability

Covered by Sections 13 and 10.5 respectively; NFR-05's auditability requirement (input data, model result, agent recommendation, user decision, final outcome, model-version history, RBAC changes) maps directly to the `AuditLog`, `Approval`, `Incident`, and `ModelVersion` tables in Section 11.2 — every item in that NFR list has a concrete table, not just a logging convention.

---

# 15. Deployment Architecture & Environments

## 15.1 Environments

| Environment | Purpose | Notes |
|---|---|---|
| Dev | Local/CI development | Mocked camera source, synthetic process data |
| Staging | Pre-release validation | Real pipeline stages, synthetic or anonymized data |
| Hackathon Demo | Live demonstration | Matches BRD Section 43 Hackathon tier exactly (Section 3.3 above) |
| Pilot | First customer deployment | Real MES/camera integration at one line/plant |
| Production/Enterprise | Multi-plant deployment | Full multi-tenant, full RBAC/SSO |

## 15.2 CI/CD

```text
Commit ──► Lint/Unit Tests ──► Build Container Images ──► Deploy to Staging
              │                                                │
              └──(model changes)──► Retraining pipeline tests ─┘
                                     (Section 7, holdout gate)
Staging ──► Manual promotion gate ──► Production
```

Model artifacts follow a separate promotion path from application code (Section 7's approval gate), so a code release and a model promotion are never conflated into one deploy action.

## 15.3 Infrastructure (Conceptual)

```text
                 ┌───────────────┐
                 │  Load Balancer │
                 └───────┬───────┘
                         ▼
              ┌─────────────────────┐
              │ API Gateway (N pods) │
              └──────────┬──────────┘
                         ▼
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
 Agent Hub          Model Serving        Camera Ingest
 (N pods)           (GPU pool)           (per-line workers)
     │                   │                   │
     └───────────────────┼───────────────────┘
                         ▼
             PostgreSQL (primary+replica) │ Object Store │ Model Registry
```

---

# 16. Technology Stack

| Layer | Technology | Design Notes |
|---|---|---|
| Frontend | React | Investigation UI, admin consoles (camera, taxonomy, RBAC, retraining) |
| Motion (Product UI) | Framer Motion | Restrained, functional motion on the dashboard/admin consoles — state transitions, list reordering, meter fills (Section 16.1) |
| Motion (Marketing Surface) | Framer Motion + React Bits | Rich, scroll-choreographed motion on the public landing page only — hero sequence, staggered reveals, animated counters (Section 16.1) |
| Backend/API | Python / FastAPI | JWT auth, RBAC middleware, request schema validation (Pydantic) |
| Computer Vision | PyTorch / OpenCV | EfficientNet-B0 / ResNet18 inference |
| Process ML | XGBoost / Random Forest | Anomaly detection + rate-normalized equipment correlation |
| Explainability | SHAP | Feeds `EvidenceItem` generation for process-based findings |
| Data Processing | Pandas | Feature extraction, drift-metric computation |
| Database | PostgreSQL | System of record, tenant-scoped |
| Vector/Context Store | Synapt Context Substrate | Historical/SOP retrieval (hybrid structured + vector) |
| Agent Orchestration | Synapt Agent Hub | DAG-based orchestration (Section 4) |
| Data Transformation | Synapt Data Transformation | Normalization, feature prep for both CV and process pipelines |
| Video Ingestion | OpenCV / GStreamer / FFmpeg over RTSP(S) | Section 6 |
| MLOps / Model Registry | MLflow (or equivalent) | Section 7 |
| Identity / RBAC | OAuth2 / JWT, Keycloak (SSO/LDAP/SAML) | Section 10 |
| Observability | Structured logging + metrics/tracing stack | Section 14.2 |
| Visualization | Plotly | Dashboard charts |

## 16.1 Motion & Interaction Design

CellMind has two distinct motion contexts, deliberately treated differently rather than sharing one animation budget:

* **Product UI (Dashboard, Investigation, Camera/Retraining/Taxonomy/RBAC admin)** — motion is restrained and purely functional: it confirms a state change (approval recorded, stream reconnected, meter filled), never decorates. An engineer scanning a dense batch table in a control room is the target user; anything beyond a 150–250ms transform/opacity transition competes with legibility rather than supporting it.
* **Public landing page** — an editorial surface aimed at prospective customers and hackathon judges, where motion is the pitch's pacing device (Section 16.1.2 below), not an afterthought.

Both contexts use the same underlying token language so a design change in one place doesn't fork the codebase's motion vocabulary:

```text
--motion-fast:    120ms   (press/hover feedback, e.g. button scale 0.97→1)
--motion-base:     220ms   (state transitions: chip color change, meter fill)
--motion-reveal:   450ms   (scroll-triggered entrance, product UI: single elements only)
--motion-hero:      650ms   (landing-page hero sequence steps)
--ease-out:        cubic-bezier(0.16, 1, 0.3, 1)   /* entrances */
--ease-in:         cubic-bezier(0.7, 0, 0.84, 0)    /* exits — always ~65% of the matching entrance duration */
```

### 16.1.1 Product UI — Framer Motion usage

Framer Motion is the implementation library for both contexts (React). On product screens it is used narrowly:

* `layout` prop for list reordering (e.g. ranked action cards re-sorting after a weight-config change) instead of a manual FLIP implementation.
* `AnimatePresence` for modal/approval-dialog enter/exit only (`scale: 0.98→1` + fade, `--motion-base`), matching the `modal-motion` principle of animating from the trigger's spatial origin.
* Confidence-meter fill and stepper-node state changes animate `width`/`background` through a plain CSS transition, not Framer Motion — these are single-property, non-interruptible changes where a library adds no value.
* All product-UI motion respects `prefers-reduced-motion` by disabling `layout`/`AnimatePresence` transitions outright (not just shortening them), since none of them carry information a static state change wouldn't.

### 16.1.2 Landing Page — Framer Motion + React Bits usage

The landing page (Section 16.1.3) is specified against `motion.section`/`motion.div` with `variants` + `whileInView` (not `animate` on mount) so nothing above the fold competes for attention simultaneously:

```text
const reveal = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.16,1,0.3,1] } }
};
// container: variants={{visible:{transition:{staggerChildren:0.08}}}}
// child:     variants={reveal}
// usage:     whileInView="visible" viewport={{ once:true, amount:0.3 }}
```

* **Hero sequence** — a `staggerChildren`-choreographed entrance (eyebrow → headline → sub-copy → live readout panel → CTA), each child using `reveal` above, total sequence ≤1.2s.
* **Section reveals** — every subsequent section's children stagger in on `whileInView` at `amount:0.3`, `once:true` (never re-triggers on scroll-back, per `toggleActions`-equivalent guidance) — this keeps a long scroll from feeling like a slot machine.
* **Animated counters** (KPI numbers, yield/defect-rate stats) — implemented via a small custom hook (`useCountUp`) driven by `whileInView`, not a React Bits component, since the values are data-bound; React Bits is used instead for the presentational primitives below.
* **React Bits components** — used specifically for: the hero's animated gradient/glow text treatment, a magnetic/spotlight hover effect on the five extended-capability cards, and a subtle ambient background (slow-drifting glow blobs behind the hero) — all optional/decorative, so each is wrapped to no-op under `prefers-reduced-motion`.
* **Exit timing** — any dismissible element (e.g. a toast confirming a CTA click) exits in ~65% of its entrance duration, per the token table above.

### 16.1.3 Landing Page as a Component

The landing page is a separate, lightweight static route (`/`), not wired into the authenticated product SPA — it has no dependency on the API Gateway, Agent Hub, or any tenant data; its content (pitch copy, the F07 demo narrative, KPIs) is static/build-time, matching BRD.MD §50–51 (Elevator Pitch, Final Positioning). This keeps the marketing surface from ever being a reason the product's security/tenancy model has to make an exception.

---

# 17. Traceability Matrix

| BRD Requirement | Design Section(s) |
|---|---|
| FR-01 Batch Management | 5, 11.2 (`Batch`) |
| FR-02 Solar Cell Inspection | 4.2, 5 |
| FR-03 Image Quality Validation | 5 |
| FR-04 Process Monitoring | 5 |
| FR-05 Equipment Correlation (rate-normalized) | 5 |
| FR-06 Root-Cause Analysis | 4.2, 4.4, 5.1 |
| FR-07 Evidence-Based Explanation | 4.4 |
| FR-08 Historical Context | 4.2, 3.2 (Context Substrate) |
| FR-09 Corrective Action Generation | 5 |
| FR-10 What-If Simulation | 4.2, 5 |
| FR-11 Action Optimization | 5, 8.1 (shared scoring function) |
| FR-12 Human-in-the-Loop | 2.3, 5 |
| FR-13 Validation | 4.2, 4.3 |
| FR-14 Confidence & Uncertainty | 5.1 |
| FR-15 OOD Detection | 5, 5 (FR-15 row) |
| FR-16 Missing Data Handling | 4.4, 13 |
| FR-17 Conflicting Evidence | 5, 13 |
| FR-18 RTSP/Camera Ingestion | 6 |
| FR-19 Real-Time Model Retraining | 7 |
| FR-20 Autonomous Decision Support | 8 |
| FR-21 Defect Taxonomy | 9 |
| FR-22 RBAC | 10 |
| NFR-01 Performance | 14.1 |
| NFR-02 Explainability | 4.4, 2.2 |
| NFR-03 Reliability | 13 |
| NFR-04 Security | 10 |
| NFR-05 Auditability | 10.5, 14.3 |
| BR-01–BR-07 (human-in-loop, confidence, no fabrication) | 2.1, 4.4, 5.1 |
| BR-08 (autonomy level limits) | 8.1 |
| BR-09 (RBAC governs access) | 10 |
| BR-10 (requester ≠ approver) | 7.2, 8.3, 10.3, 11.2 (`Approval` CHECK constraint) |
| BR-11 (fail-open) | 6.2, 8.4, 13 |

---

# 18. Open Design Decisions, Assumptions & Risks

## 18.1 Open Design Decisions

1. Vector store choice for the Context Substrate (embedded pgvector vs. a dedicated vector DB) — deferred to Pilot phase based on historical-data volume.
2. Exact burst-sampling trigger logic for camera frame rate (Section 6.1) needs a threshold calibrated against real anomaly-detection latency once pilot data exists.
3. Whether `AutonomyConfig` is per-line or per-line-per-defect-category — current design assumes per-line; may need finer granularity once Pilot feedback arrives.

## 18.2 Assumptions Carried from BRD

Inherits BRD Section 44 assumptions (1–11) unchanged; this design does not introduce new assumptions beyond what those already state (camera availability, minimum labeled dataset, RBAC role approximation, industry-taxonomy starting point).

## 18.3 Design-Level Risks

| Risk | Mitigation in This Design |
|---|---|
| Evidence envelope (Section 4.4) becomes a bottleneck if every agent must populate it richly under time pressure | Schema validation rejects empty `evidence[]` only above the "low" confidence threshold — low-confidence paths are exempt, preventing artificial evidence-padding |
| Multi-tenant query helper (Section 10.4) has a single point of failure if bypassed | Enforce via a shared query builder + a CI lint rule that flags direct ORM queries missing a `tenant_id` filter, not review alone |
| Safety Constraint rule language (Section 8.2) could become too expressive/hard to audit | Start with a fixed set of constraint templates (max-delta, window-restricted, cross-equipment) rather than free-form rule scripting, revisit only if Pilot needs exceed the templates |

---

*This document is a companion to BRD.MD and should be re-validated against it whenever the BRD changes; Section 17 (Traceability Matrix) is the fastest way to check design coverage after a BRD update.*
