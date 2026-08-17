# Business Requirements Document (BRD)

## CellMind – AI-Powered Solar Cell Manufacturing Intelligence

**Document Version:** 1.3
**Document Type:** Business Requirements Document
**Solution Type:** AI / Multi-Agent / Manufacturing Quality Intelligence
**Target Industry:** Solar Cell Manufacturing
**Primary IP:** Synapt Agent Hub
**Supporting IP:** Synapt Data Transformation, Synapt Context Substrate

**Change Log:**

* v1.0 — Initial hackathon BRD.
* v1.1 — Added RTSP/camera ingestion, real-time model retraining, autonomous production decision support, complete defect taxonomy, and RBAC as in-scope capabilities (FR-18–FR-22); repaired a structural defect where this content had been nested inside an unclosed code block and contradicted the Out-of-Scope list.
* v1.2 — Closed governance gaps identified in architecture review: demonstration-tier clarification for the hackathon demo, segregation of duties between requester and approver (BR-10), a fail-open production rule (BR-11), an explicit distinction between EL-specific capture and generic RTSP cameras, RTSP transport security, a retraining labeling workflow, a taxonomy/model compatibility dependency, defect-rate normalization (vs. raw share-of-defects), multi-tenant data-isolation notes, a split of the Administrator role for separation of duties, and updates to the Executive Summary, Vision, Elevator Pitch and Positioning to reflect all in-scope capabilities.
* v1.3 — Added "Live Positioning Page" note (Section 45): the Elevator Pitch/Positioning is now realized as a public, animated landing page (LANDING_PAGE.html), specified in DDD.MD §16.1 as a data-independent static surface.

---

# 1. Executive Summary

Solar-cell manufacturing involves multiple process stages such as wafer preparation, diffusion, passivation, metallization and firing. Small variations in manufacturing parameters can result in defects, reduced efficiency and production yield loss.

Traditional quality-control systems primarily identify defective cells during or after inspection. Engineers then manually investigate process parameters, equipment history, previous incidents and inspection results to determine the likely cause.

This creates several challenges:

* Delayed root-cause analysis
* Increased scrap and rework
* Repeated manufacturing defects
* Equipment-related quality issues
* Manual investigation effort
* Difficulty prioritizing corrective actions
* Limited ability to predict the impact of process changes

**CellMind** addresses this problem by combining solar-cell inspection images, electrical characteristics, manufacturing-process parameters, equipment information and historical manufacturing context.

The solution uses AI agents to move the quality process from:

> **Detect → Reject**

to:

> **Detect → Trace → Explain → Optimize → Prevent → Learn**

The system identifies defects, correlates them with manufacturing conditions, determines the probable contributing factors, evaluates possible corrective actions and recommends the action expected to provide the best yield improvement relative to cost and downtime.

Beyond the core investigation loop, CellMind is architected to ingest live production video from RTSP and system/third-party cameras, continuously retrain its models under a governed approval workflow, rank corrective actions with configurable decision autonomy, classify defects against a complete taxonomy, and enforce role-based access across the organization — with a human engineer always retaining final authority over production-affecting decisions.

---

# 2. Business Problem

Solar-cell manufacturers need to maximize production yield while maintaining cell quality and minimizing manufacturing cost.

A typical production scenario may look like:

```text
Manufacturing Batch
       ↓
Multiple Process Stages
       ↓
Final Inspection
       ↓
Defective Cells Identified
       ↓
Manual Investigation
       ↓
Process/Eqipment Analysis
       ↓
Root Cause Identification
       ↓
Corrective Action
```

The investigation can require engineers to correlate multiple data sources.

For example:

* EL inspection images
* Electrical measurements
* Process parameters
* Equipment IDs
* Batch information
* Maintenance records
* Historical quality incidents
* Manufacturing SOPs

The absence of an integrated intelligence layer makes the process reactive.

---

# 3. Problem Statement

Solar-cell manufacturers currently have limited ability to automatically connect detected cell defects with the manufacturing process conditions that may have contributed to those defects.

When quality degradation occurs, engineers must manually analyze inspection data, manufacturing parameters, equipment history and previous incidents to identify probable causes and determine corrective actions.

This results in delayed diagnosis, repeated defects, avoidable scrap, reduced yield and increased operational cost.

There is a need for an AI-powered system that can automatically detect quality anomalies, correlate heterogeneous manufacturing data, identify probable contributing factors, explain the evidence, evaluate corrective actions and predict the expected impact on future production yield.

---

# 4. Proposed Solution

CellMind is an AI-powered solar-cell manufacturing intelligence platform.

It combines:

1. Solar-cell EL/inspection images
2. Electrical test data
3. Manufacturing-process parameters
4. Equipment information
5. Historical batch data
6. Maintenance records
7. Manufacturing SOPs and documentation

The solution uses specialized AI agents orchestrated through Synapt Agent Hub.

The agents collaborate to:

* Detect defects
* Analyze process deviations
* Retrieve historical context
* Identify probable contributing factors
* Generate corrective-action options
* Simulate potential outcomes
* Recommend the optimal intervention
* Validate the outcome
* Store the result for future analysis

---

# 5. Vision

## From Reactive Quality Control to Proactive Manufacturing Intelligence

Traditional approach:

> **Manufacture → Inspect → Detect Defect → Investigate → Correct**

CellMind:

> **Monitor → Predict → Detect → Trace → Explain → Simulate → Prevent → Learn**

The long-term vision is to create an intelligent manufacturing quality layer that continuously learns from production outcomes and supports engineers in improving yield.

This vision depends on governed infrastructure, not just smarter models: live camera ingestion, a controlled and auditable model-retraining pipeline, a managed defect taxonomy, configurable decision autonomy with safety constraints, and role-based access — so the intelligence layer itself remains explainable, auditable and safe to operate at production scale.

---

# 6. Objectives

### Primary Objectives

