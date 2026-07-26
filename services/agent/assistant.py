from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from openai import OpenAI

from services.agent.actions import ACTION_REGISTRY, action_schemas, prepare_action_request
from services.agent.approvals import ApprovalStore
from services.agent.audit import default_audit_logger
from services.agent.tools import execute_tool, response_tool_schemas


DEFAULT_MODEL = "gpt-5.4-mini"
MAX_TOOL_ROUNDS = 3
SYSTEM_INSTRUCTIONS = """You are the SentinelOps operational assistant for an industrial predictive maintenance dashboard.
Answer questions only about SentinelOps assets, predictions, and workflow execution state.
Use the approved read-only tools to retrieve current facts before making operational claims.
Never invent asset data, prediction values, workflow state, identifiers, or maintenance recommendations.
For remaining-useful-life questions, use an approved RUL prediction tool and report cycles, health, priority, recommendation, model version, and prediction time from stored data.
If a compatible RUL prediction is unavailable, say that clearly and do not substitute a risk score or placeholder estimate.
You may prepare the approved start_workflow action when the user explicitly asks to run predictive maintenance.
Preparing an action never executes it. Explain the impact and require explicit approval before execution.
The application presents approval controls in the conversation. Do not ask the user to reply with approval or include an approval identifier in the answer.
If a request is outside the supported operational scope, state that briefly and list the supported areas.
Keep answers concise and suitable for maintenance managers and reliability engineers.
Return plain text without Markdown syntax. Use short lines when listing operational facts."""


class AssistantModelClient(Protocol):
    def create_response(self, **kwargs: Any) -> Any: ...


class OpenAIResponsesClient:
    def __init__(self, client: OpenAI | None = None) -> None:
        self._client = client or OpenAI()

    def create_response(self, **kwargs: Any) -> Any:
        return self._client.responses.create(**kwargs)


def _prediction_item(prediction: dict[str, Any]) -> dict[str, Any]:
    return {
        key: prediction[key]
        for key in (
            "asset_id",
            "prediction_type",
            "remaining_useful_life_cycles",
            "risk_score",
            "health_score",
            "asset_status",
            "maintenance_priority",
            "recommended_action",
            "model_name",
            "model_version",
            "dataset_id",
            "feature_contract_version",
            "scored_at",
        )
        if key in prediction
    }


def _workflow_item(workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        key: workflow[key]
        for key in ("run_id", "status", "step", "updated_at", "error")
        if key in workflow
    }


def _safe_tool_body(body: dict[str, Any]) -> dict[str, Any]:
    safe_body = {
        key: value
        for key, value in body.items()
        if key != "data"
    }
    data = body.get("data")
    if not isinstance(data, dict):
        return safe_body
    safe_data = dict(data)
    if isinstance(data.get("predictions"), list):
        safe_data["predictions"] = [
            _prediction_item(prediction) for prediction in data["predictions"]
        ]
    if isinstance(data.get("workflows"), list):
        safe_data["workflows"] = [
            _workflow_item(workflow) for workflow in data["workflows"]
        ]
    if isinstance(data.get("workflow"), dict):
        safe_data["workflow"] = _workflow_item(data["workflow"])
    safe_body["data"] = safe_data
    return safe_body


def _result_items(
    tool_name: str,
    safe_body: dict[str, Any],
    message: str,
) -> tuple[str, list[dict[str, Any]]]:
    data = safe_body.get("data", {})
    rul_query = _is_rul_query(message)
    if tool_name in {
        "get_latest_rul_predictions",
        "get_rul_prediction_by_asset",
    }:
        predictions = sorted(
            data.get("predictions", []),
            key=lambda prediction: float(
                prediction.get("remaining_useful_life_cycles", "inf")
            ),
        )
        if not predictions:
            return "rul_unavailable", []
        return (
            "compare_rul" if tool_name == "get_latest_rul_predictions" else "explain_asset_rul",
            predictions[:5] if tool_name == "get_latest_rul_predictions" else predictions[:1],
        )
    if tool_name == "get_latest_predictions":
        predictions = sorted(
            data.get("predictions", []),
            key=lambda prediction: float(prediction.get("risk_score", 0)),
            reverse=True,
        )
        if rul_query:
            rul_predictions = [
                prediction
                for prediction in predictions
                if prediction.get("prediction_type") == "rul"
            ]
            rul_predictions.sort(
                key=lambda prediction: float(
                    prediction["remaining_useful_life_cycles"]
                )
            )
            return (
                ("compare_rul", rul_predictions[:5])
                if rul_predictions
                else ("rul_unavailable", [])
            )
        return "highest_risk_assets", predictions[:5]
    if tool_name == "get_predictions_by_asset":
        predictions = sorted(
            data.get("predictions", []),
            key=lambda prediction: prediction.get("scored_at", ""),
            reverse=True,
        )
        if rul_query:
            rul_predictions = [
                prediction
                for prediction in predictions
                if prediction.get("prediction_type") == "rul"
            ]
            return (
                ("explain_asset_rul", rul_predictions[:1])
                if rul_predictions
                else ("rul_unavailable", [])
            )
        return "explain_asset_prediction", predictions[:1]
    if tool_name == "list_assets":
        return "list_assets", data.get("assets", [])[:5]
    if tool_name in {"list_workflows", "get_workflow"}:
        workflows = data.get("workflows", [])
        if "workflow" in data:
            workflows = [data["workflow"]]
        failures_only = any(word in message.lower() for word in ("fail", "error"))
        if failures_only:
            workflows = [item for item in workflows if item.get("status") == "failed"]
        return (
            "workflow_failures" if failures_only else "workflow_summary",
            workflows[:5],
        )
    if tool_name == "get_predictions_by_run":
        return "run_predictions", data.get("predictions", [])[:5]
    return "operational_query", []


