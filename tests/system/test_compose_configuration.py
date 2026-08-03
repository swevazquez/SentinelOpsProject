from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ComposeConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.api_dockerfile = (PROJECT_ROOT / "docker" / "api.Dockerfile").read_text(
            encoding="utf-8"
        )
        self.deployment_doc = (
            PROJECT_ROOT / "docs" / "development" / "docker-compose-deployment.md"
        ).read_text(encoding="utf-8")

    def test_api_is_a_real_fastapi_service_with_readiness_healthcheck(self) -> None:
        self.assertIn('"uvicorn", "services.api.app:app"', self.api_dockerfile)
        self.assertNotIn("python -m http.server", self.api_dockerfile)
        self.assertIn("http://localhost:8000/api/health", self.compose)
        self.assertIn("condition: service_healthy", self.compose)

    def test_supported_deployment_path_documents_lifecycle_and_persistence(self) -> None:
        for required_text in (
            "docker compose up --build --wait",
            "curl --fail http://127.0.0.1:8000/api/health",
            "docker compose down",
            "docker compose down --volumes",
            "clean-checkout",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.deployment_doc)


if __name__ == "__main__":
    unittest.main()
