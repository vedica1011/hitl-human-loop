"""Tools that mutate Memory Bank. Each one is gated by ADK Tool Confirmation
(HITL): ADK pauses the run before invocation, the user confirms via the
`adk web` dialog or a REST FunctionResponse, then the tool executes.
"""
from __future__ import annotations

import os
from typing import Any

import vertexai
from google.adk.tools import ToolContext


# Lazy singleton — the Vertex client is cheap but no need to recreate per call.
_client: vertexai.Client | None = None
_engine_name: str | None = None


def _get_client() -> tuple[vertexai.Client, str]:
    global _client, _engine_name
    if _client is None:
        project = os.environ["GOOGLE_CLOUD_PROJECT"]
        location = os.environ["GOOGLE_CLOUD_LOCATION"]
        engine_id = os.environ["AGENT_ENGINE_ID"]
        _client = vertexai.Client(project=project, location=location)
        _engine_name = (
            f"projects/{project}/locations/{location}/reasoningEngines/{engine_id}"
        )
    assert _engine_name is not None
    return _client, _engine_name


def save_rule_to_memory(rule: str, tool_context: ToolContext) -> dict[str, Any]:
    """Persist a user-defined behavioural rule to Vertex AI Memory Bank.

    The rule is stored verbatim as a `fact` in Memory Bank, scoped to the
    current user_id. On subsequent turns, PreloadMemoryTool will retrieve it
    automatically and inject it into the model context.

    Call this when the user explicitly asks to *remember*, *save a rule*,
    *always do X*, *never do Y*, or sets a personal preference that should
    apply across conversations.

    Args:
        rule: The rule to remember, written first-person in the user's
              voice. Example: "I prefer answers in bullet points, not prose."

    Returns:
        Status dict with the created memory resource name.
    """
    client, engine_name = _get_client()
    user_id = tool_context._invocation_context.session.user_id  # noqa: SLF001

    op = client.agent_engines.memories.create(
        name=engine_name,
        fact=rule,
        scope={"user_id": user_id},
    )

    memory_name = op.response.name if op.response else "unknown"
    return {
        "status": "ok",
        "message": f"Rule saved. It will apply to all future conversations.",
        "memory_resource": memory_name,
        "rule": rule,
    }


def list_rules(tool_context: ToolContext) -> dict[str, Any]:
    """List every rule currently stored for this user in Memory Bank."""
    client, engine_name = _get_client()
    user_id = tool_context._invocation_context.session.user_id  # noqa: SLF001

    memories = list(
        client.agent_engines.memories.retrieve(
            name=engine_name,
            scope={"user_id": user_id},
        )
    )
    rules = [
        {"fact": m.memory.fact, "name": m.memory.name}
        for m in memories
        if m.memory and m.memory.fact
    ]
    return {"status": "ok", "count": len(rules), "rules": rules}


def forget_rule(rule_fragment: str, tool_context: ToolContext) -> dict[str, Any]:
    """Delete rules whose fact contains the given substring.

    HITL-gated — the user will be asked to confirm before deletion.

    Args:
        rule_fragment: Substring to match against stored rule facts.
    """
    client, engine_name = _get_client()
    user_id = tool_context._invocation_context.session.user_id  # noqa: SLF001

    memories = list(
        client.agent_engines.memories.retrieve(
            name=engine_name,
            scope={"user_id": user_id},
        )
    )
    matches = [
        m.memory
        for m in memories
        if m.memory and m.memory.fact and rule_fragment.lower() in m.memory.fact.lower()
    ]
    if not matches:
        return {"status": "noop", "message": f"No rule matched '{rule_fragment}'."}

    deleted = []
    for mem in matches:
        client.agent_engines.memories.delete(name=mem.name)
        deleted.append(mem.fact)
    return {"status": "ok", "deleted_count": len(deleted), "deleted_rules": deleted}