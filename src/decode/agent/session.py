import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter


MAX_SESSION_BYTES = 1_000_000


def session_path(cwd: Path, name: str) -> Path:
    if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name) is None:
        raise ValueError(
            "Use a session name of 1-64 letters, digits, hyphens, or underscores."
        )

    base = cwd.resolve()
    path = (
        base / ".hypa" / "sessions" / f"session-{name}.json"
    ).resolve()

    if not path.is_relative_to(base):
        raise ValueError("Session path must stay inside the working directory.")

    return path


def save_session(path: Path, messages: list[ModelMessage]) -> None:
    payload = ModelMessagesTypeAdapter.dump_json(messages, indent=2)

    if len(payload) > MAX_SESSION_BYTES:
        raise ValueError("Session exceeds the 1 MB storage limit.")

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(payload)

        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def load_session(path: Path) -> list[ModelMessage]:
    with path.open("rb") as stream:
        payload = stream.read(MAX_SESSION_BYTES + 1)

    if len(payload) > MAX_SESSION_BYTES:
        raise ValueError("Session exceeds the 1 MB storage limit.")

    return ModelMessagesTypeAdapter.validate_json(payload)