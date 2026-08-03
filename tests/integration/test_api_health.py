from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app


class ApiHealthTests(unittest.TestCase):
    def test_health_endpoint_returns_non_secret_readiness_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            client = TestClient(create_app(Path(temporary_directory)))

            response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"], {"service": "sentinelops-api", "healthy": True})
        self.assertNotIn("password", response.text.lower())
        self.assertNotIn("api_key", response.text.lower())


if __name__ == "__main__":
    unittest.main()
