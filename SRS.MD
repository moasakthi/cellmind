# Software Requirements Specification (SRS)

## CellMind – AI-Powered Solar Cell Manufacturing Intelligence

**Document Version:** 1.1
**Document Type:** Software Requirements Specification (IEEE 830–influenced)
**References:** BRD.MD v1.2 (business requirements), DDD.MD v1.1 (technical design)
**Companion Deliverables:** STYLE_GUIDE.html (design system), WIREFRAMES.html (screen mockups), LANDING_PAGE.html (public pitch page), openapi.yaml + API_EXPLORER.html (API contract)

**Change Log:** v1.0 initial issue. v1.1 adds REQ-N06.3–N06.5 (motion/reduced-motion and no-JS-fallback requirements) covering the new Motion & Interaction Design in DDD.MD §16.1 and the LANDING_PAGE.html artifact.

---

# 1. Introduction

## 1.1 Purpose

This SRS restates every BRD functional/non-functional requirement as a discrete, uniquely-numbered, independently verifiable requirement (`REQ-##.#`), and adds the use-case and interface detail needed to write test cases directly from this document. Where the BRD states *what the business needs* and the DDD states *how it will be built*, this SRS states *what must be true for the system to be considered correct* — the layer a QA engineer or acceptance reviewer works from.

## 1.2 Document Conventions

* **REQ-ID format:** `REQ-<FR#>.<seq>`, e.g. `REQ-05.2` is the second verifiable requirement under FR-05 (Equipment Correlation). This makes the BRD FR number recoverable from the ID alone.
* **Priority:** `Must` (blocking for any release claiming the capability) / `Should` (expected, may slip one iteration) / `Could` (nice-to-have at current tier).
* **Verification method:** `Test` (automated/manual test case) / `Inspection` (code/config review) / `Demo` (observed in a live/staged run).
* Acceptance criteria are written Given/When/Then so they map directly to test-case steps.

## 1.3 Intended Audience

QA/test engineers writing test cases, developers implementing against DDD.MD, and business stakeholders verifying BRD.MD coverage before acceptance.

## 1.4 Scope

Covers all in-scope capabilities from BRD.MD §43, including the five extended capabilities (RTSP/camera ingestion, real-time retraining, autonomous decision support, defect taxonomy, RBAC). Follows the same Hackathon Demo / Pilot / Enterprise tiering as BRD §43 — each requirement below states the tier at which it must hold if that differs from Enterprise.

## 1.5 References

* BRD.MD v1.2 — Business Requirements Document
* DDD.MD v1.0 — Detailed Design Document
* STYLE_GUIDE.html, WIREFRAMES.html — UI reference
* openapi.yaml — API contract

## 1.6 Definitions / Acronyms

See DDD.MD §1.4. Additional term used here: **REQ** — a single, independently verifiable requirement statement derived from one BRD functional/non-functional requirement.

---

# 2. Overall Description

## 2.1 Product Perspective

CellMind is a layer on top of (eventually) a plant's MES/QMS/SCADA and camera infrastructure — it does not replace them and, per BR-07/REQ-12.1, never writes back to production-control systems. See DDD.MD §3.1 for the full component diagram; the perspective relevant to this SRS is:

```text
[ Cameras / RTSP ] ─┐
[ MES/QMS/SCADA ]───┼──► [ CellMind ] ──► [ Engineer decisions, recorded ] ──► (manual) production change
[ SSO/LDAP/SAML ]────┘
```

## 2.2 Product Functions (Summary)

Investigate defects end-to-end (detect → correlate → explain → recommend → simulate → approve → validate); ingest live camera/RTSP imagery; retrain models under governance; rank interventions with configurable autonomy; maintain a versioned defect taxonomy; enforce RBAC. One-line summary of each is in BRD.MD §6.

## 2.3 User Classes and Characteristics