1. Detect defective solar cells using inspection data.
2. Identify abnormal manufacturing-process conditions.
3. Correlate defects with process and equipment information.
4. Provide probable root-cause analysis with confidence levels.
5. Explain the evidence supporting the diagnosis.
6. Generate and compare corrective actions.
7. Predict the expected effect of corrective actions.
8. Recommend the optimal intervention.
9. Validate whether the intervention improved production quality.
10. Maintain historical context for future investigations.
11. Ingest live production video (RTSP) and system/additional camera sources for inspection.
12. Continuously retrain inspection and process models as new labeled data or drift is detected.
13. Rank and recommend production interventions with configurable levels of decision autonomy.
14. Classify and manage defects against a complete, version-controlled defect taxonomy.
15. Enforce role-based access control across all platform functions.

### Business Objectives

* Improve manufacturing yield.
* Reduce scrap and rework.
* Reduce time spent on manual investigations.
* Reduce recurring quality issues.
* Improve equipment utilization.
* Improve engineering decision-making.
* Reduce time-to-root-cause.
* Increase confidence in corrective actions.
* Provide secure, role-appropriate access to manufacturing intelligence across the organization.

---

# 7. Target Users

## 7.1 Quality Engineer

Uses CellMind to:

* Investigate defective cells
* Analyze defect patterns
* Identify probable causes
* Review quality trends
* Validate corrective actions

## 7.2 Process Engineer

Uses CellMind to:

* Analyze process variations
* Identify abnormal process conditions
* Evaluate process adjustments
* Optimize manufacturing parameters

## 7.3 Equipment Engineer

Uses CellMind to:

* Identify equipment-related quality patterns
* Correlate equipment history with defects
* Identify equipment requiring inspection or maintenance

## 7.4 Manufacturing Manager

Uses CellMind to:

* Monitor production yield
* Understand quality risks
* Evaluate business impact
* Prioritize interventions

## 7.5 Plant/Operations Manager

Uses CellMind to:

* View production health
* Monitor quality KPIs
* Understand expected yield impact
* Support operational decisions

## 7.6 Platform Administrator

Uses CellMind to:

* Register and configure cameras and inspection stations
* Manage the defect taxonomy
* Configure autonomy levels and safety constraints for decision support
* Manage roles, permissions and identity-provider integration (RBAC)

The Platform Administrator configures the system but, by design (see BR-10), does not approve retraining promotions — that responsibility sits with the ML Operations Lead, keeping configuration and approval authority separated.

## 7.7 ML Operations Lead

Uses CellMind to:

* Review retraining candidates, drift alerts and holdout-evaluation results
* Approve or reject promotion of a retrained model to production
* Monitor deployed model performance and trigger rollback when needed

The ML Operations Lead approves model changes but is never the same individual who requested or authored the retraining run being approved (see BR-10).

---

# 8. High-Level User Journey

A typical user journey:

```text
User selects production batch
             ↓
System analyzes batch quality
             ↓
Defect/anomaly detected
             ↓
User selects "Investigate"
             ↓
Inspection Agent analyzes cell images
             ↓
Process Agent analyzes process parameters
             ↓
Context Agent retrieves historical information
             ↓
Root Cause Agent correlates evidence
             ↓
Probable contributing factors identified
             ↓
Optimization Agent generates actions
             ↓
Simulation Agent predicts outcomes
             ↓
Recommended action displayed
             ↓
Engineer approves/records action
             ↓
Validation Agent evaluates subsequent batch
             ↓
Outcome stored for future learning
```

---

# 9. Functional Requirements

## FR-01: Batch Management

The system shall allow users to:

* Select a manufacturing batch.
* View batch-level quality metrics.
* View production volume.
* View defect rate.
* View yield.
* View equipment involved in production.
* View process-stage information.

### Example

```text
Batch: B1847

Total Cells: 10,000
Good Cells: 9,160
Defective Cells: 840
Defect Rate: 8.4%
Yield: 91.6%

Risk Level: HIGH
```

---

# 10. FR-02: Solar Cell Inspection

The system shall allow users to upload or select an EL image.

The inspection model shall:

* Process the image.
* Determine whether the cell appears normal or defective.
* Generate a defect probability.
* Generate a confidence score.
* Identify severity where supported.
* Flag low-quality images.

### Example

```text
Cell ID: C392

Defect Probability: 87%
Severity: High
Confidence: 91%

Status:
REQUIRES INVESTIGATION
```

---

# 11. FR-03: Image Quality Validation

Before performing defect classification, the system shall validate image quality.

Potential conditions:

* Blurred image
* Overexposure
* Underexposure
* Incomplete image
* Incorrect image format
* Invalid dimensions
* No recognizable cell structure

If image quality is insufficient:

> "Inspection cannot be reliably performed. Please provide a valid EL image."

---

# 12. FR-04: Process Monitoring

The system shall analyze manufacturing-process parameters.

Example parameters:

* Diffusion temperature
* Diffusion duration
* Firing temperature
* Firing duration
* Metallization parameters
* Pressure
* Gas flow
* Equipment ID
* Process timestamp

The system shall identify parameters outside configured baseline ranges.

---

# 13. FR-05: Equipment Correlation

The system shall correlate quality issues with manufacturing equipment.

The system shall compute each piece of equipment's **defect rate per unit produced**, not only its share of total defects — a high-volume machine will naturally account for a large share of defects without necessarily being higher-risk per unit. Both figures shall be shown together so risk ranking is not biased by production volume.

Example:

```text
Defective Cells: 840

F07:
Units Produced: 2,400
Defective: 615
Defect Rate: 25.6%
Share of Total Defects: 73.2%

F03:
Units Produced: 3,100
Defective: 91
Defect Rate: 2.9%
Share of Total Defects: 10.8%

F05:
Units Produced: 2,900
Defective: 74
Defect Rate: 2.6%
Share of Total Defects: 8.8%
```

