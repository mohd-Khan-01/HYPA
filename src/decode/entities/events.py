from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class TurnStarted:
    pass

@dataclass(frozen=True,slots=True)
class TurnFinished:
    pass

@dataclass(frozen=True,slots=True)
class AssistantTextDelta:
    text:str

@dataclass(frozen=True,slots=True)
class ToolCallStarted:
    tool_name:str
    
@dataclass(frozen=True,slots=True)
class ToolResult:
    tool_name:str
    result:str
@dataclass(frozen=True,slots=True)
class TaskListUpdated:
    tasks:list[str]
    
@dataclass(frozen=True,slots=True)
class PermissionRequested:
    description:str
    
@dataclass(frozen=True,slots=True)
class AskUserRequested:
    question:str

@dataclass(frozen=True,slots=True)
class AgentError:
    message:str
    

Event=(
    TurnStarted
    |TurnFinished
    |AssistantTextDelta
    |ToolCallStarted
    |ToolResult
    |TaskListUpdated
    |PermissionRequested
    |AskUserRequested
    |AgentError
)
