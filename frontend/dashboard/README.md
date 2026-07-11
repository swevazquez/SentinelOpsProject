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

The dashboard currently uses in-page sample data shaped like the Sprint 2 API
responses. This keeps the UI demonstrable before FastAPI route wiring is added
and avoids requiring a local development server for review.

Open `frontend/dashboard/index.html` in a browser to review the page.
