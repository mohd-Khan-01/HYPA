from __future__ import annotations

from pydantic_ai import RunContext

from decode.agent.deps import AgentDeps
from decode.permissions.types import PermissionMode


def needs_approval(ctx: RunContext[AgentDeps]) -> bool:
    """Whether a gated tool must defer for approval on this call (ADR-0003 §3; ADR-0019 §1).

    ``True`` — raise :class:`pydantic_ai.ApprovalRequired` — when the call is **not yet approved**
    *and* the gate is **not** in :class:`~decode.permissions.types.PermissionMode.BYPASS`. Under
    ``BYPASS`` (and on an already-approved resume leg) the tool runs inline. This keeps every
    interactive mode's behaviour byte-for-byte (they defer and decode's loop resolves via the
    gate) while letting the headless run — which is BYPASS by construction — execute tools
    directly, with nothing to pause on.
    """
    return not (ctx.tool_call_approved or ctx.deps.gate.mode is PermissionMode.BYPASS)