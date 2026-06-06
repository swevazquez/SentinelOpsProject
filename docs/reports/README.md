## Weekly Report Generation Workflow

SentinelOps weekly reports are generated from templates stored under:

    docs/template/

Generated reports are stored under:

    docs/reports/

### Weekly Report Template

The canonical weekly report template is:

    docs/template/weekly-report-template.md

All weekly reports should follow the structure, sections, and formatting defined in this template unless explicitly instructed otherwise.

---

## Weekly Reporting Expectations

Weekly reports represent cumulative sprint progress and should reflect:
- Sprint planning activities
- Product backlog grooming
- Sprint backlog updates
- Definition of Done refinements
- Acceptance criteria updates
- Source code development progress
- Important commits
- Testing activities
- Requirement-to-test mappings
- Reproducible test execution steps and evidence
- Burndown progress
- Risks and blockers
- Planned work for the following week

The writing style should remain:
- professional,
- concise,
- engineering-focused,
- traceable to actual implementation progress.

Avoid generic AI-generated phrasing or exaggerated progress statements.

---

## Weekly Time Window

The course reporting window runs:

    Monday through Sunday

When generating a weekly report:
- analyze repository activity,
- commits,
- backlog changes,
- documentation updates,
- architecture updates,
- testing additions,
- and implementation progress

ONLY within the applicable reporting window.

---

## Report Naming Convention

Generated reports should follow this naming structure:

    docs/reports/week-XX-progress-report.md

Examples:

    docs/reports/week-03-progress-report.md
    docs/reports/week-04-progress-report.md

---

## Incremental Context Awareness

When generating a new weekly report:

1. Review the previous weekly report if one exists.
2. Analyze repository progress since the prior reporting period.
3. Avoid repeating completed accomplishments from earlier reports unless:
   - they were extended,
   - refined,
   - tested further,
   - or materially changed.
4. Track continuity between:
   - sprint goals,
   - backlog changes,
   - implementation progress,
   - testing progress,
   - and planned activities.

The report should read as part of a continuous engineering effort rather than isolated weekly summaries.

---

## Expected Inputs for Weekly Report Generation

When asked to generate a report:
- inspect repository structure,
- review recent commits,
- inspect Jira/backlog updates if available,
- inspect architecture and documentation changes,
- inspect tests added or modified,
- inspect completed or partially completed requirements.

Use actual repository evidence whenever possible.

Important commits must be linked directly to their GitHub commit pages. Do not report only an unlinked short hash.

Example:

    [`abcdef1`](https://github.com/OWNER/REPOSITORY/commit/FULL_COMMIT_SHA)

Do not fabricate:
- commits,
- completed functionality,
- test coverage,
- sprint progress,
- or backlog changes.

If information is unavailable, explicitly state assumptions or mark items as planned/in-progress.

---

## Burndown and Agile Reporting

Weekly reports should include:
- sprint progress assessment,
- remaining work summary,
- implementation risks,
- backlog grooming changes,
- sprint velocity observations where applicable.

If no backlog changes occurred during the reporting window, explicitly state:

    No significant backlog changes occurred during this reporting period.

---

## Test Reporting Expectations

For all Sprint backlog requirements:
- maintain requirement-to-test traceability,
- document acceptance criteria,
- document current test status,
- provide a complete test specification for every test case in the traceability matrix,
- include exact execution commands or UI actions,
- state the expected result for each meaningful step,
- record actual step results when executed,
- link supporting evidence such as CI runs, test files, logs, screenshots, or output artifacts,
- and document cleanup or reset actions.

A test specification is incomplete if it only states a general action such as “run the tests.” Another developer should be able to reproduce the test from the report without reading the implementation first.

For automated tests, include:
- the narrow command that exercises the specific behavior,
- the broader regression command,
- expected pass/fail output,
- and the relevant test file or CI run.

For integration, system, or workflow tests, include:
- environment and service startup,
- test data preparation,
- workflow or request execution,
- status and output verification,
- failure-path checks when applicable,
- evidence capture,
- and cleanup.

Test cases may initially be:
- planned,
- partial,
- mocked,
- or manually executed,

provided the report clearly communicates the current implementation state.

---

## Markdown Export Expectations

Weekly reports are authored in Markdown and exported to PDF externally.

Generated Markdown should:
- remain clean and readable,
- avoid excessive inline HTML,
- use relative image paths,
- preserve heading consistency,
- preserve table formatting for PDF export.

Images should be referenced relative to the report location.

Example:

    ![Sprint Burndown](../images/week-03-burndown.png)

---

## Scope Control

Weekly reports should reflect realistic solo-developer progress.

Prefer:
- accurate incremental progress,
- working vertical slices,
- meaningful implementation milestones,
- practical testing progress.

Avoid:
- overstating completion,
- speculative future implementation,
- enterprise-scale claims,
- or artificial complexity.