| Class | Characteristics | Reference |
|---|---|---|
| Viewer | Read-only, any dashboard consumer | BRD §7 |
| Quality Engineer | Investigates defects, requests retrains, approves quality actions | BRD §7.1 |
| Process Engineer | Analyzes process data, approves process actions | BRD §7.2 |
| Equipment Engineer | Correlates equipment history, approves equipment actions | BRD §7.3 |
| Manufacturing Manager / Plant-Operations Manager | Business-impact and KPI consumers, no approval actions | BRD §7.4–7.5 |
| Platform Administrator | Configures cameras, taxonomy, autonomy, RBAC — cannot approve retraining | BRD §7.6 / DDD §10.2 |
| ML Operations Lead | Approves/rejects/rolls back retraining — cannot touch RBAC/camera/taxonomy config | BRD §7.7 / DDD §10.2 |

## 2.4 Operating Environment

Web dashboard (React) over HTTPS; backend services per DDD §3; deployed at one of three tiers (Hackathon Demo / Pilot / Enterprise, BRD §43) with capability fidelity varying by tier as defined in DDD §3.3.

## 2.5 Design and Implementation Constraints

* No code path may write to `Process`/`Equipment` tables (REQ-12.1, BR-07).
* No code path may execute Level C (closed-loop) autonomy in the current release; the schema may represent it, but it must be unreachable at runtime until the FR-20 gating criteria are formally signed off (REQ-20.5, BR-08).
* The `Approval` table's `requested_by <> approver` constraint (DDD §11.2) is a hard schema constraint, not only an application check (REQ-22.4/REQ-19.5, BR-10).

## 2.6 Assumptions and Dependencies

Inherits BRD.MD §44 (Assumptions 1–11) unchanged.

---

# 3. External Interface Requirements

## 3.1 User Interfaces

All screens are specified in WIREFRAMES.html (7 screens: Dashboard, Investigation, Recommendation & Approval, Camera Admin, Retraining Console, Taxonomy Admin, RBAC & Audit); visual tokens/components in STYLE_GUIDE.html. Every AI-facing state (confidence, severity, camera health, autonomy level) must render through the chip component defined there — REQ-14.4 makes this a testable requirement, not only a style preference.

## 3.2 Hardware Interfaces

RTSP-capable cameras (system-attached or third-party), registered per FR-18/REQ-18.*. EL-capable devices must expose or have recorded confirmation of bias-voltage and dark-chamber capture conditions at registration (REQ-18.1).

## 3.3 Software Interfaces

* Identity: SSO/LDAP/SAML (Pilot+ tier), local accounts (Hackathon Demo tier) — REQ-22.6.
* Future: MES/QMS/SCADA read integration replacing simulated process/equipment data (BRD §33), out of scope for this SRS's verifiable requirements until a Pilot integration is scheduled.
* Model Registry (MLflow or equivalent) for versioned model artifacts — REQ-19.3.

## 3.4 Communication Interfaces

REST over HTTPS (see openapi.yaml for the full contract); RTSP/RTSPS for camera ingestion (REQ-18.5); WebSocket or polling for live investigation-status updates on the dashboard.

---

# 4. System Features

Each subsection below corresponds 1:1 to a BRD functional requirement. "Tier" is omitted where a requirement holds at all tiers.

## 4.1 Batch Management (FR-01)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-01.1 | User can select a batch and view cell count, good/defect count, yield, defect rate | Must | **Given** a batch with 10,000 cells and 840 defects, **when** the user opens it, **then** yield displays as 91.6% and defect rate as 8.4%, both computed, not hand-entered. |
| REQ-01.2 | Batch-level metrics are pre-aggregated on write, not recomputed per read | Must | **Given** the Dashboard is opened, **when** it loads a batch list of typical size, **then** response time is <3s (NFR-01). |
| REQ-01.3 | Batch view shows a computed Risk Level (HIGH/MEDIUM/LOW) | Should | **Given** a batch's defect rate exceeds the configured HIGH threshold, **when** viewed on the Dashboard, **then** it renders the HIGH-risk chip (STYLE_GUIDE.html status chip). |

## 4.2 Solar Cell Inspection (FR-02)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-02.1 | System returns defect probability, severity and confidence for a submitted EL image | Must | **Given** a valid EL image of cell C392, **when** submitted for inspection, **then** the response includes all three fields within 5s (NFR-01). |
| REQ-02.2 | Inspection result never omits a confidence value | Must | **Given** any successful inspection, **when** the result is returned, **then** `confidence` is present and in [0,1]. |

