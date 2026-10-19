from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from decode.agent.session import load_session, save_session


history = [
    ModelRequest(
        parts=[UserPromptPart(content="Read README.md")]
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name="read",
                args={"path": "README.md"},
                tool_call_id="read-1",
            )
        ]
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name="read",
                content="1 # HYPA",
                tool_call_id="read-1",
            )
        ]
    ),
    ModelResponse(
        parts=[TextPart(content="The project is HYPA.")]
    ),
]

with TemporaryDirectory() as directory:
    path = Path(directory) / "sessions" / "demo.json"

    save_session(path, history)
    restored = load_session(path)

    assert restored == history
    print("Complete conversation round trip: PASS")

    call = restored[1].parts[0]
    result = restored[2].parts[0]
    assert call.tool_call_id == result.tool_call_id == "read-1"
    print("Tool-call/result association preserved: PASS")

    path.write_text("{broken json", encoding="utf-8")
    try:
        load_session(path)
    except ValidationError:
        print("Malformed session rejected: PASS")
    else:
        raise AssertionError("Malformed JSON should be rejected.")

print("Session-storage checks passed.")