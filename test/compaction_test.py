import asyncio
from types import SimpleNamespace

from pydantic_ai.messages import (
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.test import TestModel

from decode.agent.compaction import build_summarizer, compact_history


class FakeSummarizer:
    def __init__(
        self,
        text="Goal: build HYPA. Earlier work is user-reported.",
        error=None,
    ):
        self.text = text
        self.error = error
        self.calls = 0

    async def run(self, prompt, **kwargs):
        self.calls += 1
        assert kwargs["usage_limits"].request_limit == 1
        assert "serialized conversation" in prompt

        if self.error is not None:
            raise self.error

        return SimpleNamespace(output=self.text)


def turn(task, answer):
    return [
        ModelRequest(parts=[UserPromptPart(content=task)]),
        ModelResponse(parts=[TextPart(content=answer)]),
    ]


async def main():
    older = turn("Build HYPA", "Earlier notes. " * 140)
    recent = [
        ModelRequest(parts=[UserPromptPart(content="Read README")]),
        ModelResponse(parts=[
            ToolCallPart(
                tool_name="read",
                args={"path": "README.md"},
                tool_call_id="read-1",
            ),
        ]),
        ModelRequest(parts=[
            ToolReturnPart(
                tool_name="read",
                content="# HYPA",
                tool_call_id="read-1",
            ),
        ]),
        ModelResponse(parts=[TextPart(content="README read observed.")]),
        *turn("What next?", "Implement compaction."),
    ]

    history = older + recent
    original = ModelMessagesTypeAdapter.dump_json(history)
    fake = FakeSummarizer()
    compacted = await compact_history(history, fake)

    assert fake.calls == 1
    assert len(ModelMessagesTypeAdapter.dump_json(compacted)) < len(original)
    assert all(
        actual is expected
        for actual, expected in zip(compacted[-len(recent):], recent)
    )
    assert ModelMessagesTypeAdapter.dump_json(history) == original
    restored = ModelMessagesTypeAdapter.validate_json(
        ModelMessagesTypeAdapter.dump_json(compacted)
    )
    assert restored == compacted
    print("Smaller history, intact recent evidence, JSON roundtrip: PASS")

    failures = [
        FakeSummarizer(error=RuntimeError("simulated provider failure")),
        FakeSummarizer(text="   "),
        FakeSummarizer(text="x" * 3_001),
        FakeSummarizer(text="x" * 2_700),
    ]

    for fake in failures:
        try:
            await compact_history(history, fake)
        except (RuntimeError, ValueError):
            assert ModelMessagesTypeAdapter.dump_json(history) == original
        else:
            raise AssertionError("Expected failed compaction")

    print("Provider/empty/oversized/no-reduction failures preserve history: PASS")

    huge = turn("Long task", "x" * 9_000) + recent
    fake = FakeSummarizer()

    try:
        await compact_history(huge, fake)
    except ValueError:
        assert fake.calls == 0
    else:
        raise AssertionError("Expected the input-size guard")

    print("Oversized input blocked before model request: PASS")

    summarizer = build_summarizer(TestModel())
    assert not summarizer._function_toolset.tools
    print("Summarizer has no function tools: PASS")


if __name__ == "__main__":
    asyncio.run(main())