F07's defect rate (25.6%) is far above both F03 and F05 and above the plant average, so the system may identify F07 as a high-risk equipment candidate — the conclusion is supported by rate, not just by volume share.

---

# 14. FR-06: Root-Cause Analysis

The system shall combine:

* Image analysis
* Process data
* Equipment data
* Statistical analysis
* Historical incidents
* Manufacturing documentation

to generate probable contributing factors.

Example:

```text
Probable contributing factor:

F07 firing-process variation

Confidence: 91%

Supporting evidence:

1. 73% of affected cells originated from F07.
2. F07 showed abnormal temperature variance.
3. Similar historical batch found.
4. SOP threshold was exceeded.
5. Electrical degradation is consistent with the observed pattern.
```

The system shall avoid representing a probabilistic conclusion as proven causality.

---

# 15. FR-07: Evidence-Based Explanation

Every AI recommendation should provide supporting evidence.

The system shall show:

* Key contributing parameters
* Historical comparisons
* Equipment correlation
* Relevant SOP information
* Confidence level

Example:

```text
Primary factor:
Firing temperature variation

Contribution:
31%

Confidence:
91%

Evidence:
Temperature variance exceeded configured baseline.
Similar historical incident found in Batch B1632.
```

---

# 16. FR-08: Historical Context

The system shall retrieve relevant historical information.

Potential sources:

* Previous batches
* Quality incidents
* Maintenance reports
* SOPs
* Equipment manuals
* Previous corrective actions

Example:

> "A similar issue occurred in Batch B1632. The recorded corrective action was Furnace F07 calibration."

---

# 17. FR-09: Corrective Action Generation

The system shall generate possible corrective actions.

Example:

```text
Action A:
Adjust F07 firing profile

Cost: Low
Expected improvement: 2.4%

Action B:
Perform F07 maintenance

Cost: Medium
Expected improvement: 4.1%

Action C:
Replace component

Cost: High
Expected improvement: 4.8%
```

---

# 18. FR-10: What-If Simulation

Users shall be able to evaluate potential interventions.

Example:

### Scenario

> "What happens if firing temperature variance is reduced?"

System:

```text
Current defect rate:
8.4%

Predicted defect rate:
5.6%

Expected improvement:
2.8 percentage points
```

The simulation shall clearly indicate that the result is a prediction, not a guaranteed outcome.

---

# 19. FR-11: Action Optimization

The system shall evaluate corrective actions using factors such as:

* Expected yield improvement
* Cost
* Equipment downtime
* Risk
* Urgency
* Expected energy/material recovery

The system shall recommend an action based on configurable business priorities.

---

# 20. FR-12: Human-in-the-Loop

CellMind shall not automatically modify production parameters.

For the hackathon MVP:

```text
AI Recommendation
        ↓
Engineer Review
        ↓
Approve / Reject / Modify
        ↓
Action Recorded
```

This is especially important for production safety and enterprise adoption.

---

# 21. FR-13: Validation

After a corrective action, the system shall compare:

* Predicted outcome
* Actual outcome

Example:

```text
Predicted defect reduction:
30%

Actual defect reduction:
24%

Prediction variance:
6 percentage points
```

The outcome shall be stored for future analysis.

---

# 22. FR-14: Confidence and Uncertainty

The system shall provide confidence levels.

Example:

| Confidence  | System Behavior               |
| ----------- | ------------------------------ |
| High        | AI recommendation available   |
| Medium      | Recommend engineering review  |
| Low         | Insufficient evidence         |
| Conflicting | Manual investigation required |

Exact thresholds shall be configurable.

---

# 23. FR-15: Out-of-Distribution Detection

If the inspection model encounters an image pattern significantly different from its training data, the system should flag it.

Example:

> **Unknown defect pattern detected. Manual inspection required.**

The system must not confidently classify an unfamiliar defect.

---

# 24. FR-16: Missing Data Handling

If critical manufacturing data is unavailable:

```text
Firing Temperature: Missing
Equipment History: Available
EL Image: Available
```

The system shall reduce confidence and clearly communicate:

> "Root-cause confidence is reduced because firing telemetry is unavailable."

The system must not invent missing values.

---

# 25. FR-17: Conflicting Evidence

Example:

```text
EL Image:
High defect probability

Process data:
Normal

Historical data:
No similar incident
```

The system shall report:

> **Evidence conflict detected. Additional inspection recommended.**

---

# 26. FR-18: RTSP / System Camera / Additional Camera Models

The system shall support multiple image-acquisition sources for inspection, not only static uploaded images.

The system shall:

* Ingest live RTSP video streams and sample frames for inspection.
* Integrate with system-attached cameras and third-party/additional camera models.
* Allow registration and configuration of multiple camera models (EL/visual) and map them to production lines or inspection stations.
* Distinguish EL-specific inspection hardware (biased cell, dark-chamber capture) from generic visual/RTSP camera sources at registration time. A camera shall only be used for EL inspection if it is registered as EL-capable with its required capture conditions verified; a generic visual/RTSP feed shall not be assumed sufficient for EL inspection.
* Perform camera health checks and basic calibration checks to ensure image consistency across sources.
* Detect and clearly report a disconnected, degraded or unavailable stream, and fall back gracefully (skip frame, queue, alert) rather than fail silently.
* Require authenticated, encrypted transport for camera/RTSP connections (e.g., RTSP over TLS, or a segmented/VPN network); anonymous or default-credential streams shall not be accepted in production.
* Apply a configurable retention policy to sampled frames and any retained video; continuous raw video shall not be stored indefinitely by default.

### Example

```text
Camera: CAM-EL-07
Type: EL / RTSP
Line: L2 / Station: S3
Status: ONLINE
Last Frame: 2026-08-12 10:42:03
Stream Health: OK
```

---

# 27. FR-19: Real-Time Model Retraining

The system shall support near-real-time retraining of inspection and process models based on new production data.

The system shall:

* Collect labeled examples and detected performance/data drift signals from production.
* Define a labeling workflow for retraining candidates: engineer-confirmed defect classifications and validated incident outcomes are the primary label source; any auto-labeled data shall be flagged as lower-trust and weighted or reviewed accordingly before it is used for training.
* Run retraining through a controlled pipeline: data validation → versioning → holdout evaluation → staged rollout.
* Monitor deployed model performance for drift and raise an alert when retraining is recommended.
* Enforce guardrails before promoting a retrained model: minimum labeled-data volume, holdout performance thresholds, and mandatory human approval.
* Require that the approver of a retrained model's promotion is not the same user who requested or triggered that retraining run (see BR-10).
* Support rollback to a prior model version if a staged rollout underperforms.
* Isolate retraining data and resulting models per tenant/site where the platform serves multiple manufacturing customers, unless cross-tenant sharing is explicitly authorized.

### Example

```text
Drift Alert: Inspection model accuracy dropped 4.2 points over 3 days

Retraining Candidate: Model v2.4 → v2.5
Holdout Evaluation: PASS (F1 0.93 vs baseline 0.91)

Status: PENDING APPROVAL
```

---

# 28. FR-20: Autonomous Production Decision Support

The system shall provide decision-support automation that ranks recommended interventions by expected impact, cost and risk, with configurable autonomy.

The system shall support configurable autonomy levels:

* **Level A — Recommend-only:** the system presents ranked options; no action is pre-selected.
* **Level B — Auto-suggest with human approval:** the system pre-selects a top recommendation; an authorized engineer must approve before it is recorded as an action.
* **Level C — Closed-loop automation (future):** not enabled in the current release; see Section 43 (Scope).

Every automated ranking or recommendation shall be logged with its rationale, supporting evidence, and any operator override. Safety constraints shall prevent the system from recommending an action known to risk equipment damage or product-quality degradation.

Level C shall not be enabled for any deployment until: (a) a documented safety case and failure-mode analysis exists, (b) independent validation of closed-loop behavior has been performed, and (c) explicit customer/regulatory sign-off is recorded. No release currently targets Level C.

If the decision-support system or Agent Hub is unavailable, production shall continue under standard manual procedure rather than being blocked by the AI system's unavailability, unless a customer explicitly configures fail-closed behavior for a given line (see BR-11).

### Example

```text
Autonomy Level: B (Auto-suggest, approval required)

Ranked Recommendations:
1. Adjust F07 firing profile — Impact: High, Cost: Low, Risk: Low
2. Perform F07 maintenance   — Impact: High, Cost: Medium, Risk: Low
3. Replace component         — Impact: Medium, Cost: High, Risk: Medium

Status: AWAITING ENGINEER APPROVAL
```

---

# 29. FR-21: Defect Taxonomy Management

The system shall maintain a complete, version-controlled defect taxonomy used by inspection models and reporting.

The system shall:

* Define defect categories, subtypes and severity levels, benchmarked against established PV-industry EL-defect classification conventions where available rather than defined independently from first principles.
* Map each taxonomy entry to probable root-cause families and suggested corrective actions to accelerate triage.
* Version the taxonomy with a change-log, and provide migration guidance for reclassifying historical data when the taxonomy changes.
* Trigger a compatibility review of dependent inspection models whenever a taxonomy version adds, removes or redefines a category; if a model's output classes no longer map cleanly to the new version, retraining or a mapping layer shall be evaluated (see FR-19).

### Example

```text
Defect Category: Micro-crack
Subtype: Edge-induced micro-crack
Severity: Medium

Linked Root-Cause Families: Handling stress, Firing thermal shock
Suggested Actions: Inspect handling equipment, review firing ramp rate

Taxonomy Version: v1.3
```

---

# 30. FR-22: Role-Based Access Control (RBAC)

The system shall enforce role-based access control across all platform functionality.

The system shall:

* Provide roles including Viewer, Quality Engineer, Process Engineer, Equipment Engineer, Plant/Operations Manager, Platform Administrator and ML Operations Lead.
* Restrict sensitive actions — requesting a retrain, approving a corrective action or autonomous recommendation, approving a model promotion, managing cameras, and configuring the taxonomy — to authorized roles.
* Enforce that the requester/author of a retraining run or recommendation and its approver are always distinct users, regardless of role (see BR-10).
* Log all sensitive operations (model retraining, decision-support approvals, RBAC changes) for audit purposes.
* Support integration with enterprise identity providers (SSO / LDAP / SAML) for centralized identity management.
* Scope roles and data access per tenant/organization, in addition to per-role permissions, where the platform serves multiple manufacturing customers.

### Example

```text
User: J. Alvarez
Role: Process Engineer

Permitted:
View process data, Request retrain, Approve process actions

Denied:
Manage RBAC, Approve autonomous closed-loop actions
```

---

# 31. Non-Functional Requirements

## NFR-01: Performance

Prototype target:

* Image analysis: <5 seconds
* Agent investigation: <30 seconds
* Dashboard response: <3 seconds for normal queries
* Camera/RTSP ingestion: sustained frame sampling from at least one stream per registered station, with per-frame analysis latency consistent with the image-analysis target above
* Retraining cycle: end-to-end (data collection → validation → holdout evaluation → staged-rollout decision) target <24 hours for a scheduled cycle, configurable per deployment

These are hackathon/prototype targets and should be validated against the actual prototype environment.

## NFR-02: Explainability

AI recommendations should provide evidence and reasoning factors.

## NFR-03: Reliability

System should gracefully handle:

* Missing data
* Invalid images
* Agent failures
* Model failures
* API timeouts
* Camera/RTSP stream interruptions

## NFR-04: Security

The platform shall enforce authentication and role-based authorization (see FR-22) for all users and sensitive operations.

Production implementation should include:

* Authentication
* Authorization / RBAC
* Encryption
* Audit logging
* Role-based access
* SSO / LDAP / SAML integration for enterprise identity
* Authenticated, encrypted transport for camera/RTSP ingestion (see FR-18)
* Per-tenant data isolation where the platform serves multiple manufacturing customers