## 4.3 Image Quality Validation (FR-03)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-03.1 | Insufficient-quality images are rejected before classification | Must | **Given** a blurred/overexposed/incomplete image, **when** submitted, **then** the system returns the fixed rejection message and does **not** return a defect classification. |
| REQ-03.2 | Quality check runs before, not instead of, the cost of full inference | Should | **Given** a rejected image, **when** measured, **then** CV-model inference is not invoked (DDD §5 FR-03 design). |

## 4.4 Process Monitoring (FR-04)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-04.1 | Process parameters outside configured baseline are flagged | Must | **Given** firing temperature exceeds its configured baseline range, **when** the batch is analyzed, **then** the parameter appears in `anomalies[]` with baseline and deviation values. |
| REQ-04.2 | Baseline ranges are configurable without a code release | Should | **Given** a Platform Administrator updates a `ProcessBaseline` threshold, **when** saved, **then** subsequent analyses use the new threshold immediately. |

## 4.5 Equipment Correlation (FR-05)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-05.1 | Correlation output includes both defect rate per unit produced and share of total defects | Must | **Given** F07 (2,400 units, 615 defective) and F03 (3,100 units, 91 defective), **when** correlated, **then** F07 shows a 25.6% rate and 73.2% share, and F03 shows 2.9% / 10.8% — both figures present for both machines. |
| REQ-05.2 | High-volume equipment is not flagged high-risk on share alone | Must | **Given** two machines with equal share of defects but different unit volumes, **when** ranked, **then** the one with the lower per-unit defect rate is not labeled higher-risk than the other. |

## 4.6 Root-Cause Analysis (FR-06)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-06.1 | Root cause output is framed as "probable contributing factor," never as proven causality | Must | **Given** any Root Cause Agent output, **when** rendered, **then** the UI/text template used is the "probable factor" template (BR-04), with no alternate "confirmed cause" template reachable. |
| REQ-06.2 | Root cause combines image, process, equipment, statistical, historical and documentation evidence | Must | **Given** the B1847/F07 scenario, **when** investigated, **then** the returned evidence list includes at least one item from each of: image, process, equipment/historical, SOP categories, or explicitly notes which are missing (REQ-16.1). |

## 4.7 Evidence-Based Explanation (FR-07)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-07.1 | Every recommendation/finding renders its evidence list in the UI | Must | **Given** a Root Cause Agent result with a non-empty `evidence[]`, **when** displayed, **then** each evidence item's source type and reference are visible without an extra click. |
| REQ-07.2 | No agent result with confidence above the "low" threshold may have an empty evidence list | Must | **Given** an `AgentResult` with `confidence` ≥ medium threshold, **when** validated against the schema (DDD §4.4), **then** an empty `evidence[]` is rejected before reaching the user. |

## 4.8 Historical Context (FR-08)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-08.1 | Historical matches are retrieved by equipment/defect-category similarity | Must | **Given** Batch B1847 (F07, firing defect), **when** Context Agent runs, **then** Batch B1632 (same equipment, same defect family) appears in `historical_matches[]` with a similarity score. |
| REQ-08.2 | Historical information always displays its source | Must | **Given** any historical match or SOP reference shown to a user, **when** rendered, **then** its source identifier (batch ID / SOP ID) is visible (BR-06). |

## 4.9 Corrective Action Generation (FR-09)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-09.1 | At least one candidate action is generated per probable-cause family, each with a cost tier and expected improvement | Must | **Given** the F07 firing-variation cause, **when** Optimization Agent runs, **then** ≥2 candidate actions are returned, each with `cost` and `expected_improvement`. |

## 4.10 What-If Simulation (FR-10)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-10.1 | Simulation output is always labeled as a prediction | Must | **Given** any simulation result, **when** rendered, **then** the UI prefixes it "Predicted," never "Result" or "Actual." |
| REQ-10.2 | Simulation recomputes the process-anomaly model under a counterfactual parameter change | Must | **Given** a request to reduce firing-temperature variance, **when** simulated, **then** the returned predicted defect rate differs from the current defect rate and is computed, not interpolated by a fixed percentage. |

