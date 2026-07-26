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
- Workflows: a repeatable four-checkpoint RUL lifecycle demonstration, scenario
  progress and reset controls, status metrics, execution history, and the latest
  pipeline timeline.
- Assistant: an operational query console for supported asset, prediction, and
  workflow questions, with suggested prompts, structured results, and visible
  approved-tool evidence.

The dashboard reads the configured RUL scenario, latest predictions, and
workflow execution states from the FastAPI service. The default workflow replays
four held-out FD001 engines at 40%, 60%, 80%, and 100% of their lifecycles. It
waits for the selected checkpoint to complete before refreshing the maintenance
view. Reset begins a new session but retains prior workflow and prediction
evidence.

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