## NFR-05: Auditability

The system should maintain:

* Input data
* Model result
* Agent recommendation
* User decision
* Final outcome
* Model version history and retraining approvals
* RBAC changes and access decisions

---

# 32. Synapt IP Mapping

## Primary IP: Synapt Agent Hub

Agent Hub orchestrates the multi-agent workflow.

### Agents

```text
Inspection Agent
       ↓
Process Analysis Agent
       ↓
Context Agent
       ↓
Root Cause Agent
       ↓
Optimization Agent
       ↓
Simulation Agent
       ↓
Validation Agent
```

---

## Supporting IP: Synapt Data Transformation

Used for:

* EL image processing
* Manufacturing-data normalization
* Feature extraction
* Data quality checks
* Process analytics
* ML input preparation

---

## Supporting IP: Synapt Context Substrate

Used as enterprise manufacturing memory.

Stores/retrieves:

* SOPs
* Equipment manuals
* Historical batches
* Quality incidents
* Maintenance records
* Corrective actions

---

# 33. Data Architecture

The MVP can use two categories of data, with a live ingestion path where cameras are available.

## Real/Public Data

EL inspection images and associated labels from publicly available research datasets.

## Simulated Enterprise Data

Because real manufacturing telemetry is typically proprietary, the prototype can use realistic synthetic data for:

* Process parameters
* Equipment information
* Batch history
* Maintenance history
* Quality measurements

## Live Production Data (Camera / RTSP)

Where system or third-party cameras are available, the platform can ingest live EL/visual inspection frames via RTSP for real-time inspection, in addition to static image datasets (see FR-18). Raw video/frames are subject to a configurable retention policy rather than indefinite storage.

Where CellMind is deployed across more than one plant or customer, production data, retraining data and resulting models shall be isolated per tenant unless cross-tenant sharing is explicitly authorized (see FR-19, FR-22).

The production architecture shall support replacing simulated data with real MES/SCADA/QMS data.

---

# 34. MVP Data Model

### Batch

```text
batch_id
production_date
line_id
equipment_ids
cell_count
good_count
defect_count
yield
```

### Cell

```text
cell_id
batch_id
image_path
defect_probability
severity
voc
isc
fill_factor
efficiency
series_resistance
```

### Process

```text
process_id
batch_id
stage
equipment_id
temperature
duration
pressure
gas_flow
timestamp
```

### Equipment

```text
equipment_id
equipment_type
operating_hours
maintenance_date
status
```

### Incident

```text
incident_id
batch_id
equipment_id
defect_type
probable_cause
corrective_action
outcome
```

### Camera

```text
camera_id
camera_type (EL/visual)
model
line_id
station_id
stream_url
status
last_frame_at
```

### ModelVersion

```text
model_version_id
model_name
version
trained_on_date
holdout_metric
status (staged/production/retired)
approved_by
```

### DefectTaxonomyEntry

```text
taxonomy_id
category
subtype
severity
root_cause_family
suggested_action
taxonomy_version
```

### Role

```text
role_id
role_name
permissions
```

---

# 35. In-Scope Capability Details

The following capabilities are explicitly in-scope for the CellMind project (MVP and near-term roadmap), expanding on FR-18 through FR-22.

### 1. RTSP / System Camera / Additional Camera Models

* Support for ingesting live video streams (RTSP) and sampling frames for inspection.
* Integration with system-attached cameras and third-party camera models.
* Camera configuration, health checks, and basic calibration support to ensure image consistency.
* Ability to register multiple camera models (EL/visual) and map them to production lines or inspection stations.

### 2. Real-Time Model Retraining

* Infrastructure to collect labeled examples and drifts detected during production for near-real-time retraining cycles.
* Controlled retraining pipeline with data validation, versioning, testing (holdout evaluation), and staged rollout.
* Metrics and monitoring for model performance drift and automated alerts when retraining is recommended.
* Guardrails to prevent unsafe or low-quality retraining (human approval gates, minimum data size, and performance thresholds).

### 3. Autonomous Production Decisions

* Decision-support automation that ranks recommended interventions based on impact, cost and risk.
* Configurable autonomy levels: (a) Recommend-only, (b) Auto-suggest with human approval, (c) (future) Closed-loop automation.
* Recording and audit of any automated decision, including rationale, evidence, and operator overrides.
* Safety constraints to prevent automated actions that could harm equipment or product quality.

### 4. Complete Defect Taxonomy

* Deliver a comprehensive defect taxonomy (categories, subtypes, severity levels) used by the inspection models and reporting.
* Map taxonomy entries to root-cause families and suggested corrective actions to accelerate triage.
* Version-controlled taxonomy with change-log and migration guidance for historical data.

### 5. Role-Based Access Control (RBAC)

* Fine-grained RBAC for the platform with roles such as: Viewer, Quality Engineer, Process Engineer, Equipment Engineer, Plant/Operations Manager, Platform Administrator, ML Operations Lead.
* Permissions for actions: view data, request retrain, approve actions, approve autonomous-decision recommendations, approve model promotion, manage cameras, configure taxonomy.
* Requester/author and approver of the same retraining run or recommendation are always distinct users (see BR-10).
* Audit logging for sensitive operations (model retrain, autonomous-decision approval, RBAC changes).
* Integration points for enterprise SSO / LDAP / SAML for centralized identity management, with per-tenant data scoping for multi-customer deployments.

---

# 36. Business Rules

### BR-01

The system shall not automatically reject a cell solely based on AI classification.

### BR-02

Low-confidence predictions shall be routed for human review.

### BR-03

Missing critical data shall reduce confidence rather than be replaced with fabricated information.

### BR-04

AI-generated root causes shall be presented as probable contributing factors unless causal evidence is available.

### BR-05

Corrective actions shall be recommendations requiring authorized human approval.

### BR-06