## 4.11 Action Optimization (FR-11)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-11.1 | Actions are ranked by a configurable weighted score (impact, cost, downtime, risk) | Must | **Given** the three F07 candidate actions, **when** ranked under default weights, **then** the ordering matches the weighted-score formula in DDD §5 FR-11, not an arbitrary/static order. |
| REQ-11.2 | Ranking weights are configurable per deployment without a code change | Should | **Given** a business-priority config change (e.g., cost weighted higher), **when** saved, **then** the next ranking reflects the new weights. |

## 4.12 Human-in-the-Loop (FR-12)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-12.1 | No API endpoint writes to `Process` or `Equipment` tables from an automated/agent context | Must | **Given** a full audit of the API surface (openapi.yaml), **when** reviewed, **then** zero write endpoints exist for `Process`/`Equipment` outside manual, human-authored administrative correction, and none are reachable from any agent or scheduled job. |
| REQ-12.2 | Every action passes through Approve/Reject/Modify before being recorded | Must | **Given** a system-authored recommendation, **when** a user interacts with it, **then** the only recorded outcomes are `approved`, `rejected`, or `modified`, each tied to a named user. |

## 4.13 Validation (FR-13)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-13.1 | Predicted vs. actual outcome is recorded after the next batch completes | Must | **Given** an approved action on B1847 and a subsequent batch on the same equipment, **when** that batch completes, **then** `Incident.outcome` records both predicted and actual defect-rate change. |

## 4.14 Confidence and Uncertainty (FR-14)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-14.1 | Confidence maps to one of High/Medium/Low/Conflicting via configurable thresholds | Must | **Given** a confidence score and the current `ConfidenceThresholds` config, **when** evaluated, **then** the resulting band matches the BRD FR-14 table, and changing the config changes the band without a release. |
| REQ-14.2 | Low confidence routes to "insufficient evidence"; conflicting routes to "manual investigation required" | Must | **Given** two agent results, one below the Low threshold and one flagged conflicting, **when** displayed, **then** each shows its distinct corresponding message — they are not interchangeable. |
| REQ-14.4 | All confidence/severity/health/autonomy states render via the single chip component | Must | **Given** any of the four state families, **when** rendered anywhere in the UI, **then** the same chip component/classes from STYLE_GUIDE.html are used — no ad hoc color-only indicator exists elsewhere. |

## 4.15 Out-of-Distribution Detection (FR-15)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-15.1 | An OOD input is flagged regardless of raw classification confidence | Must | **Given** an image with an OOD score above the configured threshold, **when** classified, **then** the response is "unknown defect pattern — manual inspection required," even if the raw softmax confidence was high. |

## 4.16 Missing Data Handling (FR-16)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-16.1 | Missing critical data is recorded as a gap, never defaulted | Must | **Given** a batch missing firing-temperature telemetry, **when** analyzed, **then** `data_gaps` includes "firing_temperature missing" and no value is substituted in its place. |
| REQ-16.2 | Each data gap reduces confidence by a defined penalty | Must | **Given** two otherwise-identical investigations, one with a data gap and one without, **when** compared, **then** the one with the gap has strictly lower confidence. |

## 4.17 Conflicting Evidence (FR-17)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-17.1 | Evidence sources disagreeing beyond the configured divergence threshold produce a conflict response, not a ranked cause | Must | **Given** high image-based defect probability with normal process data and no historical match, **when** analyzed, **then** the response is "evidence conflict detected — additional inspection recommended," with no probable-cause ranking shown. |

