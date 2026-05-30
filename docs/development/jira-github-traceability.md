# Jira and GitHub Traceability

SentinelOps uses Jira as the backlog source and GitHub as the code source. Each meaningful code change should be traceable to a Jira story so sprint reports can connect planned user stories, implementation commits, tests, and documentation updates.

## Current Systems

| System | Purpose | Link |
|---|---|---|
| Jira project | User stories, sprint planning, status tracking, and backlog refinement | <https://psu-capstone-sentinelops.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog> |
| GitHub repository | Source control, pull requests, code review, and CI checks | <https://github.com/swevazquez/SentinelOpsProject> |

The Jira project key is `SCRUM`. Jira stories use keys such as `SCRUM-1`, `SCRUM-4`, and `SCRUM-19`.

## Working Agreement

Use one Jira story as the primary traceability anchor for each implementation branch or pull request.

1. Start from a Jira story assigned to the current sprint.
2. Create a branch that includes the Jira key.
3. Include the same Jira key in the pull request title or body.
4. Reference the Jira key in meaningful commits when practical.
5. Update the Jira story status as the code moves from implementation to validation.

Example:

```text
Branch: SCRUM-4-workflow-orchestration
PR title: SCRUM-4 Add Sprint 1 workflow orchestration
Commit: SCRUM-4 Add Airflow DAG for telemetry feature workflow
```

## GitHub Autolink

Configure a GitHub autolink so Jira keys in commits, pull requests, and branch names link directly to Jira.

Recommended repository autolink:

```text
Reference prefix: SCRUM-
Target URL: https://psu-capstone-sentinelops.atlassian.net/browse/SCRUM-<num>
```

This setting is configured in GitHub under repository settings, or through the GitHub API by an authenticated maintainer.

```bash
gh api \
  --method POST \
  /repos/swevazquez/SentinelOpsProject/autolinks \
  -f key_prefix='SCRUM-' \
  -f url_template='https://psu-capstone-sentinelops.atlassian.net/browse/SCRUM-<num>' \
  -F is_alphanumeric=false
```

## Pull Request Traceability Check

The repository includes a CI check that verifies pull requests contain a Jira key matching `SCRUM-[0-9]+` in at least one of:

- branch name,
- pull request title,
- pull request body,
- or latest commit message.

Run the check locally with:

```bash
./scripts/check-jira-traceability.sh
```

For documentation-only work that is not tied to a sprint story, include the closest Jira key in the pull request body and briefly explain the documentation relationship.

## Sprint Reporting Use

Weekly reports should use Jira for planned scope and sprint status, then use GitHub commits and pull requests containing Jira keys as implementation evidence. This keeps reports grounded in both backlog intent and code activity.
