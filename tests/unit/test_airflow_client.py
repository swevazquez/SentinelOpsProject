from __future__ import annotations

import base64
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from services.api.airflow_client import (
    AirflowClientError,
    AirflowSettings,
    trigger_dag_run,
)


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class AirflowClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = AirflowSettings(
            api_url="http://airflow:8080/api/v1",
            username="airflow",
            password="secret",
            dag_id="sentinelops_predictive_maintenance",
            timeout_seconds=4,
        )

    @patch("services.api.airflow_client.urlopen")
    def test_trigger_posts_run_identifier_and_model_configuration(self, urlopen) -> None:
        urlopen.return_value = _Response({"dag_run_id": "demo-run"})

        response = trigger_dag_run(
            run_id="demo-run",
            model_version="1.0.0",
            settings=self.settings,
        )

        self.assertEqual(response["dag_run_id"], "demo-run")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "http://airflow:8080/api/v1/dags/"
            "sentinelops_predictive_maintenance/dagRuns",
        )
        self.assertEqual(
            request.get_header("Authorization"),
            "Basic " + base64.b64encode(b"airflow:secret").decode("ascii"),
        )
        self.assertEqual(
            json.loads(request.data.decode("utf-8")),
            {
                "dag_run_id": "demo-run",
                "conf": {"model_version": "1.0.0"},
            },
        )

    @patch("services.api.airflow_client.urlopen")
    def test_trigger_does_not_expose_credentials_when_airflow_rejects_request(
        self,
        urlopen,
    ) -> None:
        urlopen.side_effect = HTTPError(
            url="http://airflow:8080/api/v1/dags/dag/dagRuns",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )

        with self.assertRaises(AirflowClientError) as raised:
            trigger_dag_run(
                run_id="demo-run",
                model_version="1.0.0",
                settings=self.settings,
            )

        self.assertNotIn("secret", str(raised.exception))
        self.assertIn("401", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