## 4.18 RTSP / System Camera / Additional Camera Models (FR-18)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-18.1 | A camera can only serve EL inspection if registered EL-capable with confirmed capture conditions | Must | **Given** a camera registered as `visual` (not EL-capable), **when** an attempt is made to bind it to an EL inspection station, **then** the system rejects the binding. |
| REQ-18.2 | Camera health is monitored and surfaced as Online/Degraded/Offline | Must | **Given** three consecutive missed heartbeats, **when** checked, **then** status transitions to Degraded; sustained failure transitions to Offline, both visible on the Camera Admin screen. |
| REQ-18.3 | Camera/RTSP disconnection does not block production | Must | **Given** an Offline camera, **when** the line continues operating, **then** no system behavior halts the line — the station falls back to manual/upload inspection (BR-11). |
| REQ-18.5 | Only authenticated, encrypted transport is accepted for camera streams | Must | **Given** a plain, unauthenticated `rtsp://` stream, **when** registration is attempted in a production environment, **then** it is rejected in favor of `rtsps://` or an equivalent secured transport. |
| REQ-18.6 | Sampled frames are purged per the configured retention policy | Should | **Given** frames older than the configured retention window, **when** the retention job runs, **then** those frames are removed from storage. |

## 4.19 Real-Time Model Retraining (FR-19)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-19.1 | Retraining candidates are labeled primarily from engineer-confirmed data; auto-labels are flagged lower-trust | Must | **Given** a mix of confirmed and auto-labeled examples, **when** a training set is assembled, **then** auto-labeled examples are marked and excluded from the holdout set. |
| REQ-19.2 | A run below the minimum labeled-data volume halts before training | Must | **Given** a labeled dataset below the configured minimum, **when** a retraining run is requested, **then** it halts at the data-validation stage with a clear reason. |
| REQ-19.3 | A candidate model must meet or exceed the holdout threshold to proceed to staged rollout | Must | **Given** a candidate scoring below the configured holdout threshold vs. baseline, **when** evaluated, **then** it does not advance to staged rollout. |
| REQ-19.4 | Canary regression beyond threshold triggers automatic rollback | Must | **Given** a staged rollout whose canary error rate exceeds the configured regression threshold, **when** monitored, **then** the system automatically reverts to the prior model version and notifies the ML Operations Lead. |
| REQ-19.5 | The approver of a retraining promotion is never the requester | Must | **Given** a retraining run requested by user A, **when** user A attempts to approve its own promotion, **then** the request is rejected (BR-10; enforced by both API check and DB constraint per DDD §11.2). |
| REQ-19.6 | Retraining data/models are isolated per tenant unless explicitly shared | Must | **Given** two tenants, **when** a retraining run executes for Tenant 1, **then** no Tenant 2 data is included unless a `cross_tenant_share` authorization exists. |

## 4.20 Autonomous Production Decision Support (FR-20)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-20.1 | At Level A, no action is pre-selected | Must | **Given** a line configured to Autonomy Level A, **when** recommendations are shown, **then** no action carries a "pre-selected" or default-approved state. |
| REQ-20.2 | At Level B, the top-ranked action is pre-selected but still requires explicit approval from an authorized role | Must | **Given** Level B, **when** a recommendation is generated, **then** it cannot be recorded as an action without a distinct approval event (see also REQ-12.2). |
| REQ-20.3 | Safety-constraint-violating actions are filtered and the reason is shown, not silently dropped | Must | **Given** a candidate action violating a configured `SafetyConstraint`, **when** ranking runs, **then** it is excluded from the visible list and appears in a "filtered" log with its `filter_reason`. |
| REQ-20.4 | If Agent Hub/decision support is unavailable, production is not blocked | Must | **Given** Agent Hub is unreachable, **when** an investigation is requested, **then** the API returns a degraded-mode response and the UI displays raw inspection results without recommendations, and no production-blocking state is set (BR-11). |
| REQ-20.5 | Level C is not reachable via configuration alone | Must | **Given** any configuration change attempt setting `autonomy_level = C`, **when** attempted at any tier, **then** the system rejects it — enabling Level C requires a code release gated by the FR-20 sign-off criteria, not a config toggle. |

