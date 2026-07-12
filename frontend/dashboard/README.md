# Dashboard

Frontend dashboard for asset health, predictions, pipeline monitoring, and agent interaction.

## Operations Dashboard

The dashboard is a desktop-first industrial operations console built as directly
served static assets:

- `index.html`
- `tokens.css`
- `styles.css`
- `app.js`

The current experiment modernizes the reviewed operations wireframe with a dark
enterprise theme, reusable design tokens, live API data, and four in-scope views:

- Overview: fleet KPIs, health and prediction charts, workflow status, alerts,
  and highest-risk assets.
- Assets: search, filtering, sorting, richer prediction fields, and an asset
  detail dialog.
- Workflows: manual predictive-maintenance execution, status metrics, execution
  history, and the latest pipeline timeline.
- Assistant: a controlled enterprise preview that documents current context,
  approved tools, and the pending FR-12 integration without simulating responses.

The dashboard reads asset profiles, latest predictions, and workflow execution
states from the FastAPI service. When no prediction run exists yet, it displays
the configured asset profiles and labels them as baseline data until a workflow
is run.

## Design System

`tokens.css` defines the SentinelOps color, typography, spacing, radius, shadow,
and layout tokens. `styles.css` composes those tokens into reusable buttons,
badges, KPI cards, panels, charts, tables, workflow timelines, empty states,
dialogs, and toast notifications. Navigation and interface controls use Lucide
icons while preserving text labels and accessible names.

See `DESIGN_SYSTEM.md` for the component and data-visualization conventions used
by the dashboard.

Start the API from the repository root and open `http://127.0.0.1:8000` to review
the integrated dashboard.
