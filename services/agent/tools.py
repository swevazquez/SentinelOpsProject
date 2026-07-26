from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from services.agent.audit import AgentAuditLogger, default_audit_logger
from services.api.operations import (
    ApiResponse,
    latest_predictions_response,
    latest_rul_predictions_response,
    list_assets_response,
    predictions_by_asset_response,
    predictions_by_run_response,
    rul_prediction_by_asset_response,
    workflow_list_response,
    workflow_status_response,
)


ToolHandler = Callable[[Path, dict[str, str]], ApiResponse]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    read_only: bool = True


def _no_arguments(handler: Callable[[Path], ApiResponse]) -> ToolHandler:
    def wrapped(project_root: Path, arguments: dict[str, str]) -> ApiResponse:
        if arguments:
            raise ValueError("tool does not accept arguments")
        return handler(project_root)

    return wrapped


def _required_argument(
    name: str,
    handler: Callable[[Path, str], ApiResponse],
) -> ToolHandler:
    def wrapped(project_root: Path, arguments: dict[str, str]) -> ApiResponse:
        if set(arguments) != {name}:
            raise ValueError(f"tool requires exactly one argument: {name}")
        value = arguments[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return handler(project_root, value)

    return wrapped


def _object_schema(properties: dict[str, dict[str, str]]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


APPROVED_TOOLS = (
    ToolDefinition(
        name="list_assets",
        description="List configured SentinelOps assets.",
        input_schema=_object_schema({}),
        handler=_no_arguments(list_assets_response),
    ),
    ToolDefinition(
        name="list_workflows",
        description="List recent workflow execution states.",
        input_schema=_object_schema({}),
        handler=_no_arguments(workflow_list_response),
    ),
    ToolDefinition(
        name="get_latest_predictions",
        description="Retrieve the latest prediction for each scored asset.",
        input_schema=_object_schema({}),
        handler=_no_arguments(latest_predictions_response),
    ),
    ToolDefinition(
        name="get_latest_rul_predictions",
        description=(
            "Retrieve the latest compatible remaining-useful-life prediction "
            "for each RUL-scored asset."
        ),
        input_schema=_object_schema({}),
        handler=_no_arguments(latest_rul_predictions_response),
    ),
    ToolDefinition(
        name="get_workflow",
        description="Retrieve one workflow execution by run identifier.",
        input_schema=_object_schema({"run_id": {"type": "string"}}),
        handler=_required_argument("run_id", workflow_status_response),
    ),
    ToolDefinition(
        name="get_predictions_by_run",
        description="Retrieve predictions produced by one workflow run.",
        input_schema=_object_schema({"run_id": {"type": "string"}}),
        handler=_required_argument("run_id", predictions_by_run_response),
    ),
    ToolDefinition(
        name="get_predictions_by_asset",
        description="Retrieve prediction history for one asset.",
        input_schema=_object_schema({"asset_id": {"type": "string"}}),
        handler=_required_argument("asset_id", predictions_by_asset_response),
    ),
    ToolDefinition(
        name="get_rul_prediction_by_asset",
        description=(
            "Retrieve compatible remaining-useful-life prediction history "
            "for one asset."
        ),
        input_schema=_object_schema({"asset_id": {"type": "string"}}),
        handler=_required_argument("asset_id", rul_prediction_by_asset_response),
    ),
)

TOOL_REGISTRY = {tool.name: tool for tool in APPROVED_TOOLS}


def tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }
        for tool in APPROVED_TOOLS
    ]


def response_tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
            "strict": True,
        }
        for tool in APPROVED_TOOLS
    ]


def execute_tool(
    *,
    project_root: Path,
    tool_name: str,
    arguments: dict[str, str],
    correlation_id: str | None = None,
    audit_logger: AgentAuditLogger | None = None,
) -> dict[str, Any]:
    started_at = perf_counter()
    request_id = correlation_id or str(uuid4())
    logger = audit_logger or default_audit_logger(project_root)
    outcome = "failed"
    error_category: str | None = None
    try:
        tool = TOOL_REGISTRY.get(tool_name)
        if tool is None:
            raise ValueError(f"tool is not approved: {tool_name}")
        response = tool.handler(project_root, arguments)
        if 200 <= response.status_code < 300:
            outcome = "succeeded"
        elif response.status_code == 404:
            outcome = "not_found"
        else:
            outcome = "rejected"
            error_category = f"http_{response.status_code}"
        return {
            "tool": tool.name,
            "read_only": tool.read_only,
            "status_code": response.status_code,
            "result": response.body,
        }
    except (TypeError, ValueError):
        outcome = "rejected"
        error_category = "validation_error"
        raise
    except Exception:
        error_category = "execution_error"
        raise
    finally:
        logger.record(
            correlation_id=request_id,
            operation_type="tool",
            operation_name=tool_name if isinstance(tool_name, str) else "invalid_operation_name",
            outcome=outcome,
            duration_ms=(perf_counter() - started_at) * 1000,
            error_category=error_category,
        )
