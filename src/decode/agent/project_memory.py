from pathlib import Path


MAX_PROJECT_BYTES = 4_000


def load_project_instructions(cwd: Path) -> tuple[str, str | None]:
    try:
        base = cwd.resolve()
        path = (base / ".hypa" / "project.md").resolve()

        if not path.is_relative_to(base):
            return "", "Project instructions skipped: path leaves the workspace."

        with path.open("rb") as stream:
            payload = stream.read(MAX_PROJECT_BYTES + 1)

    except FileNotFoundError:
        return "", None
    except OSError as error:
        return "", f"Project instructions skipped: {error}"

    if len(payload) > MAX_PROJECT_BYTES:
        return "", "Project instructions skipped: file exceeds 4,000 bytes."

    try:
        text = payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return "", "Project instructions skipped: file is not valid UTF-8."

    return text, None