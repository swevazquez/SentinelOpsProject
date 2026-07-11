from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
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
        self.css = (DASHBOARD_DIR / "styles.css").read_text(encoding="utf-8")
        self.js = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")
        self.parser = DashboardHtmlParser()
        self.parser.feed(self.html)

    def test_dashboard_assets_are_directly_openable(self):
        self.assertIn("./styles.css", self.parser.links)
        self.assertIn("./app.js", self.parser.scripts)
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
        self.assertIn("Workflow Status", visible_text)
        self.assertIn("Prediction Summary", visible_text)

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
        self.assertIn('showView("overview")', self.js)
        self.assertIn("view.hidden = view.dataset.view !== viewName", self.js)

    def test_dashboard_includes_required_api_response_states(self):
        for state in ("ok", "not_found", "error", "unavailable"):
            with self.subTest(state=state):
                self.assertIn(f'status: "{state}"', self.js)

        for status_code in ("200", "400", "404", "503"):
            with self.subTest(status_code=status_code):
                self.assertRegex(self.js, rf"statusCode:\s*{status_code}")

    def test_dashboard_sample_data_covers_assets_predictions_and_workflows(self):
        self.assertGreaterEqual(len(re.findall(r'asset_id: "', self.js)), 5)
        self.assertIn('asset_id: "PUMP-104"', self.js)
        self.assertIn('asset_id: "MOTOR-207"', self.js)
        self.assertIn("risk_score", self.js)
        self.assertIn("maintenance_priority", self.js)
        self.assertIn("recommended_action", self.js)
        self.assertGreaterEqual(len(re.findall(r'run_id: "', self.js)), 3)
        self.assertIn('status: "completed"', self.js)
        self.assertIn('status: "failed"', self.js)

    def test_workflow_view_supports_manual_execution(self):
        self.assertIn('id="run-workflow-button"', self.html)
        self.assertIn('id="workflow-action-status"', self.html)
        self.assertIn('fetch("/api/workflows"', self.js)
        self.assertIn('workflow: "predictive-maintenance"', self.js)
        self.assertIn("button.disabled = true", self.js)

    def test_dashboard_styles_support_responsive_wireframe_layout(self):
        self.assertIn("summary-grid", self.css)
        self.assertIn("dashboard-layout", self.css)
        self.assertIn(".view-panel", self.css)
        self.assertIn("[hidden]", self.css)
        self.assertIn("@media (max-width: 1100px)", self.css)
        self.assertIn("@media (max-width: 760px)", self.css)
        self.assertIn("overflow-x: auto", self.css)


if __name__ == "__main__":
    unittest.main()