## 4.21 Defect Taxonomy Management (FR-21)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-21.1 | Taxonomy entries carry category, subtype, severity, root-cause family and suggested action | Must | **Given** any taxonomy entry, **when** viewed, **then** all five fields are populated (or explicitly marked not-yet-mapped). |
| REQ-21.2 | Publishing a new taxonomy version does not invalidate historical records | Must | **Given** a published version that removes a category, **when** historical `Cell`/`Incident` rows referencing it are queried, **then** they remain readable via the `TaxonomyMigration` mapping. |
| REQ-21.3 | A taxonomy version change triggers a model-compatibility check | Must | **Given** a new taxonomy version that removes a category the CV model still outputs, **when** published, **then** a compatibility flag is raised and a retraining-review candidate is created (linking to FR-19). |

## 4.22 Role-Based Access Control (FR-22)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-22.1 | Every sensitive action is restricted to an authorized role | Must | **Given** a Viewer account, **when** any write/approval endpoint is called, **then** the API returns 403 and the attempt is audit-logged. |
| REQ-22.2 | Platform Administrator cannot approve retraining; ML Operations Lead cannot manage RBAC/cameras/taxonomy | Must | **Given** each role attempts the other's restricted action, **when** attempted, **then** both are denied (DDD §10.2 role split). |
| REQ-22.4 | Requester and approver are always distinct users on any approval-gated action | Must | See REQ-19.5; identical check applies to recommendation approvals (DDD §10.3). |
| REQ-22.5 | Data access is scoped per tenant | Must | **Given** a user of Tenant 1, **when** querying any list endpoint, **then** no Tenant 2 rows are returned, even if requested by ID. |
| REQ-22.6 | SSO/LDAP/SAML federation is supported at Pilot tier and above | Should | **Given** a Pilot-tier deployment configured with SSO, **when** a user logs in via the identity provider, **then** a session is established with the correct role mapping. |

---

# 5. Non-Functional Requirements

## 5.1 Performance (NFR-01)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N01.1 | Image analysis completes in <5s | Must | Measured under prototype load per DDD §14.1. |
| REQ-N01.2 | Full agent investigation completes in <30s | Must | Measured end-to-end from `/investigations` POST to final status. |
| REQ-N01.3 | Dashboard queries respond in <3s | Must | Measured for normal-size batch lists. |
| REQ-N01.4 | Retraining cycle completes in <24h (scheduled cycle) | Should | Configurable per deployment; measured at Pilot tier. |

## 5.2 Security (NFR-04)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N04.1 | All requests require a valid JWT except `/auth/*` | Must | Unauthenticated request to any other endpoint returns 401. |
| REQ-N04.2 | Camera/RTSP transport is authenticated and encrypted | Must | See REQ-18.5. |
| REQ-N04.3 | All sensitive operations are audit-logged | Must | See REQ-N05.1. |

## 5.3 Reliability (NFR-03)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N03.1 | Agent/model/camera failures degrade gracefully, never block production | Must | See REQ-20.4, REQ-18.3. |

## 5.4 Usability

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N06.1 | Every state-carrying UI element encodes state in both color and text label | Must | Verified against STYLE_GUIDE.html §Status & Badges; no color-only indicator ships. |
| REQ-N06.2 | All interactive elements have a visible keyboard-focus state | Must | Tab through WIREFRAMES.html/STYLE_GUIDE.html controls; focus ring is visible on each. |
| REQ-N06.3 | All motion is disabled outright, not merely shortened, under `prefers-reduced-motion: reduce` | Must | **Given** the OS reduced-motion setting is enabled, **when** any product-UI or landing-page surface loads, **then** scroll reveals, hero sequence, ambient blobs and count-up animations render in their final state immediately — no fade/slide/typing sequence plays. |
| REQ-N06.4 | Landing-page content is fully readable if JavaScript/animation fails to run | Must | **Given** a browser with JS disabled or an animation library failure, **when** the landing page loads, **then** all copy, stats and CTAs are present and legible without requiring any scroll-reveal or count-up to complete first. |
| REQ-N06.5 | Product-UI motion is restrained to state-confirming transitions only; landing-page motion may be decorative but must never delay time-to-readable-content | Should | **Given** the landing page's ambient background/spotlight-hover effects, **when** disabled or removed, **then** no layout or content is affected — they are additive only (DDD §16.1.2). |

