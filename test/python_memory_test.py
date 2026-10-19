from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from decode.agent.project_memory import (
    MAX_PROJECT_BYTES,
    load_project_instructions,
)


with TemporaryDirectory() as directory:
    root = Path(directory)

    assert load_project_instructions(root) == ("", None)
    print("Missing optional file: PASS")

    path = root / ".hypa" / "project.md"
    path.parent.mkdir()
    path.write_text("Use unittest.\n", encoding="utf-8")

    assert load_project_instructions(root) == ("Use unittest.", None)
    print("Valid instructions: PASS")

    path.write_bytes(b"x" * (MAX_PROJECT_BYTES + 1))
    text, notice = load_project_instructions(root)
    assert text == "" and notice is not None
    print("Oversized instructions skipped: PASS")

    path.write_bytes(b"\xff")
    text, notice = load_project_instructions(root)
    assert text == "" and notice is not None
    print("Invalid UTF-8 skipped: PASS")

    with patch.object(
        Path,
        "open",
        side_effect=PermissionError("simulated unreadable file"),
    ):
        text, notice = load_project_instructions(root)
        assert text == "" and notice is not None

    print("Unreadable instructions skipped: PASS")

print("Project-memory checks passed.")