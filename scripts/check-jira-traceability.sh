#!/usr/bin/env bash
set -euo pipefail

JIRA_KEY_PATTERN="${JIRA_KEY_PATTERN:-SCRUM-[0-9]+}"

candidate_text=""

append_value() {
  local label="$1"
  local value="${2:-}"

  if [[ -n "$value" ]]; then
    candidate_text+="${label}: ${value}"$'\n'
  fi
}

append_value "branch" "${GITHUB_HEAD_REF:-${GITHUB_REF_NAME:-}}"
append_value "pull request title" "${PR_TITLE:-}"
append_value "pull request body" "${PR_BODY:-}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  append_value "latest commit" "$(git log -1 --pretty=%B 2>/dev/null || true)"
fi

if printf '%s' "$candidate_text" | grep -Eq "$JIRA_KEY_PATTERN"; then
  printf 'Jira traceability key found.\n'
  exit 0
fi

cat <<EOF
Missing Jira traceability key.

Include a Jira story key such as SCRUM-4 in at least one of:
- branch name, for example SCRUM-4-workflow-orchestration
- pull request title, for example SCRUM-4 Add Sprint 1 workflow DAG
- pull request body
- commit message

Pattern checked: ${JIRA_KEY_PATTERN}
EOF

exit 1
