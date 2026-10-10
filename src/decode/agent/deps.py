from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path

from decode.entities.events import Event
from decode.permission.types import PermissionOutcome


PermissionDecision = PermissionOutcome
EventSink = Callable[[Event], None]
PermissionGateCallback = Callable[[str], PermissionDecision]
PermissionResolver = Callable[[str], Awaitable[bool]]
UserQuestionResolver = Callable[[str], Awaitable[str]]


@dataclass(slots=True)
class AgentDeps:
    cwd: Path
    emit: EventSink
    gate: PermissionGateCallback
    resolve_permission: PermissionResolver
    resolve_user_question: UserQuestionResolver
    task_store: list = field(default_factory=list)