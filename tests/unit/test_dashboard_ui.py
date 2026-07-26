from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = PROJECT_ROOT / "frontend" / "dashboard"


class DashboardHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.visible_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if "id" in attributes and attributes["id"]:
            self.ids.add(attributes["id"])
        if tag == "link" and attributes.get("href"):
            self.links.append(attributes["href"] or "")
        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"] or "")

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.visible_text.append(stripped)


class DashboardUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        self.tokens = (DASHBOARD_DIR / "tokens.css").read_text(encoding="utf-8")
        self.css = (DASHBOARD_DIR / "styles.css").read_text(encoding="utf-8")
        self.js = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")
        self.parser = DashboardHtmlParser()
        self.parser.feed(self.html)

    def test_dashboard_assets_are_directly_openable(self):
        self.assertTrue(any(link.startswith("./tokens.css?") for link in self.parser.links))
        self.assertTrue(any(link.startswith("./styles.css?") for link in self.parser.links))
        self.assertTrue(any(script.startswith("./app.js?") for script in self.parser.scripts))
        self.assertTrue((DASHBOARD_DIR / "tokens.css").is_file())
        self.assertTrue((DASHBOARD_DIR / "styles.css").is_file())
        self.assertTrue((DASHBOARD_DIR / "app.js").is_file())

    def test_dashboard_maps_to_scrum_10_acceptance_criteria(self):
        required_sections = {
            "overview",
            "overview-view",
            "assets-view",
            "workflows-view",
            "assistant-view",
            "asset-health",
            "workflow-status",
            "prediction-summary-title",
            "system-states",
        }

        self.assertTrue(required_sections.issubset(self.parser.ids))
        visible_text = " ".join(self.parser.visible_text)
        self.assertIn("Asset Health", visible_text)
        self.assertIn("Workflow Execution", visible_text)
        self.assertIn("Prediction Distribution", visible_text)

    def test_dashboard_opens_to_overview_only(self):
        self.assertIn('data-view="overview"', self.html)
        self.assertIn('data-view="assets" hidden', self.html)
        self.assertIn('data-view="workflows" hidden', self.html)
        self.assertIn('data-view="assistant" hidden', self.html)
        self.assertIn('data-view-target="overview" aria-current="page"', self.html)

    def test_dashboard_navigation_switches_between_views(self):
        for view_name in ("overview", "assets", "workflows", "assistant"):
            with self.subTest(view_name=view_name):
                self.assertIn(f'data-view-target="{view_name}"', self.html)

        self.assertIn("function showView(viewName)", self.js)
        self.assertIn('get("view")', self.js)
        self.assertIn('requestedView : "overview"', self.js)
        self.assertIn("view.hidden = view.dataset.view !== viewName", self.js)

    def test_dashboard_loads_operational_data_from_api(self):
        self.assertIn('apiFetch("/api/assets")', self.js)
        self.assertIn('apiFetch("/api/predictions/latest")', self.js)
        self.assertIn('apiFetch("/api/workflows")', self.js)
        self.assertNotIn('asset_id: "PUMP-104"', self.js)
        self.assertNotIn('run_id: "sprint1-0942"', self.js)

    def test_workflow_view_supports_manual_execution(self):
        self.assertIn('id="run-workflow-button"', self.html)
        self.assertIn('id="workflow-action-status"', self.html)
        self.assertIn('fetch("/api/workflows"', self.js)
        self.assertIn('workflow: "predictive-maintenance"', self.js)
        self.assertIn("button.disabled = true", self.js)
        self.assertIn("Predictive maintenance", self.js)
        self.assertIn('id="workflow-detail-dialog"', self.html)
        self.assertIn("function openWorkflowDetails(runId)", self.js)
        self.assertIn("Run identifier", self.js)

    def test_workflow_history_supports_status_filters(self):
        self.assertIn('data-workflow-filter="${state}"', self.js)
        self.assertIn('id="workflow-filter-clear"', self.html)
        self.assertIn('workflow.status === workflowFilter', self.js)

    def test_header_controls_provide_actionable_feedback(self):
        self.assertIn('id="notification-popover"', self.html)
        self.assertIn('data-notification-type="${alert.targetType}"', self.js)
        self.assertIn('id="user-popover"', self.html)
        self.assertIn('refreshLabel.textContent = "Refreshing"', self.js)
        self.assertNotIn('id="header-alert-count"', self.html)

    def test_detail_drill_down_preserves_the_current_view(self):
        self.assertIn('class="interactive-table-row"', self.js)
        self.assertIn('tabindex="0" role="button"', self.js)
        self.assertIn('event.target.matches(".interactive-table-row")', self.js)
        notification_handler = self.js.split('const notificationControl = event.target.closest("[data-notification-type]");', 1)[1]
        notification_handler = notification_handler.split("const accountControl", 1)[0]
        self.assertNotIn("showView(", notification_handler)

    def test_assistant_submits_supported_operational_queries(self):
        self.assertIn('id="assistant-form"', self.html)
        self.assertIn('id="assistant-input"', self.html)
        self.assertIn(
            'data-assistant-prompt="Show assets with the shortest RUL"',
            self.html,
        )
        self.assertIn('fetch("/api/assistant/query"', self.js)
        self.assertIn("payload.data.response.answer", self.js)
        self.assertIn('id="assistant-model-name"', self.html)
        self.assertIn("payload.data.response.model", self.js)
        self.assertIn("tool_calls", self.js)
        self.assertIn("#assistant-view", self.css)
        self.assertIn("height: calc(100vh - var(--topbar-height)", self.css)
        self.assertIn(".assistant-transcript", self.css)
        self.assertIn("overscroll-behavior: contain", self.css)
        self.assertIn("grid-template-rows: auto minmax(0, 1fr) auto", self.css)
        self.assertIn('class="panel context-panel context-disclosure" open', self.html)
        self.assertIn(".context-disclosure[open]", self.css)
        self.assertIn(".workflow-feedback", self.css)
        self.assertIn("padding: var(--space-3) var(--space-4)", self.css)

    def test_assistant_requires_explicit_approval_for_operational_actions(self):
        self.assertIn('data-assistant-prompt="Run predictive maintenance"', self.html)
        self.assertNotIn('id="assistant-approval-dialog"', self.html)
        self.assertIn('data-approval-card="${escapeHtml(action.approval_id)}"', self.js)
        self.assertIn('data-assistant-decision="approved"', self.js)
        self.assertIn('data-assistant-decision="denied"', self.js)
        self.assertIn('fetch(`/api/assistant/approvals/${encodeURIComponent', self.js)
        self.assertIn('fetch("/api/assistant/actions/execute"', self.js)
        self.assertIn("action.fingerprint", self.js)
        self.assertIn("function decideAssistantAction(decision, approvalId)", self.js)
        self.assertIn(".assistant-action-card", self.css)
        self.assertIn(".assistant-action-controls", self.css)

    def test_assistant_links_completed_actions_to_workflow_details(self):
        self.assertIn("function assistantWorkflowLink(response)", self.js)
        self.assertIn('data-workflow-link="${runId}"', self.js)
        self.assertIn("View completed workflow", self.js)
        self.assertIn('href="?view=assistant"', self.js)
        self.assertIn("openWorkflowDetails(workflowLink.dataset.workflowLink)", self.js)
        self.assertNotIn('get("run")', self.js)
        self.assertIn(".assistant-workflow-link", self.css)

    def test_dashboard_has_enterprise_design_system_and_in_scope_navigation(self):
        for token in (
            "--color-bg-canvas",
            "--color-healthy",
            "--color-warning",
            "--color-critical",
            "--space-4",
            "--radius-lg",
        ):
            self.assertIn(token, self.tokens)

        self.assertIn("lucide", self.html)
        self.assertIn('data-lucide="layout-dashboard"', self.html)
        for view_name in ("overview", "assets", "workflows", "assistant"):
            self.assertIn(f'data-view-target="{view_name}"', self.html)
        for out_of_scope_view in ("predictions", "analytics", "settings"):
            self.assertNotIn(f'data-view="{out_of_scope_view}"', self.html)

    def test_assets_support_search_sort_and_details(self):
        self.assertIn('id="asset-search"', self.html)
        self.assertIn('id="asset-sort"', self.html)
        self.assertIn('id="asset-detail-dialog"', self.html)
        self.assertIn("function openAssetDetails(assetId)", self.js)
        self.assertIn("model_confidence", self.js)

    def test_dashboard_exposes_rul_without_confusing_it_with_risk(self):
        self.assertIn("<th>Risk Score</th><th>RUL</th>", self.html)
        self.assertIn('value="rul-asc">RUL: shortest horizon', self.html)
        self.assertIn("function formatRul(value)", self.js)
        self.assertIn('optionalApiFetch("/api/predictions/rul/latest")', self.js)
        self.assertIn("prediction?.prediction_type === \"rul\"", self.js)
        self.assertIn("remaining_useful_life_cycles", self.js)
        self.assertIn("asset.rul_available", self.js)
        self.assertIn("RUL is unavailable because no compatible stored", self.js)
        self.assertIn("not a guaranteed failure date", self.js)
        self.assertIn('class="rul-chip', self.js)
        self.assertIn(".rul-chip.rul-unavailable", self.css)
        self.assertIn(
            'data-assistant-prompt="What is the RUL for FD001-ENGINE-002?"',
            self.html,
        )
        self.assertIn('"compare_rul", "explain_asset_rul"', self.js)

    def test_dashboard_styles_support_responsive_wireframe_layout(self):
        self.assertIn("kpi-grid", self.css)
        self.assertIn("app-shell", self.css)
        self.assertIn(".view-panel", self.css)
        self.assertIn("[hidden]", self.css)
        self.assertIn("@media (max-width: 1400px)", self.css)
        self.assertIn("@media (max-width: 1100px)", self.css)
        self.assertIn("@media (max-width: 820px)", self.css)
        self.assertIn("overflow-x: auto", self.css)
        self.assertIn(".donut-chart", self.css)


if __name__ == "__main__":
    unittest.main()
