# SentinelOps Weekly Progress Report

| Field | Value |
|---|---|
| Course | SWENG 894 - Software Engineering Capstone Experience |
| Project | SentinelOps |
| Student | Eli Vazquez |
| Sprint | Sprint 1 |
| Reporting Week | Week 2 |
| Reporting Period | 2026-06-01 to 2026-06-07 |
| Report Date | 2026-06-06 |
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |

---

# Sprint Goal

The Sprint 1 goal remains establishing a working and repeatable predictive-maintenance
data workflow. The sprint covers telemetry generation, raw persistence, feature
engineering, workflow orchestration, failure visibility, component separation, and
repeatable local execution.

Week 2 also added a bounded UI design activity. Dashboard wireframes were prepared
before Sprint 2 implementation so operational requirements, user priorities, interface
states, and expected API dependencies are explicit.

---

# Sprint Planning

## Groomed Product Backlog Summary

| ID | Requirement / User Story | Priority | Estimation | Sprint | Current Status |
|---|---|---|---|---|---|
| SCRUM-1 / FR-01 | Telemetry Generation and Ingestion | High | 5 SP | Sprint 1 | Done |
| SCRUM-2 / FR-02 | Raw Telemetry Storage | High | 3 SP | Sprint 1 | Done |
| SCRUM-3 / FR-03 | Feature Engineering Processing | High | 5 SP | Sprint 1 | Done |
| SCRUM-4 / FR-04 | Workflow Orchestration | High | 8 SP | Sprint 1 | To Do |
| SCRUM-17 / NFR-01 | Failed Workflow Detection and Reporting | High | 3 SP | Sprint 1 | To Do |
| SCRUM-19 / NFR-03 | Component Responsibility Separation | High | 2 SP | Sprint 1 | To Do |
| SCRUM-20 / NFR-04 | Repeatable Local Execution | Medium | 2 SP | Sprint 1 | To Do |
| SCRUM-27 / UX-01 | Operational Dashboard Wireframe | High | 3 SP | Sprint 1 | In Review |

## Sprint Backlog

| ID | Requirement / User Story | Priority | Estimation | Status |
|---|---|---|---|---|
| SCRUM-1 / FR-01 | Telemetry Generation and Ingestion | High | 5 SP | Done |
| SCRUM-2 / FR-02 | Raw Telemetry Storage | High | 3 SP | Done |
| SCRUM-3 / FR-03 | Feature Engineering Processing | High | 5 SP | Done |
| SCRUM-4 / FR-04 | Workflow Orchestration | High | 8 SP | To Do |
| SCRUM-17 / NFR-01 | Failed Workflow Detection and Reporting | High | 3 SP | To Do |
| SCRUM-19 / NFR-03 | Component Responsibility Separation | High | 2 SP | To Do |
| SCRUM-20 / NFR-04 | Repeatable Local Execution | Medium | 2 SP | To Do |
| SCRUM-27 / UX-01 | Operational Dashboard Wireframe | High | 3 SP | In Review |

## Definition of Done

| Area | Definition of Done Criteria |
|---|---|
| Requirements | Requirement and acceptance criteria are reviewed in Jira. |
| Design | Affected architecture, workflow, or interface design is updated. |
| Development | Changes are committed on a traceable story branch. |
| Testing | Automated or manual validation is documented with reproducible steps. |
| Integration | Local CI and GitHub Actions complete successfully. |
| Documentation | Relevant documentation and weekly-report evidence are updated. |
| Validation | The result is reviewed against every acceptance criterion before Jira closure. |

## Acceptance Criteria for Current Work

| Requirement ID | Acceptance Criteria |
|---|---|
| SCRUM-4 / FR-04 | Given the Sprint 1 Airflow workflow is configured, when triggered, telemetry generation, raw persistence, feature engineering, and processed-feature persistence execute in order. |
| SCRUM-27 / UX-01 | Given project stakeholders and requirements, when the wireframes are reviewed, asset health, workflow status, maintenance priority, and prediction summaries have a clear hierarchy. |
| SCRUM-27 / UX-01 | Given data may be incomplete, when alternate states are reviewed, loading, empty, failed, unavailable, and permission-required behavior is defined. |
| SCRUM-27 / UX-01 | Given Sprint 2 requires backend integration, when design annotations are reviewed, major panels identify user purpose and expected API or data sources. |
| SCRUM-27 / UX-01 | Given the design is complete, when repository documentation is reviewed, rationale and traceability to SCRUM-10 / FR-10 are available. |

---

# Backlog Grooming

## Backlog Changes This Week

