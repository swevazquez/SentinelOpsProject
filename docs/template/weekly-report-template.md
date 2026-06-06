# SentinelOps Weekly Progress Report Template

| Field | Value |
|---|---|
| Course | SWENG 894 – Software Engineering Capstone Experience |
| Project | SentinelOps |
| Student | Eli Vazquez |
| Sprint | Sprint X |
| Reporting Week | Week X |
| Reporting Period | Monday, Month DD, YYYY – Sunday, Month DD, YYYY |
| Report Date | Month DD, YYYY |
| Git Repository | [Insert Repository Link] |
| Jira Board | [Insert Jira Board Link] |

---

# Sprint Goal

The goal for this sprint is to [briefly describe the sprint objective]. This sprint focuses on [summarize the main development theme, such as environment setup, telemetry ingestion, workflow orchestration, API development, dashboard development, testing, or agent integration].

---

# Sprint Planning

## Groomed Product Backlog Summary

During this reporting period, the product backlog was reviewed to confirm priority, estimation, and sprint alignment. The backlog continues to organize requirements by functional value, technical dependency, implementation risk, and MVP priority.

| ID | Requirement / User Story | Priority | Estimation | Sprint | Current Status |
|---|---|---|---|---|---|
| FR-XX | [Requirement Title] | High / Medium / Low | X SP | Sprint X | Planned / In Progress / Done |
| NFR-XX | [Non-Functional Requirement Title] | High / Medium / Low | X SP | Sprint X | Planned / In Progress / Done |

## Sprint Backlog

The following requirements are included in the current sprint backlog.

| ID | Requirement / User Story | Priority | Estimation | Status |
|---|---|---|---|---|
| FR-XX | [Requirement Title] | High | X SP | Planned / In Progress / Done |
| NFR-XX | [Requirement Title] | High | X SP | Planned / In Progress / Done |

## Definition of Done

The following Definition of Done applies to each sprint backlog item unless otherwise noted.

| Area | Definition of Done Criteria |
|---|---|
| Requirements | Requirement is reviewed and acceptance criteria are documented. |
| Design | Any affected architecture, data model, workflow, or interface design is updated. |
| Development | Code is implemented, committed, and aligned with the existing project structure. |
| Testing | Unit and/or system tests are created or updated for the requirement. |
| Integration | The change is integrated with related components where applicable. |
| Documentation | Relevant documentation, comments, or report sections are updated. |
| Validation | The implementation is validated against acceptance criteria. |

## Acceptance Criteria for Sprint Backlog Items

| Requirement ID | Acceptance Criteria |
|---|---|
| FR-XX | Given [precondition], when [action], then [expected result]. |
| FR-XX | Given [precondition], when [action], then [expected result]. |
| NFR-XX | Given [precondition], when [action], then [expected result]. |

---

# Backlog Grooming

## Backlog Changes This Week

| Change Type | Requirement ID | Description | Rationale | Impact |
|---|---|---|---|---|
| Added / Removed / Updated / Reprioritized | FR-XX | [Describe change] | [Explain reason] | [Architecture, testing, schedule, or scope impact] |

If no changes occurred, use the following statement:

No significant backlog changes occurred during this reporting period. The current sprint backlog remains aligned with the planned sprint goal and MVP delivery strategy.

## Backlog Grooming Rationale

[Provide a short paragraph explaining any backlog changes, reprioritization, estimation changes, scope adjustments, or technical discoveries. Include whether the change impacts architecture, implementation tasks, testing, or sprint delivery.]

---

# Source Code Development

## Summary of Contributions

During this reporting period, development focused on [summarize the main implementation activity]. The work completed this week contributed to [explain how the work supports sprint goals and requirements].

Key contributions include:

- [Contribution 1]
- [Contribution 2]
- [Contribution 3]
- [Contribution 4]

## Repository Information

| Resource | Link |
|---|---|
| Git Repository | [Insert Repository Link] |
| Jira Board | [Insert Jira Board Link] |

## Important Commits

Use direct GitHub commit links so each reported code change can be opened and reviewed from the report.

