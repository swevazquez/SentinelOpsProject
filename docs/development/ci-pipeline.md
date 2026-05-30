# CI Pipeline

SentinelOps uses GitHub Actions to keep Sprint 1 work demonstrable and traceable. The pipeline intentionally stays lightweight so it can run quickly for every pull request while still validating the current vertical slice.

## Current Checks

The pipeline runs `./scripts/check-ci.sh`, which validates:

- required repository structure,
- no committed generated files under `data/raw/` or `data/processed/`,
- unit tests with `python3 -m unittest discover -s tests`,
- the Sprint 1 telemetry-to-features smoke workflow with `./scripts/seed-data.sh ci-smoke`,
- expected raw telemetry and processed feature output counts,
- Airflow DAG Python syntax,
- and basic Markdown file readability under `docs/`.

Pull requests also run `./scripts/check-jira-traceability.sh` to ensure implementation work references a Jira key such as `SCRUM-1`.

## Rationale

The automated pipeline was pulled forward during Sprint 1 backlog grooming because telemetry generation, raw storage, feature processing, and workflow orchestration depend on repeatable local execution. Establishing CI early reduces integration risk before the project adds APIs, dashboard views, prediction scoring, and agent-assisted workflows.

This supports `NFR-04 Repeatable Local Execution` and provides validation evidence for weekly sprint reports.