Historical information shall be presented with its source/context.

### BR-07

Production parameters shall not be automatically modified by the hackathon prototype.

### BR-08

Autonomous production decision support shall operate only at Recommend-only or Auto-suggest-with-approval autonomy levels; closed-loop execution is not enabled in the current release.

### BR-09

Access to platform data and actions shall be governed by RBAC; a user shall only view or perform actions permitted by their assigned role.

### BR-10

The user who requests or triggers a model retraining run, or who authors an autonomous recommendation, shall not also be the approver of that same action; a distinct authorized approver is required.

### BR-11

If AI inspection, decision-support, or Agent Hub services are unavailable, production shall continue under standard manual inspection procedure rather than being blocked by system unavailability, unless a customer explicitly configures fail-closed behavior for a given line.

---

# 37. Edge Cases

The system shall support the following scenarios:

1. Normal cell incorrectly flagged.
2. Defective cell incorrectly classified as normal.
3. Unknown defect pattern.
4. Poor-quality EL image.
5. Missing process parameter.
6. Missing equipment history.
7. Conflicting evidence.
8. Multiple probable causes.
9. No historical match.
10. Low model confidence.
11. High-cost corrective action.
12. Multiple equipment candidates.
13. Simulation predicts negative impact.
14. Actual result differs significantly from prediction.
15. Agent/service failure.
16. Duplicate inspection record.
17. Invalid batch ID.
18. Incomplete batch.
19. Sudden process anomaly without immediate quality degradation.
20. Quality degradation without an obvious process anomaly.
21. Camera/RTSP stream disconnected or degraded mid-inspection.
22. Retraining triggered on insufficient or low-quality labeled data.
23. Retrained model underperforms the current production model on holdout evaluation.
24. Unauthorized or misconfigured access attempt (RBAC denial).
25. Autonomous recommendation conflicts with a configured safety constraint.

---

# 38. Key Performance Indicators

The success of CellMind should be measured using:

## Technical KPIs

* Defect classification precision
* Defect classification recall
* F1 score
* False-negative rate
* Root-cause recommendation confidence
* Prediction accuracy
* Image processing latency
* Agent workflow completion rate
* Camera/stream uptime and availability
* Model retraining cycle time
* Retrained model holdout performance vs. baseline
* RBAC policy violations detected/blocked

## Business KPIs

### 1. Yield Improvement

```text
Post-intervention yield - Pre-intervention yield
```

### 2. Time-to-Root-Cause

Measure the time from defect detection to probable cause identification.

### 3. Scrap Reduction

Measure reduction in defective production.

### 4. Engineering Investigation Time

Compare manual investigation effort with AI-assisted investigation.

### 5. Recurring Defect Reduction

Measure whether previously observed issues occur less frequently.

---

# 39. Success Criteria for Hackathon MVP

The MVP will be considered successful if it can demonstrate the complete workflow:

```text
EL Image
   ↓
Defect Detection
   ↓
Batch Identification
   ↓
Process Analysis
   ↓
Historical Context Retrieval
   ↓
Probable Root Cause
   ↓
Corrective Action Options
   ↓
What-If Simulation
   ↓
Recommended Action
   ↓
Predicted Yield Improvement
```

A successful demo should demonstrate at least one defect scenario end-to-end.

### Demonstration Checklist for Extended Capabilities

Section 43 defines which delivery tier (hackathon demo / pilot / enterprise) applies to each extended capability. For anything marked "Demonstrated" in that tier table, the hackathon demo must visibly show it — not only describe it in this document:

* [ ] A frame is shown arriving from a registered camera/RTSP source (live or recorded), not only a manually uploaded image (FR-18).
* [ ] A ranked recommendation is shown at the configured autonomy level, gated behind an explicit approval action (FR-20).
* [ ] The defect on screen is linked to a taxonomy entry (category/subtype/severity) from the demo taxonomy subset (FR-21).
* [ ] At least two different roles are shown with visibly different permitted actions (FR-22).
* [ ] The retraining pipeline stages are shown against a pre-staged run (data validation → holdout evaluation → approval), rather than a live full training job (FR-19).

---

# 40. Recommended Hackathon Demo Scenario

## Scenario: Furnace F07 Quality Degradation

### Initial state

```text
Batch: B1847

Production:
10,000 cells

Defect Rate:
8.4%

Yield:
91.6%
```

### Detection

EL inspection identifies an abnormal pattern, captured from a registered EL-capable camera.

```text
Source: CAM-EL-07 (RTSP)

Defect Probability:
87%

Confidence:
91%
```

### Investigation

Agent Hub activates:

```text
Inspection Agent       ✓
Process Agent          ✓
Context Agent          ✓
Root Cause Agent       ✓
```

### Finding

```text
Probable contributing factor:

F07 firing-process variation

Confidence:
91%
```

### Evidence

```text
F07 defect rate: 25.6% (share of defects: 73%)
→ Well above plant average and above F03/F05

F07 temperature variance
→ Above baseline

Historical match
→ Batch B1632
```

### Corrective actions

```text
1. Adjust process
2. Perform maintenance
3. Replace component
```

### Decision Support & Approval

```text
Autonomy Level: B (Auto-suggest, approval required)

Ranked Recommendation: Adjust process + inspect F07
Authored by: Root Cause Agent (system)
Approval required from: Process Engineer role

Approver: J. Alvarez (Process Engineer)
Status: APPROVED
```

### Simulation

```text
Current defect rate:
8.4%

Recommended action:
Adjust process + inspect F07

Predicted defect rate:
5.6%

Predicted improvement:
2.8 percentage points
```

### Validation

```text
Predicted:
5.6%

Actual:
5.9%

Outcome:
Recommendation direction validated
```

### Continuous Improvement

```text
Incident logged: F07 firing-process variation
Taxonomy entry attached: Micro-crack / Edge-induced (Severity: Medium)

Retraining candidate flagged: include validated B1847 outcome as labeled example
Requested by: Quality Engineer (incident review)
Approver: ML Operations Lead — distinct from requester (BR-10)
Status: QUEUED FOR NEXT RETRAINING CYCLE
```

