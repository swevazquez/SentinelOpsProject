from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.operations import predictions_by_run_response
from services.ml.prediction_store import (
    CsvPredictionRepository,
    PostgresPredictionRepository,
    prediction_repository,
)
from services.persistence.config import PersistenceConfigurationError
from services.workflows.status import (
    JsonWorkflowStatusRepository,
    PostgresWorkflowStatusRepository,
    workflow_status_repository,
)


class PersistenceConfigurationTests(unittest.TestCase):
    def test_file_backend_is_default_for_both_repository_types(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(os.environ, {}, clear=True):
            project_root = Path(temp_dir)

            predictions = prediction_repository(project_root)
            workflows = workflow_status_repository(project_root)

        self.assertIsInstance(predictions, CsvPredictionRepository)
        self.assertIsInstance(workflows, JsonWorkflowStatusRepository)

    def test_postgres_backend_configures_both_repository_types(self) -> None:
        environment = {
            "SENTINELOPS_PERSISTENCE_BACKEND": "postgres",
            "DATABASE_URL": "postgresql://example.invalid/sentinelops",
        }
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, environment, clear=True
        ):
            project_root = Path(temp_dir)

            predictions = prediction_repository(project_root)
            workflows = workflow_status_repository(project_root)

        self.assertIsInstance(predictions, PostgresPredictionRepository)
        self.assertIsInstance(workflows, PostgresWorkflowStatusRepository)

    def test_postgres_backend_requires_database_url(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SENTINELOPS_PERSISTENCE_BACKEND": "postgres"},
            clear=True,
        ):
            with self.assertRaisesRegex(
                PersistenceConfigurationError,
                "DATABASE_URL is required",
            ):
                prediction_repository(Path(temp_dir))

    def test_unavailable_postgres_returns_explicit_service_state(self) -> None:
        environment = {
            "SENTINELOPS_PERSISTENCE_BACKEND": "postgres",
            "DATABASE_URL": "postgresql://unavailable.invalid/sentinelops",
        }
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, environment, clear=True
        ), patch(
            "services.persistence.postgres.psycopg.connect",
            side_effect=psycopg.OperationalError("database unavailable"),
        ):
            response = predictions_by_run_response(Path(temp_dir), "run-1")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body["request_state"], "unavailable")
        self.assertIn("operation was not committed", response.body["message"])

    def test_workflow_is_not_accepted_when_postgres_is_unavailable(self) -> None:
        environment = {
            "SENTINELOPS_PERSISTENCE_BACKEND": "postgres",
            "DATABASE_URL": "postgresql://unavailable.invalid/sentinelops",
        }
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, environment, clear=True
        ), patch(
            "services.persistence.postgres.psycopg.connect",
            side_effect=psycopg.OperationalError("database unavailable"),
        ):
            project_root = Path(temp_dir)
            with TestClient(create_app(project_root)) as client:
                response = client.post(
                    "/api/workflows",
                    json={
                        "workflow": "predictive-maintenance",
                        "inference_mode": "baseline",
                    },
                )

        self.assertEqual(response.status_code, 503)
        self.assertIn("operation was not committed", response.json()["detail"])
        self.assertFalse((project_root / "data" / "workflow-status").exists())


if __name__ == "__main__":
    unittest.main()