def _is_rul_query(message: str) -> bool:
    normalized = message.lower()
    return "rul" in normalized or "remaining useful life" in normalized


def _function_calls(response: Any) -> list[Any]:
    return [item for item in response.output if item.type == "function_call"]


def answer_operational_query(
    project_root: Path,
    message: str,
    *,
    client: AssistantModelClient | None = None,
    model: str | None = None,
    approval_store: ApprovalStore | None = None,
) -> dict[str, Any]:
    query = message.strip()
    if not query:
        raise ValueError("message must not be empty")

    model_name = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    rul_query = _is_rul_query(query)
    correlation_id = str(uuid4())
    model_client = client or OpenAIResponsesClient()
    approvals = approval_store or ApprovalStore(project_root)
    conversation_input: list[Any] = [{"role": "user", "content": query}]
    response = model_client.create_response(
        model=model_name,
        instructions=SYSTEM_INSTRUCTIONS,
        input=conversation_input,
        tools=response_tool_schemas() + action_schemas(),
        max_tool_calls=MAX_TOOL_ROUNDS,
        parallel_tool_calls=False,
        store=False,
    )
    tool_evidence: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    intent = "operational_query"
    action_request: dict[str, object] | None = None

    tool_rounds = 0
    while True:
        calls = _function_calls(response)
        if not calls:
            break
        if tool_rounds >= MAX_TOOL_ROUNDS:
            raise RuntimeError("assistant exceeded the approved tool-call limit")
        tool_rounds += 1
        conversation_input.extend(
            item.model_dump(exclude_none=True)
            if hasattr(item, "model_dump")
            else item
            for item in response.output
        )
        outputs = []
        for call in calls:
            try:
                arguments = json.loads(call.arguments)
            except json.JSONDecodeError as exc:
                default_audit_logger(project_root).record(
                    correlation_id=correlation_id,
                    operation_type="action" if call.name in ACTION_REGISTRY else "tool",
                    operation_name=call.name,
                    outcome="rejected",
                    duration_ms=0,
                    error_category="validation_error",
                )
                raise ValueError("model returned invalid tool arguments") from exc
            if not isinstance(arguments, dict):
                default_audit_logger(project_root).record(
                    correlation_id=correlation_id,
                    operation_type="action" if call.name in ACTION_REGISTRY else "tool",
                    operation_name=call.name,
                    outcome="rejected",
                    duration_ms=0,
                    error_category="validation_error",
                )
                raise ValueError("model tool arguments must be an object")
            if call.name in ACTION_REGISTRY:
                if action_request is not None:
                    raise ValueError("assistant may prepare only one action per request")
                try:
                    prepared_action = prepare_action_request(
                        action_name=call.name,
                        arguments=arguments,
                    )
                except ValueError:
                    default_audit_logger(project_root).record(
                        correlation_id=correlation_id,
                        operation_type="action",
                        operation_name=call.name,
                        outcome="rejected",
                        duration_ms=0,
                        error_category="validation_error",
                    )
                    raise
                approval = approvals.create(prepared_action)
                action_request = approval.public_dict()
                intent = "action_approval_required"
                default_audit_logger(project_root).record(
                    correlation_id=correlation_id,
                    operation_type="action",
                    operation_name=call.name,
                    outcome="rejected",
                    duration_ms=0,
                    error_category="approval_required",
                )
                tool_evidence.append(
                    {
                        "name": call.name,
                        "read_only": False,
                        "status_code": 202,
                    }
                )
                outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(
                            {
                                "status": "approval_required",
                                "action": action_request,
                            }
                        ),
                    }
                )
                continue
            tool_result = execute_tool(
                project_root=project_root,
                tool_name=call.name,
                arguments=arguments,
                correlation_id=correlation_id,
            )
            safe_body = _safe_tool_body(tool_result["result"])
            tool_evidence.append(
                {
                    "name": tool_result["tool"],
                    "read_only": tool_result["read_only"],
                    "status_code": tool_result["status_code"],
                }
            )
            current_intent, current_items = _result_items(
                call.name,
                safe_body,
                query,
            )
            intent = current_intent
            items = current_items
            outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(safe_body),
                }
            )
        conversation_input.extend(outputs)
        available_tools = response_tool_schemas()
        if action_request is None:
            available_tools += action_schemas()
        response = model_client.create_response(
            model=model_name,
            instructions=SYSTEM_INSTRUCTIONS,
            input=conversation_input,
            tools=available_tools,
            max_tool_calls=MAX_TOOL_ROUNDS,
            parallel_tool_calls=False,
            store=False,
        )
    answer = response.output_text.strip()
    if not answer:
        raise RuntimeError("assistant returned no answer")
    if action_request is not None:
        answer = (
            "I prepared the predictive-maintenance workflow action. "
            "Review the protected operation below before it runs."
        )
    if rul_query and intent == "rul_unavailable":
        answer = (
            "RUL is unavailable. No compatible stored remaining-useful-life "
            "prediction was found, so SentinelOps will not present an estimate."
        )
    elif rul_query and not any(
        evidence["name"]
        in {
            "get_latest_rul_predictions",
            "get_rul_prediction_by_asset",
            "get_latest_predictions",
            "get_predictions_by_asset",
            "get_predictions_by_run",
        }
        for evidence in tool_evidence
    ):
        intent = "rul_unavailable"
        items = []
        answer = (
            "RUL is unavailable because no approved prediction lookup "
            "completed. SentinelOps will not present an unverified estimate."
        )
    return {
        "answer": answer,
        "correlation_id": correlation_id,
        "action_request": action_request,
        "intent": intent,
        "tool_calls": tool_evidence,
        "items": items,
        "provider": "openai",
        "model": model_name,
    }