---

# 41. MVP Technology Architecture

```text
        Camera / RTSP Sources
                       │
                       ▼
                React Dashboard
                       │
                       ▼
                  FastAPI API
                       │
                       ▼
               Synapt Agent Hub
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
       CV             ML           Context
      Model         Models        Substrate
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                 Data Layer
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
      Images        Process Data    Historical
                                     Data
```

RTSP/camera ingestion feeds the CV Model path; retraining runs as a controlled pipeline alongside the CV/ML models (see FR-18, FR-19).

---

# 42. Prototype Technology Stack

| Layer                | Suggested Technology                 |
| --------------------- | ------------------------------------- |
| Frontend             | React                                 |
| Backend              | Python / FastAPI                      |
| Computer Vision      | PyTorch / OpenCV                      |
| Image Model          | EfficientNet-B0 / ResNet18            |
| Process ML           | XGBoost / Random Forest               |
| Explainability       | SHAP                                  |
| Data Processing      | Pandas                                |
| Database             | PostgreSQL                            |
| Knowledge            | Synapt Context Substrate              |
| Agent Orchestration  | Synapt Agent Hub                      |
| Data Transformation  | Synapt Data Transformation            |
| Visualization        | Plotly                                |
| Video Ingestion      | RTSP via OpenCV / GStreamer / FFmpeg  |
| MLOps / Retraining   | MLflow (or equivalent) + scheduled retrain jobs |
| Identity / RBAC      | OAuth2 / JWT, Keycloak (SSO/LDAP/SAML) |

---

# 43. Scope

## In Scope

* EL image analysis
* Defect detection
* Batch analysis
* Process anomaly detection
* Equipment correlation
* Probable root-cause analysis
* Historical context retrieval
* Corrective-action recommendation
* What-if simulation
* Yield prediction
* Human approval
* Outcome validation
* RTSP / system camera / additional camera model ingestion (FR-18)
* Real-time model retraining pipeline (FR-19)
* Autonomous production decision support with configurable autonomy levels (FR-20)
* Complete, version-controlled defect taxonomy (FR-21)
* Role-based access control (FR-22)

### Delivery Tier for Extended Capabilities

"In scope" does not mean identically built at every stage. Each extended capability is delivered at a different fidelity depending on phase:

| Capability                  | Hackathon Demo (Phase 1)                             | Pilot (Phase 2)                        | Enterprise (Phase 3+)                                              |
| ---------------------------- | ------------------------------------------------------ | ----------------------------------------- | --------------------------------------------------------------------- |
| RTSP / camera ingestion     | Demonstrated: one live or recorded stream             | Real ingestion at pilot-line scale       | Multi-line, multi-camera at plant scale                              |
| Real-time model retraining  | Simulated: pipeline stages shown on a pre-staged run  | Real pipeline, scheduled staged rollout  | Continuous, monitored, multi-model                                    |
| Autonomous decision support | Demonstrated: Level A/B ranking with approval gate    | Level B at pilot scale                   | Level B at enterprise scale; Level C gated by FR-20 criteria only    |
| Defect taxonomy             | Demonstrated: representative subset (5–10 categories) | Full taxonomy for pilot defect types     | Full, versioned taxonomy across plants                                |
| RBAC                        | Demonstrated: 2+ roles, local accounts                | Role set above, basic SSO                | Full role set, enterprise SSO/LDAP/SAML, multi-tenant scoping        |

## Out of Scope for MVP

* Direct factory equipment control
* Automatic modification of production parameters
* Real-time PLC control
* Full semiconductor physics simulation
* Production-grade MES integration
* Closed-loop autonomous execution (Level C autonomy) — recommend-only and approval-gated autonomy (Levels A/B) remain in scope

---

# 44. Assumptions

1. EL inspection images are available.
2. Batch information can be associated with inspection results.
3. Manufacturing process data is available or can be simulated.
4. Equipment identifiers are available.
5. Historical information can be represented in the prototype.
6. Real manufacturing data will be proprietary; synthetic data can be used for the hackathon.
7. Human engineers remain responsible for production decisions.
8. At least one system, RTSP, or additional camera source is available for live-ingestion testing, or a recorded stream can substitute for the demo.
9. A minimum viable labeled dataset is available to exercise the retraining pipeline in staging.
10. Roles and initial permission mappings for RBAC can be defined with the customer or approximated for the prototype.
11. Where an established PV-industry EL-defect classification convention exists, it will be used as the starting point for the taxonomy (FR-21) rather than defining categories from first principles.

---

# 45. Risks and Mitigations

| Risk                                        | Impact | Mitigation                                                       |
| -------------------------------------------- | ------ | ------------------------------------------------------------------ |
| Limited real manufacturing data              | High   | Use public EL data + realistic synthetic process data             |
| Model false negatives                        | High   | Optimize recall and require human review                          |
| Root cause incorrectly inferred              | High   | Present probable causes with confidence/evidence                  |
| Poor image quality                           | Medium | Add image-quality validation                                      |
| Unknown defects                              | High   | Out-of-distribution detection                                     |
| Missing telemetry                            | Medium | Reduce confidence                                                 |
| Agent hallucination                          | High   | Ground recommendations in structured evidence/context             |
| Overly complex MVP                           | High   | Limit to one defect scenario                                      |
| Lack of measurable business impact           | Medium | Add yield/cost simulation                                         |
| Model overfitting                            | Medium | Separate training/test data by module/batch where possible        |
| RTSP/camera stream instability               | Medium | Health checks, automatic reconnect, fallback to last-known-good frame |
| Retraining on poor-quality or drifted data    | High   | Data validation, holdout evaluation, staged rollout, approval gate |
| Autonomous decision-support overreach        | High   | Default to Recommend-only autonomy, safety constraints, audit logging |
| RBAC misconfiguration exposing sensitive data | Medium | Least-privilege defaults, periodic role review, audit logging     |
| AI/decision-support system unavailable mid-production | Medium | Fail-open business rule (BR-11): production continues under manual procedure |
| Self-approval undermines audit trail on retraining/recommendations | Medium | Segregation-of-duties rule (BR-10), enforced via RBAC |
| EL acquisition assumed equivalent to generic RTSP capture | High   | FR-18 requires explicit EL-capable device registration with capture-condition validation |
| Taxonomy changes silently break deployed model output mapping | Medium | FR-21 compatibility review triggers a retraining/mapping evaluation |

