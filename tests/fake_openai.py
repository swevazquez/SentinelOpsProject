from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any


class FakeAssistantClient:
    def __init__(
        self,
        *,
        tool_name: str | None,
        arguments: dict[str, str] | None = None,
        answer: str,
    ) -> None:
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.answer = answer
        self.requests: list[dict[str, Any]] = []

    def create_response(self, **kwargs: Any) -> Any:
        self.requests.append(kwargs)
        if self.tool_name is not None and len(self.requests) == 1:
            call = SimpleNamespace(
                type="function_call",
                name=self.tool_name,
                arguments=json.dumps(self.arguments),
                call_id="call-1",
            )
            return SimpleNamespace(id="response-1", output=[call], output_text="")
        return SimpleNamespace(
            id=f"response-{len(self.requests)}",
            output=[],
            output_text=self.answer,
        )