| Change Type | Requirement ID | Description | Rationale | Impact |
|---|---|---|---|---|
| Updated scope | SCRUM-4 / FR-04 | Limited Sprint 1 orchestration to telemetry generation, raw persistence, feature engineering, and processed-feature persistence. | Predictive scoring and prediction reporting are planned under Sprint 2 stories and should not be implicit Sprint 1 dependencies. | Makes acceptance criteria implementable and testable without pulling Sprint 2 functionality forward. |
| Added | SCRUM-27 / UX-01 | Added a 3-point operational dashboard wireframe story. | Early interface design provides visible UI progress and clarifies user needs before dashboard implementation. | Sprint 1 scope increased from 28 to 31 story points. SCRUM-27 now blocks SCRUM-10. |
| Refined quality process | SCRUM-20 / NFR-04 | Expanded the weekly-report template with detailed test execution and direct commit-link expectations. | Professor feedback identified incomplete test execution detail and limited commit traceability. | Future reports require reproducible test procedures and reviewable code evidence. |

## Backlog Grooming Rationale

The grooming changes protect the vertical-slice boundary. SCRUM-4 now coordinates only
the processing capabilities available during Sprint 1, while predictive scoring and
reporting remain in Sprint 2. SCRUM-27 was added as a small design precursor rather
than expanding SCRUM-10 into the current sprint. This produces reviewable UI evidence
without claiming production frontend implementation.

---

# Source Code Development

## Summary of Contributions

Week 2 work focused on reporting quality, dashboard design, and requirements
traceability.

Key contributions include:

- Updated the weekly-report template to require complete execution procedures and
  direct GitHub commit links.
- Reorganized diagram sources into architecture, workflow, and UI directories.
- Created editable Excalidraw and Mermaid wireframes for the operations overview,
  asset details, workflow details, and operations assistant.
- Exported reviewed 1440 by 1024 PNG images for report and documentation use.
- Documented stakeholder needs, design rationale, alternate states, API/data
  dependencies, and traceability to SCRUM-10 / FR-10.
- Reviewed rendered wireframes and corrected title, button-label, and panel clipping.

## Repository Information

| Resource | Link |
|---|---|
| Git Repository | <https://github.com/swevazquez/SentinelOpsProject> |
| Jira Board | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |
| SCRUM-27 | <https://psu-capstone-sentinelops.atlassian.net/browse/SCRUM-27> |
| SCRUM-10 | <https://psu-capstone-sentinelops.atlassian.net/browse/SCRUM-10> |

## Important Commits