| Commit | Commit Summary | Related Requirement / User Story | Notes |
|---|---|---|---|
| [`abcdef1`](https://github.com/OWNER/REPOSITORY/commit/FULL_COMMIT_SHA) | [Commit message or summary] | FR-XX / NFR-XX | [Explain relationship to sprint work] |
| [`1234567`](https://github.com/OWNER/REPOSITORY/commit/FULL_COMMIT_SHA) | [Commit message or summary] | FR-XX / NFR-XX | [Explain relationship to sprint work] |

## Burndown Summary

[Summarize remaining sprint work, completed effort, and whether progress is on track.]

| Metric | Value |
|---|---|
| Sprint Total Estimated Effort | X Story Points |
| Completed Effort | X Story Points |
| Remaining Effort | X Story Points |
| Sprint Status | On Track / At Risk / Behind |

## Burndown Chart

Sprint Burndown Chart

---

# Software Testing

## Testing Overview

Testing activities this week focused on defining and/or executing test cases for the requirements included in the sprint backlog. Unit and system testing are prioritized, while user acceptance testing may be documented manually when appropriate.

## Requirement-to-Test Traceability Matrix

| Requirement ID | Test Case ID | Test Type | Test Objective | Status |
|---|---|---|---|---|
| FR-XX | TC-XX-01 | Unit / System / UAT | [Describe test objective] | Planned / Passed / Failed / Blocked |
| FR-XX | TC-XX-02 | Unit / System / UAT | [Describe test objective] | Planned / Passed / Failed / Blocked |
| NFR-XX | TC-XX-03 | Unit / System / UAT | [Describe test objective] | Planned / Passed / Failed / Blocked |

## Test Case Specifications

Each test specification must provide enough detail for another developer to reproduce the test without consulting the implementation. Include exact setup, commands or UI actions, expected results for meaningful steps, cleanup, and evidence.

### TC-XX-01 – [Test Case Name]

| Field | Description |
|---|---|
| Related Requirement | FR-XX / NFR-XX |
| Test Type | Unit / Integration / System / User Acceptance |
| Objective | [Specific behavior or requirement being verified] |
| Preconditions | [Required branch or commit, dependencies, services, configuration, credentials, and starting state] |
| Test Data / Parameters | [Exact fixtures, input files, values, run IDs, environment variables, or request payloads] |
| Execution Environment | [Local or CI environment, operating system, runtime/tool versions, and relevant service versions] |
| Expected Final Result | [Overall expected output, persisted state, response, or observable behavior] |
| Actual Result | [Observed output and relevant measurements, or “Not yet executed”] |
| Evidence | [Direct CI run, test file, log, screenshot, output artifact, or commit link] |
| Cleanup / Reset | [Commands or actions needed to restore the environment, or “None”] |
| Status | Planned / Passed / Failed / Blocked |

#### Execution Steps

1. [Navigate to the repository or required working directory.]
   - Command or action: `[exact command or UI action]`
   - Expected result: [Observable result confirming the step succeeded.]
2. [Prepare the required test data, configuration, or service state.]
   - Command or action: `[exact command, payload, or UI action]`
   - Expected result: [Observable setup result.]
3. [Execute the behavior under test.]
   - Command or action: `[exact command, request, workflow trigger, or UI action]`
   - Expected result: [Observable response or generated artifact.]
4. [Verify the result against the acceptance criteria.]
   - Command or action: `[assertion, query, file inspection, or UI check]`
   - Expected result: [Exact values, status, schema, count, or behavior expected.]
5. [Capture evidence and perform cleanup when applicable.]
   - Command or action: `[evidence and cleanup command or action]`
   - Expected result: [Evidence location and restored environment state.]

#### Step Results

| Step | Actual Result | Status |
|---|---|---|
| 1 | [Observed result] | Passed / Failed / Blocked / Not Run |
| 2 | [Observed result] | Passed / Failed / Blocked / Not Run |
| 3 | [Observed result] | Passed / Failed / Blocked / Not Run |
| 4 | [Observed result] | Passed / Failed / Blocked / Not Run |
| 5 | [Observed result] | Passed / Failed / Blocked / Not Run |

Repeat this complete specification for every test case listed in the requirement-to-test traceability matrix. Do not replace execution steps with a general statement such as “run the tests.”

For automated tests, identify both the narrow test command and the broader regression command when applicable. For workflow or system tests, include service startup, trigger, status verification, output inspection, failure handling, evidence capture, and cleanup.

## Testing Summary

[Summarize the testing progress for this week. Include whether tests were planned, implemented, executed, passed, failed, or blocked. Mention any impact to the sprint plan.]

---

# Risks, Roadblocks, and Mitigation

| Risk / Roadblock | Impact | Mitigation / Next Step |
|---|---|---|
| [Risk or blocker] | [Schedule, architecture, testing, or implementation impact] | [Planned mitigation] |

If no major blockers occurred, use the following statement:

No significant blockers were encountered during this reporting period. Current risks remain manageable within the planned sprint scope.

---

# Plan for Next Week

Next week’s work will focus on [summarize planned work]. Planned activities include:

- [Planned activity 1]
- [Planned activity 2]
- [Planned activity 3]
- [Planned activity 4]

---

# Overall Sprint Assessment

[Provide a concise assessment of sprint health, current progress, remaining work, and confidence in meeting the sprint goal.]

Example:

Sprint progress is currently [on track / at risk / behind]. The completed work supports the sprint goal by [brief explanation]. Remaining work includes [brief explanation]. The primary focus for the next reporting period is [brief explanation].
