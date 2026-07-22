from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping


SUPPORTED_WORKFLOW = "predictive-maintenance"


ActionValidator = Callable[[dict[str, Any]], dict[str, str]]


@dataclass(frozen=True)
class ActionDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    validator: ActionValidator


@dataclass(frozen=True)
class ActionRequest:
    name: str
    arguments: Mapping[str, str]
    fingerprint: str
    requires_approval: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "arguments": dict(self.arguments),
            "fingerprint": self.fingerprint,
            "requires_approval": self.requires_approval,
        }


def _object_schema(properties: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _validate_workflow(arguments: dict[str, Any]) -> dict[str, str]:
    if set(arguments) != {"workflow"}:
        raise ValueError("action requires exactly one argument: workflow")
    workflow = arguments["workflow"]
    if not isinstance(workflow, str) or workflow != SUPPORTED_WORKFLOW:
        raise ValueError(f"unsupported workflow action: {workflow}")
    return {"workflow": workflow}


APPROVED_ACTIONS = (
    ActionDefinition(
        name="start_workflow",
        description="Request execution of the supported predictive-maintenance workflow.",
        input_schema=_object_schema(
            {
                "workflow": {
                    "type": "string",
                    "enum": [SUPPORTED_WORKFLOW],
                }
            }
        ),
        validator=_validate_workflow,
    ),
)

ACTION_REGISTRY = {action.name: action for action in APPROVED_ACTIONS}


def action_schemas() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": action.name,
            "description": action.description,
            "parameters": action.input_schema,
            "strict": True,
        }
        for action in APPROVED_ACTIONS
    ]


def prepare_action_request(
    *,
    action_name: str,
    arguments: dict[str, Any],
) -> ActionRequest:
    if not isinstance(action_name, str):
        raise ValueError("action name must be a string")
    action = ACTION_REGISTRY.get(action_name)
    if action is None:
        raise ValueError(f"action is not approved: {action_name}")
    if not isinstance(arguments, dict):
        raise ValueError("action arguments must be an object")
    validated_arguments = action.validator(arguments)
    canonical_request = json.dumps(
        {"name": action.name, "arguments": validated_arguments},
        sort_keys=True,
        separators=(",", ":"),
    )
    fingerprint = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    return ActionRequest(
        name=action.name,
        arguments=MappingProxyType(validated_arguments),
        fingerprint=fingerprint,
    )