| Commit | Commit Summary | Related Requirement / User Story | Notes |
|---|---|---|---|
| [`acf0220`](https://github.com/swevazquez/SentinelOpsProject/commit/acf02208db9c24df9a580423b9c4f9c2d3274802) | Improve weekly report test specifications | SCRUM-20 / NFR-04 | Implements professor feedback for reproducible tests and direct commit traceability. |
| [`c075ea1`](https://github.com/swevazquez/SentinelOpsProject/commit/c075ea1f0080963e174dd999152577dd9ea38db8) | Add operational dashboard wireframes | SCRUM-27 / UX-01 | Adds editable sources, rendered images, design rationale, data dependencies, and requirement traceability. |

## Dashboard Wireframe Evidence

![SentinelOps Operations Overview Wireframe](../images/ui/wireframes/dashboard-wireframe.png)

## Burndown Summary

Sprint scope increased by 3 points when SCRUM-27 was added. The wireframe story is
implemented on its feature branch and remains in review until its pull request is
accepted. Jira continues to count 13 completed points until that closure.

| Metric | Value |
|---|---|
| Sprint Total Estimated Effort | 31 story points |
| Completed Effort | 13 story points |
| In Review | 3 story points |
| Remaining To Do | 15 story points |
| Sprint Status | At Risk |

## Burndown Chart

The Sprint 1 burndown will be regenerated after SCRUM-27 review so the chart reflects
the accepted story status rather than counting in-review work as completed.

---

# Software Testing

## Testing Overview

Testing this week included repository regression validation, structural validation of
the Excalidraw scene files, native rendering of all wireframes, image-dimension checks,
and a visual containment review for clipping and overlapping elements.

## Requirement-to-Test Traceability Matrix

| Requirement ID | Test Case ID | Test Type | Test Objective | Status |
|---|---|---|---|---|
| SCRUM-27 / UX-01 | TC-UX01-01 | System / UAT | Verify all editable wireframes render and communicate the intended operational hierarchy without clipping. | Passed |
| SCRUM-27 / UX-01 | TC-UX01-02 | Structural | Verify Excalidraw scenes and exported PNG evidence are complete and valid. | Passed |
| SCRUM-20 / NFR-04 | TC-NFR04-03 | Regression / CI | Verify documentation changes do not break the existing Sprint 1 validation workflow. | Passed |

## Test Case Specifications

### TC-UX01-01 - Wireframe Rendering and Human Review

| Field | Description |
|---|---|
| Related Requirement | SCRUM-27 / UX-01 |
| Test Type | System / User Acceptance |
| Objective | Confirm that all four wireframes render as understandable operational interfaces without clipped labels, overlapping controls, or content outside the canvas. |
| Preconditions | Branch `SCRUM-27-dashboard-wireframes`; Google Chrome installed; Excalidraw export dependencies available in a temporary local renderer. |
| Test Data / Parameters | Four `.excalidraw` files under `docs/diagrams/ui/`; 1440 by 1024 export viewport. |
| Execution Environment | macOS; local Chrome headless renderer; Excalidraw v2 scene format. |
| Expected Final Result | Each scene renders at 1440 by 1024, all controls and labels are visible, information hierarchy is understandable, and alternate states are represented. |
| Actual Result | All four scenes rendered. Workflow title/status overlap, artifact-panel overflow, and retry-button clipping were identified and corrected. Final containment review passed. |
| Evidence | `docs/images/ui/wireframes/*.png` and commit [`c075ea1`](https://github.com/swevazquez/SentinelOpsProject/commit/c075ea1f0080963e174dd999152577dd9ea38db8). |
| Cleanup / Reset | Stop the temporary localhost rendering server and remove temporary renderer files. |
| Status | Passed |

#### Execution Steps

1. Open the SCRUM-27 branch and locate the editable scenes.
   - Command or action: `git switch SCRUM-27-dashboard-wireframes && find docs/diagrams/ui -name '*.excalidraw' -type f`
   - Expected result: Four Excalidraw files are listed.
2. Render each scene through Excalidraw's native SVG export in a local browser.
   - Command or action: Open each scene with the local renderer at a 1440 by 1024 viewport.
   - Expected result: Dashboard, asset details, workflow details, and assistant scenes render without a blank canvas or export error.
3. Review each rendered scene for information hierarchy and operational meaning.
   - Command or action: Inspect navigation, summary metrics, detail panels, statuses, evidence, and action controls.
   - Expected result: Each view has a clear user purpose and consistent navigation; workflow and assistant actions are understandable.
4. Check boundaries and label containment.
   - Command or action: Compare text and control bounds and inspect the rendered PNGs at full resolution.
   - Expected result: No label exceeds its control, no panel content is clipped, and all scene elements remain inside the canvas.
5. Save evidence and stop temporary services.
   - Command or action: Save PNGs under `docs/images/ui/wireframes/` and stop the local renderer.
   - Expected result: Four reviewable PNGs remain in the repository and no temporary server remains active.

#### Step Results

| Step | Actual Result | Status |
|---|---|---|
| 1 | Four editable Excalidraw scenes were present. | Passed |
| 2 | All scenes rendered successfully at 1440 by 1024. | Passed |
| 3 | Each scene presented a coherent operational workflow and consistent navigation. | Passed |
| 4 | Three workflow-view issues were corrected; the final containment audit reported no overflow. | Passed |
| 5 | Four PNG evidence files were saved and the temporary server was stopped. | Passed |

### TC-UX01-02 - Wireframe Artifact Validation

| Field | Description |
|---|---|
| Related Requirement | SCRUM-27 / UX-01 |
| Test Type | Structural |
| Objective | Verify that editable scenes use the Excalidraw v2 format and that each PNG export has the expected dimensions. |
| Preconditions | SCRUM-27 wireframe files and ImageMagick are available. |
| Test Data / Parameters | `docs/diagrams/ui/*.excalidraw`; `docs/images/ui/wireframes/*.png`. |
| Execution Environment | Local macOS shell with `jq` and ImageMagick `magick`. |
| Expected Final Result | Four nonempty Excalidraw v2 scenes validate and four PNGs report dimensions of 1440 by 1024. |
| Actual Result | All scene files passed JSON checks and all four PNGs reported 1440 by 1024 dimensions. |
| Evidence | Editable files under `docs/diagrams/ui/` and exports under `docs/images/ui/wireframes/`. |
| Cleanup / Reset | None. |
| Status | Passed |

#### Execution Steps

1. Navigate to the repository.
   - Command or action: `cd /Users/ctrvazquez/workspace/capstone/SentinelOpsProject`
   - Expected result: The repository root is the current directory.
2. Validate each Excalidraw file.
   - Command or action: `for file in docs/diagrams/ui/*.excalidraw; do jq -e '.type == "excalidraw" and .version == 2 and (.elements | length > 0)' "$file" >/dev/null || exit 1; done`
   - Expected result: The command exits successfully with no invalid or empty scene.
3. Inspect every exported PNG.
   - Command or action: `for file in docs/images/ui/wireframes/*.png; do magick identify -format '%f %wx%h\n' "$file"; done`
   - Expected result: Four filenames are printed and each reports `1440x1024`.
4. Confirm source-to-export mapping.
   - Command or action: Review `docs/images/ui/wireframes/README.md`.
   - Expected result: Every PNG maps to an editable Excalidraw source.
5. Record the result.
   - Command or action: Add the observed result to this test specification.
   - Expected result: Validation evidence is reproducible from the report.

#### Step Results

| Step | Actual Result | Status |
|---|---|---|
| 1 | Repository root was available. | Passed |
| 2 | Four Excalidraw v2 scenes contained editable elements. | Passed |
| 3 | Four PNG files reported 1440 by 1024 dimensions. | Passed |
| 4 | The export index mapped each image to its source. | Passed |
| 5 | Results were recorded in the Week 2 report. | Passed |

### TC-NFR04-03 - Repository Regression Validation

| Field | Description |
|---|---|
| Related Requirement | SCRUM-20 / NFR-04 |
| Test Type | Regression / CI |
| Objective | Confirm that diagram reorganization and reporting changes preserve the repeatable Sprint 1 validation workflow. |
| Preconditions | Repository checkout with Python available and project scripts executable. |
| Test Data / Parameters | Default `RUN_ID=ci-smoke`; representative asset profiles. |
| Execution Environment | Local macOS shell and GitHub Actions-compatible validation script. |
| Expected Final Result | Unit tests pass, 96 telemetry rows and 4 feature rows are generated, Airflow syntax passes, and Markdown files are readable. |
| Actual Result | Thirteen unit tests passed; expected telemetry and feature counts were produced; all remaining checks passed. |
| Evidence | `./scripts/check-ci.sh` output and the SCRUM-27 branch CI run after push. |
| Cleanup / Reset | Generated smoke files remain ignored under `data/raw/` and `data/processed/`. |
| Status | Passed |

#### Execution Steps

1. Navigate to the repository.
   - Command or action: `cd /Users/ctrvazquez/workspace/capstone/SentinelOpsProject`
   - Expected result: Project scripts and configuration are available.
2. Execute the regression gate.
   - Command or action: `./scripts/check-ci.sh`
   - Expected result: Unit tests begin, followed by the Sprint 1 smoke workflow.
3. Verify automated tests.
   - Command or action: Review the unit-test section of the command output.
   - Expected result: Thirteen tests pass with no failures.
4. Verify workflow and documentation checks.
   - Command or action: Review generated row counts, Airflow syntax, and Markdown checks.
   - Expected result: 96 telemetry rows and 4 feature rows are persisted; syntax and documentation checks pass.
5. Record evidence.
   - Command or action: Confirm the final output states `CI checks passed.`
   - Expected result: The complete regression gate reports success.

#### Step Results

| Step | Actual Result | Status |
|---|---|---|
| 1 | Repository scripts were available. | Passed |
| 2 | The complete CI script executed. | Passed |
| 3 | Thirteen tests passed. | Passed |
| 4 | Expected workflow counts, Airflow syntax, and Markdown checks passed. | Passed |
| 5 | The command ended with `CI checks passed.` | Passed |

## Testing Summary

All planned Week 2 wireframe and regression checks passed. The review produced
corrective design changes rather than only confirming file existence, and the final
artifacts are reproducible from the documented commands.

---

# Risks, Roadblocks, and Mitigation

| Risk / Roadblock | Impact | Mitigation / Next Step |
|---|---|---|
| Sprint 1 scope increased while 15 implementation points remain. | Completing orchestration and supporting NFRs by June 14 is at risk. | Keep SCRUM-27 limited to design artifacts, close its review promptly, and begin SCRUM-4 next. |
| Jira Sprint 1 remains configured as a future sprint despite its May 25 start date. | Native Jira burndown and open-sprint queries are unavailable. | Correct the sprint state in Jira or continue generating report charts from issue status and story points. |
| Wireframes depend on APIs planned for later stories. | UI implementation cannot yet use live operational data. | Preserve the documented panel-to-data mapping as the integration contract for Sprint 2. |

---

# Plan for Next Week

Next week will focus on completing the Sprint 1 workflow foundation.

- Complete review and merge of SCRUM-27.
- Implement SCRUM-4 workflow orchestration against the groomed Sprint 1 scope.
- Add SCRUM-17 workflow failure detection and reporting.
- Close SCRUM-19 and SCRUM-20 with architecture and clean-checkout execution evidence.
- Update Jira status, sprint burndown, and the next weekly report from accepted work.

---

# Overall Sprint Assessment

Sprint 1 is currently at risk because 15 implementation points remain before the
June 14 sprint end, excluding the 3-point wireframe story in review. Week 2 improved
requirements clarity, UI design evidence, testing documentation, and traceability.
The immediate priority is completing SCRUM-4 and SCRUM-17 without expanding their
scope into Sprint 2 functionality.
