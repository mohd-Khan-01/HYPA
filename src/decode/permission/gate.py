from decode.permission.types import (
    PermissionMode,
    PermissionOutcome,
    ToolKind,
)


class PermissionGate:
    def __init__(
        self,
        mode: PermissionMode = PermissionMode.DEFAULT,
    ) -> None:
        self.mode = mode

    def __call__(self, tool_name: str) -> PermissionOutcome:
        kinds = {
            "read": ToolKind.READ_ONLY,
            "glob": ToolKind.READ_ONLY,
            "grep": ToolKind.READ_ONLY,
            "write": ToolKind.FILE_EDIT,
            "edit": ToolKind.FILE_EDIT,
            "load_skill": ToolKind.READ_ONLY,        
        }
        kind = kinds.get(tool_name, ToolKind.OTHER)

        if self.mode == PermissionMode.BYPASS:
            return PermissionOutcome.ALLOW

        if kind == ToolKind.READ_ONLY:
            return PermissionOutcome.ALLOW

        if self.mode == PermissionMode.PLAN:
            return PermissionOutcome.DENY

        if (
            self.mode == PermissionMode.EDIT
            and kind == ToolKind.FILE_EDIT
        ):
            return PermissionOutcome.ALLOW

        return PermissionOutcome.ASK