## 5.5 Auditability (NFR-05)

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N05.1 | Input data, model result, recommendation, user decision, and outcome are all independently queryable | Must | Each has a concrete table (DDD §11.2); a full investigation can be reconstructed from `AuditLog` + `Incident` + `Approval` alone. |
| REQ-N05.2 | Audit log is append-only | Must | No UPDATE/DELETE grant exists on the `AuditLog` table at the DB role level. |

## 5.6 Scalability

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N07.1 | Camera ingestion throughput is decoupled from CV inference throughput | Should | A frame-rate burst on one camera does not increase latency for other cameras' inspections (DDD §14.1). |

## 5.7 Maintainability

| REQ | Statement | Priority | Acceptance Criteria |
|---|---|---|---|
| REQ-N08.1 | Confidence thresholds, safety constraints and ranking weights are configuration, not code | Should | Changing any of the three takes effect without a deployment (see REQ-14.1, REQ-20.3, REQ-11.2). |

---

# 6. Use Case Specifications

## UC-01: Investigate a Defective Batch

* **Actor:** Quality Engineer
* **Precondition:** Batch exists with inspection data available.
* **Main Flow:** User opens Dashboard → selects batch → clicks Investigate → Agent Hub runs Inspection/Process/Context/Root Cause/Optimization/Simulation → ranked recommendation displayed.
* **Alternate Flows:** Missing data (REQ-16.1) → confidence reduced, gap shown. Conflicting evidence (REQ-17.1) → conflict message shown, no ranked cause. OOD input (REQ-15.1) → "unknown pattern" message.
* **Postcondition:** An `Investigation` record and `Recommendation` exist, ready for approval (UC-02).

## UC-02: Approve a Corrective-Action Recommendation

* **Actor:** Process/Quality/Equipment Engineer (role matching the action category)
* **Precondition:** A `Recommendation` exists from UC-01.
* **Main Flow:** User reviews ranked actions + simulation → Approve / Reject / Modify.
* **Alternate Flow:** User attempting to approve their own authored override where disallowed → rejected (REQ-22.4).
* **Postcondition:** `Approval` record created with `requested_by`/`approver` distinct; `Incident` updated.

## UC-03: Register a Camera

* **Actor:** Platform Administrator
* **Precondition:** Camera stream reachable over `rtsps://`.
* **Main Flow:** Admin opens Camera Admin → enters stream URL, type, EL-capable flag → Register.
* **Alternate Flow:** EL-capable flag unset, later bound to an EL station → rejected (REQ-18.1).
* **Postcondition:** `Camera` row created; health monitoring begins.

## UC-04: Approve a Model Retraining Promotion

* **Actor:** ML Operations Lead
* **Precondition:** A `RetrainingRun` has passed holdout evaluation and staged rollout.
* **Main Flow:** ML Ops Lead reviews holdout/canary metrics on Retraining Console → Approve.
* **Alternate Flow:** ML Ops Lead is the same user who requested the run → rejected (REQ-19.5).
* **Postcondition:** `ModelVersion.status = production`; prior version retained for rollback.

## UC-05: Publish a Taxonomy Version

* **Actor:** Platform Administrator
* **Precondition:** Taxonomy changes drafted.
* **Main Flow:** Admin edits categories → Publish → compatibility check runs against CV model output classes.
* **Alternate Flow:** Mismatch found → retraining-review candidate created (REQ-21.3), publish still succeeds but is flagged.
* **Postcondition:** New `TaxonomyVersion` active; `TaxonomyMigration` rows created for any removed/merged categories.

## UC-06: Manage RBAC Roles & Permissions

* **Actor:** Platform Administrator
* **Precondition:** None.
* **Main Flow:** Admin opens RBAC & Audit → assigns/edits a user's role.
* **Alternate Flow:** Admin attempts to grant themselves retrain-approval permission → out of scope for Platform Administrator's permission set; rejected (REQ-22.2).
* **Postcondition:** `RolePermission`/`User.role_id` updated; change audit-logged.

## UC-07: Run a What-If Simulation

