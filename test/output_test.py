from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import tempfile

from decode.config.settings import Settings
from decode.permission.gate import PermissionGate
from decode.tools import files
from decode.tools.truncate import truncate


with TemporaryDirectory(
    dir=Path.cwd(),
    prefix="hypa-output-check-",
) as directory:
    root = Path(directory)
    original_tempdir = tempfile.tempdir
    original_settings = files.settings

    # Keep spill files inside this disposable test directory.
    tempfile.tempdir = directory

    try:
        cases = [
            ("Empty", "", 2, 100, ""),
            ("Below limits", "hello\n", 2, 100, "hello\n"),
            ("Line cap", "one\ntwo\nthree\n", 2, 100, "one\ntwo\n"),
            ("UTF-8 byte cap", "é\nb\n", 10, 3, "é\n"),
            ("Oversized first line", "abcdef\nnext\n", 10, 2, "abcdef\n"),
        ]

        for label, content, lines, byte_cap, expected in cases:
            result = truncate(
                content,
                max_lines=lines,
                max_bytes=byte_cap,
            )

            assert result.text == expected, (label, result.text)
            assert result.truncated == (expected != content)

            if result.truncated:
                assert result.full_path is not None
                assert result.full_path.resolve().is_relative_to(
                    root.resolve()
                )
                assert result.full_path.read_text(
                    encoding="utf-8"
                ) == content
            else:
                assert result.full_path is None

            print(f"{label}: PASS")

        workspace = root / "workspace"
        workspace.mkdir()
        (workspace / "a.py").write_text(
            "needle one\nneedle two\n", encoding="utf-8"
        )
        (workspace / "b.py").write_text(
            "needle three\n", encoding="utf-8"
        )

        ctx = SimpleNamespace(
            deps=SimpleNamespace(
                cwd=workspace,
                gate=PermissionGate(),
            ),
            tool_call_approved=True,
        )

        files.settings = Settings(max_output_lines=1)

        checks = [
            (
                "Read cap",
                lambda: files.read(ctx, "a.py"),
                "1\tneedle one\n2\tneedle two",
            ),
            (
                "Glob cap",
                lambda: files.glob(ctx, "*.py"),
                "a.py\nb.py",
            ),
            (
                "Grep cap",
                lambda: files.grep(ctx, "needle"),
                "a.py:1:needle one\n"
                "a.py:2:needle two\n"
                "b.py:1:needle three",
            ),
        ]

        for label, operation, complete_output in checks:
            before = set(root.glob("decode-output-*.txt"))
            output = operation()
            created = set(root.glob("decode-output-*.txt")) - before

            assert output.splitlines()[0] == complete_output.splitlines()[0]
            assert "[Output truncated;" in output
            assert len(created) == 1

            spill = created.pop()
            assert spill.read_text(encoding="utf-8") == complete_output
            print(f"{label}: PASS")

    finally:
        tempfile.tempdir = original_tempdir
        files.settings = original_settings

print("All output checks passed; temporary fixtures removed.")