# Dashboard

Frontend dashboard for asset health, predictions, pipeline monitoring, and agent interaction.

## Sprint 2 Operations Dashboard

`SCRUM-10` implements the first dashboard slice as directly openable static
assets:

- `index.html`
- `styles.css`
- `app.js`

The page follows the reviewed operations overview wireframe in
`docs/diagrams/ui/dashboard-wireframe.mmd` and displays the Sprint 2 acceptance
criteria for FR-10:

- asset health and maintenance priority,
- prediction summaries and recommendations,
- workflow execution status,
- manual predictive-maintenance workflow execution,
- and clear normal, missing, invalid, and unavailable response-state mappings.

The dashboard reads asset profiles, latest predictions, and workflow execution
states from the FastAPI service. When no prediction run exists yet, it displays
the configured asset profiles and labels them as baseline data until a workflow
is run.

Start the API from the repository root and open `http://127.0.0.1:8000` to review
the integrated dashboard.