* **Actor:** Process Engineer
* **Precondition:** An investigation with process data exists.
* **Main Flow:** User adjusts a process parameter on the Recommendation screen → system returns predicted defect rate.
* **Postcondition:** Result displayed with "Predicted" label (REQ-10.1); not persisted as an actual outcome.

---

# 7. Data Requirements

Full physical schema is defined in DDD.MD §11.2. This SRS treats each table's primary/foreign keys and the `Approval.requested_by <> approver` constraint as verifiable requirements (REQ-19.5/REQ-22.4) rather than restating the schema. Any new field added to a table listed there requires a corresponding REQ-ID addition here before it is considered specified.

---

# 8. Business Rules (Verifiable Form)

| BRD Rule | SRS Verifiable Form |
|---|---|
| BR-01 | REQ-02.1/REQ-02.2 — no auto-rejection endpoint exists keyed off classification alone |
| BR-02 | REQ-14.2 |
| BR-03 | REQ-16.1 |
| BR-04 | REQ-06.1 |
| BR-05 | REQ-12.2 |
| BR-06 | REQ-08.2 |
| BR-07 | REQ-12.1 |
| BR-08 | REQ-20.5 |
| BR-09 | REQ-22.1 |
| BR-10 | REQ-19.5, REQ-22.4 |
| BR-11 | REQ-18.3, REQ-20.4 |

---

# 9. Traceability Matrix

| BRD FR/NFR | SRS REQ-IDs | DDD Component | Verification |
|---|---|---|---|
| FR-01 | REQ-01.1–01.3 | DDD §5 (`Batch`) | Test |
| FR-02/03 | REQ-02.1–02.2, REQ-03.1–03.2 | DDD §5, §5.1 | Test |
| FR-04 | REQ-04.1–04.2 | DDD §5 | Test |
| FR-05 | REQ-05.1–05.2 | DDD §5 (rate normalization) | Test |
| FR-06/07 | REQ-06.1–06.2, REQ-07.1–07.2 | DDD §4.2, §4.4 | Test + Inspection |
| FR-08 | REQ-08.1–08.2 | DDD §3.2 (Context Substrate) | Test |
| FR-09/10/11 | REQ-09.1, REQ-10.1–10.2, REQ-11.1–11.2 | DDD §5, §8.1 | Test |
| FR-12 | REQ-12.1–12.2 | DDD §2.3 | Inspection + Test |
| FR-13 | REQ-13.1 | DDD §4.2/4.3 | Test |
| FR-14 | REQ-14.1–14.2, REQ-14.4 | DDD §5.1 | Test + Demo |
| FR-15 | REQ-15.1 | DDD §5 | Test |
| FR-16/17 | REQ-16.1–16.2, REQ-17.1 | DDD §4.4, §13 | Test |
| FR-18 | REQ-18.1–18.6 | DDD §6 | Test + Demo |
| FR-19 | REQ-19.1–19.6 | DDD §7 | Test + Inspection |
| FR-20 | REQ-20.1–20.5 | DDD §8 | Test + Inspection |
| FR-21 | REQ-21.1–21.3 | DDD §9 | Test |
| FR-22 | REQ-22.1–22.6 | DDD §10 | Test + Inspection |
| NFR-01 | REQ-N01.1–N01.4 | DDD §14.1 | Test |
| NFR-03 | REQ-N03.1 | DDD §13 | Test |
| NFR-04 | REQ-N04.1–N04.3 | DDD §10 | Test |
| NFR-05 | REQ-N05.1–N05.2 | DDD §10.5, §14.3 | Inspection |

---

# 10. Appendix

## 10.1 Acceptance Test Approach

Each `Must`-priority REQ requires an automated test before its owning capability is marked done at any tier; `Should`/`Could` items may be verified by Demo at the Hackathon Demo tier and upgraded to Test by Pilot. The Given/When/Then phrasing above is written to be pasted directly into a test framework's scenario syntax.

## 10.2 Open Issues

Carried from DDD.MD §18.1 (vector-store choice, burst-sampling threshold calibration, `AutonomyConfig` granularity) — none block writing tests against the REQ-IDs above, but each should resolve before its dependent REQ is finalized at Pilot tier.
