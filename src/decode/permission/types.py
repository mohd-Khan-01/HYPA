from __future__ import annotations
from enum import StrEnum
class PermissionMode(StrEnum):
    """DEFAULT auto allows read only
       PLAN denies any mutation
       EDIT allows file edit
       BYPASS allows everything"""
    DEFAULT="default"
    PLAN = "plan"
    EDIT = "edit"
    BYPASS = "bypass"
    
class PermissionOutcome(StrEnum):
    ALLOW="allow"
    ASK="ask"
    DENY="deny"
class ToolKind(StrEnum):
    """``READ_ONLY`` = no disk/exec side effect; ``FILE_EDIT`` = mutates the file tree (``write`` /
    ``edit``); ``OTHER`` = everything else (``bash``, and the default for an unclassified tool).
    """
    READ_ONLY = "read_only"
    FILE_EDIT = "file_edit"
    OTHER = "other"