---

# 46. Future Roadmap

## Phase 1 — Hackathon MVP

```text
EL Image
 ↓
Defect Detection
 ↓
Synthetic Process Data
 ↓
Root Cause
 ↓
What-if
 ↓
Recommendation
```

Includes baseline RBAC (Viewer/Engineer roles) and camera/RTSP ingestion where a source is available, alongside static image upload.

## Phase 2 — Pilot

Integrate:

* MES
* QMS
* Equipment telemetry
* Maintenance system
* Real production data
* Live RTSP camera ingestion at pilot scale
* Retraining pipeline with staged rollout
* Expanded RBAC with SSO

## Phase 3 — Enterprise

Add:

* Multi-line monitoring
* Real-time anomaly detection
* Advanced process optimization
* Predictive equipment quality analysis
* Automated work-order creation
* Cross-plant benchmarking
* Full defect-taxonomy governance across plants
* Autonomous decision ranking (Level B) across all lines
* Enterprise RBAC/SSO across all plants

## Phase 4 — Autonomous Quality Intelligence

Long-term vision:

```text
Detect
 ↓
Diagnose
 ↓
Predict
 ↓
Optimize
 ↓
Human Approval
 ↓
Execute
 ↓
Validate
 ↓
Learn
```

Potential Level C closed-loop automation, subject to the safety case, independent validation and sign-off criteria defined in FR-20 — not a default outcome of this roadmap.

---

# 47. Expected Business Value

CellMind can potentially create value across four areas:

### Quality

Earlier identification of emerging defects.

### Yield

Reduction in avoidable production losses.

### Engineering Productivity

Reduced manual investigation effort.

### Operational Excellence

Better prioritization of equipment and process interventions.

The actual financial benefit should be calculated using customer-specific production volume, scrap cost, yield and intervention cost rather than using assumed numbers.

---

# 48. Competitive Differentiation

CellMind is not positioned as another defect-classification system.

| Conventional Approach    | CellMind                   |
| ------------------------ | --------------------------- |
| Detect defect            | Detect + investigate        |
| Image classification     | Multimodal analysis         |
| Static alert             | Agent-driven investigation  |
| Manual root cause        | AI-assisted probable cause  |
| Historical data isolated | Context-aware reasoning     |
| Fixed threshold          | Evidence + prediction        |
| Corrective action manual | Action comparison            |
| No what-if               | Intervention simulation      |
| Reactive                 | Preventive                   |
| No learning loop         | Outcome validation           |

---

# 49. Innovation Statement

The core innovation is the combination of **multimodal quality intelligence and agentic manufacturing reasoning**.

Instead of treating a solar-cell defect as an isolated image-classification problem, CellMind connects:

> **What is wrong?**

with:

> **Where did it originate?**

then:

> **Why might it have happened?**

and finally:

> **What should we do differently in the next batch?**

This creates a closed-loop manufacturing intelligence system:

> **Detect → Trace → Explain → Optimize → Prevent → Learn**

---

# 50. Final Elevator Pitch

> **CellMind is an AI-powered solar-cell manufacturing intelligence platform that goes beyond detecting defective cells. It combines EL inspection images, electrical characteristics, manufacturing-process parameters, equipment history and enterprise context to identify probable contributing factors, explain the evidence, simulate corrective actions and recommend the intervention that maximizes expected yield improvement while minimizing cost and downtime. CellMind ingests live production imagery from cameras and RTSP streams, continuously and safely retrains its models under human governance, and enforces role-based access across the organization. Powered by Synapt Agent Hub, CellMind transforms reactive quality inspection into proactive, explainable, secure and continuously improving manufacturing intelligence.**

---

# 51. Final Hackathon Positioning

## Problem

**Manufacturing defects are detected late and root-cause analysis is largely manual.**

## Solution

**AI agents connect cell-level defects with manufacturing-process evidence and recommend preventive actions.**

## Innovation

**Moving from defect detection to defect prevention through agentic root-cause analysis and what-if optimization.**

## IP

**Synapt Agent Hub + Synapt Data Transformation + Synapt Context Substrate**

## Primary KPI

**Manufacturing Yield Improvement**

## Secondary KPIs

**Time-to-Root-Cause, Scrap Reduction, Engineering Effort Reduction and Recurring Defect Reduction.**

## Governance

**Every autonomous recommendation, retraining cycle and access decision is approval-gated, segregated between requester and approver, and fully audited.**

## Tagline

### **"Don't just detect the defect. Find why it happened—and prevent the next batch from failing."**

## Live Positioning Page

This pitch is now realized as a public, animated landing page (`LANDING_PAGE.html`) aimed at prospective manufacturers and hackathon judges — it does not depend on tenant data or the authenticated product (DDD.MD §16.1.3), so it can be shared independently of a live deployment. Its structure follows the same Problem → Solution → Proof → Capabilities → CTA narrative as this section and Section 45.

---

# 52. Next Steps

* Update architecture and data flow diagrams to include RTSP/camera ingestion and retraining pipelines.
* Define the RBAC matrix and map UI screens/actions to roles.
* Draft the initial defect taxonomy and mapping to corrective actions.
* Specify the retraining data schema and approval workflow for staged rollouts.
* Define autonomy-level configuration and safety-constraint policy for production decision support.
