"""HITL chat assistant with Vertex AI Memory Bank rule persistence.

Run with:
    adk web agent --memory_service_uri="agentengine://${AGENT_ENGINE_ID}"
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import FunctionTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from .memory_tools import forget_rule, list_rules, save_rule_to_memory


from .telemetry import setup_langfuse
setup_langfuse()    

load_dotenv()
#os.environ['DEEPSEEK_API_KEY'] = "sk************************"
#MODEL = "deepseek/deepseek-v4-pro"

MODEL = "gemini-3.1-flash-lite"


# ---------------------------------------------------------------------------
# After-agent callback: snapshot the conversation into Memory Bank so the
# LLM-extraction path also captures implicit preferences alongside the
# explicit rules we store via save_rule_to_memory.
# ---------------------------------------------------------------------------
async def _persist_session_to_memory(callback_context: CallbackContext):
    ctx = callback_context._invocation_context  # noqa: SLF001
    if ctx.memory_service is not None:
        await ctx.memory_service.add_session_to_memory(ctx.session)


# ---------------------------------------------------------------------------
# Sub-agent: handles all rule mutations. Tools here are HITL-gated.
# ---------------------------------------------------------------------------
rule_manager_agent = LlmAgent(
    model=MODEL,
    name="rule_manager_agent",
    description=(
        "Manages persistent behavioural rules for the user. Delegate to this "
        "agent whenever the user asks to remember, save, update, list, or "
        "forget a rule or preference."
    ),
    instruction=(
        "You manage the user's long-term behavioural rules stored in Vertex "
        "AI Memory Bank.\n\n"
        "Workflow:\n"
        "1. If the user wants to save a rule, rewrite it as a clear, "
        "first-person statement (e.g. 'I prefer concise answers with code "
        "blocks.') and call `save_rule_to_memory`. The system will ask the "
        "user to confirm before persisting — that is intentional, do NOT "
        "try to bypass it.\n"
        "2. If the user wants to see their rules, call `list_rules`.\n"
        "3. If the user wants to remove a rule, call `forget_rule` with a "
        "distinctive substring. Confirmation will be requested.\n"
        "4. After the tool returns, summarise the outcome in one short "
        "sentence and hand control back to the root agent.\n\n"
        "Never invent rules the user did not ask for."
    ),
    tools=[
        # Boolean HITL — ADK pauses and asks the user to confirm before
        # the function body executes. Resumes only on confirmed=true.
        FunctionTool(save_rule_to_memory, require_confirmation=True),
        FunctionTool(forget_rule, require_confirmation=True),
        # Read-only — no confirmation needed.
        FunctionTool(list_rules),
    ],
)


# ---------------------------------------------------------------------------
# Root: general-purpose chat assistant. PreloadMemoryTool auto-fetches
# Memory Bank facts at the start of every turn, so any saved rule is in
# context before the model generates a response.
# ---------------------------------------------------------------------------
root_agent = LlmAgent(
    model=MODEL,
    name="hitl_memory_assistant",
    description="General-purpose chat assistant with persistent user rules.",
    instruction=(
        "You are a helpful, concise chat assistant.\n\n"
        "## Memory rules (HIGH PRIORITY)\n"
        "Before every turn, the system injects any rules the user has "
        "previously saved to Memory Bank. These appear in your context as "
        "memories. ALWAYS obey them. If a rule conflicts with what the user "
        "is asking right now, follow the rule and briefly note it.\n\n"
        "## Delegation\n"
        "If the user asks to remember, save, list, update, or forget a "
        "rule or preference, delegate to `rule_manager_agent`. Do not try "
        "to handle memory mutations yourself.\n\n"
        "## Style\n"
        "Default to short, direct answers unless a saved rule says otherwise."
    ),
    sub_agents=[rule_manager_agent],
    tools=[
        # Always pulls user-scoped Memory Bank facts and prepends them to
        # the LLM prompt at every turn.
        PreloadMemoryTool(),
    ],
    after_agent_callback=_persist_session_to_memory,
)