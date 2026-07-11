from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from services.api.operations import (
    ApiResponse,
    list_assets_response,
    predictions_by_asset_response,
    predictions_by_run_response,
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


def execute_tool(
    *,
    project_root: Path,
    tool_name: str,
    arguments: dict[str, str],
) -> dict[str, Any]:
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        raise ValueError(f"tool is not approved: {tool_name}")
    response = tool.handler(project_root, arguments)
    return {
        "tool": tool.name,
        "read_only": tool.read_only,
        "status_code": response.status_code,
        "result": response.body,
    }
