from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


AIRFLOW_API_URL_ENV = "AIRFLOW_API_URL"
AIRFLOW_API_USERNAME_ENV = "AIRFLOW_API_USERNAME"
AIRFLOW_API_PASSWORD_ENV = "AIRFLOW_API_PASSWORD"
AIRFLOW_DAG_ID_ENV = "AIRFLOW_DAG_ID"
AIRFLOW_REQUEST_TIMEOUT_ENV = "AIRFLOW_REQUEST_TIMEOUT_SECONDS"
DEFAULT_AIRFLOW_DAG_ID = "sentinelops_predictive_maintenance"
DEFAULT_AIRFLOW_REQUEST_TIMEOUT_SECONDS = 15.0


class AirflowConfigurationError(RuntimeError):
    """Raised when the Airflow trigger client is not configured."""


class AirflowClientError(RuntimeError):
    """Raised when Airflow rejects or cannot receive a trigger request."""


@dataclass(frozen=True)
class AirflowSettings:
    api_url: str
    username: str
    password: str
    dag_id: str
    timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "AirflowSettings":
        api_url = os.getenv(AIRFLOW_API_URL_ENV, "").strip().rstrip("/")
        username = os.getenv(AIRFLOW_API_USERNAME_ENV, "").strip()
        password = os.getenv(AIRFLOW_API_PASSWORD_ENV, "")
        dag_id = os.getenv(AIRFLOW_DAG_ID_ENV, DEFAULT_AIRFLOW_DAG_ID).strip()
        timeout_value = os.getenv(
            AIRFLOW_REQUEST_TIMEOUT_ENV,
            str(DEFAULT_AIRFLOW_REQUEST_TIMEOUT_SECONDS),
        ).strip()
        if not api_url:
            raise AirflowConfigurationError(
                f"{AIRFLOW_API_URL_ENV} is required for the Airflow workflow backend"
            )
        if not username or not password:
            raise AirflowConfigurationError(
                f"{AIRFLOW_API_USERNAME_ENV} and {AIRFLOW_API_PASSWORD_ENV} "
                "are required for the Airflow workflow backend"
            )
        if not dag_id:
            raise AirflowConfigurationError(
                f"{AIRFLOW_DAG_ID_ENV} must not be empty"
            )
        try:
            timeout_seconds = float(timeout_value)
        except ValueError as exc:
            raise AirflowConfigurationError(
                f"{AIRFLOW_REQUEST_TIMEOUT_ENV} must be a positive number"
            ) from exc
        if timeout_seconds <= 0:
            raise AirflowConfigurationError(
                f"{AIRFLOW_REQUEST_TIMEOUT_ENV} must be a positive number"
            )
        return cls(
            api_url=api_url,
            username=username,
            password=password,
            dag_id=dag_id,
            timeout_seconds=timeout_seconds,
        )


def trigger_dag_run(
    *,
    run_id: str,
    model_version: str,
    settings: AirflowSettings | None = None,
) -> dict[str, object]:
    """Trigger the configured Airflow DAG and return its API response."""
    if not run_id or any(character in run_id for character in ("/", "\\", "..")):
        raise ValueError("run_id must be a non-empty file-safe value")
    configuration = settings or AirflowSettings.from_environment()
    endpoint = (
        f"{configuration.api_url}/dags/"
        f"{quote(configuration.dag_id, safe='')}/dagRuns"
    )
    credentials = base64.b64encode(
        f"{configuration.username}:{configuration.password}".encode("utf-8")
    ).decode("ascii")
    request = Request(
        endpoint,
        data=json.dumps(
            {
                "dag_run_id": run_id,
                "conf": {"model_version": model_version},
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=configuration.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = _response_detail(exc)
        raise AirflowClientError(
            f"Airflow rejected the workflow trigger ({exc.code}): {detail}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise AirflowClientError(
            "Airflow is unavailable; start the Airflow service and try again"
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AirflowClientError(
            "Airflow returned an invalid trigger response"
        ) from exc

    if not isinstance(payload, dict):
        raise AirflowClientError("Airflow returned an invalid trigger response")
    returned_run_id = payload.get("dag_run_id")
    if returned_run_id != run_id:
        raise AirflowClientError(
            "Airflow returned a different run identifier than requested"
        )
    return payload


def _response_detail(error: HTTPError) -> str:
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        return "request failed"
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message")
        if isinstance(detail, str) and detail.strip():
            return " ".join(detail.split())[:300]
    return "request failed"
