# HYPA

HYPA is a local command-line coding agent built with Python, Pydantic AI, and Groq. It can inspect a project, search files, make permitted changes, run commands, and continue a conversation across saved sessions.

**Status:** under active development. The current execution backend requires Windows.

## Features

- Read files with line numbers, discover paths, and search text.
- Create files and apply exact, unique text replacements.
- Run local programs with approval, timeouts, bounded output, and Windows process-tree cleanup.
- Switch permission modes during a conversation.
- Save and resume conversation snapshots.
- Load optional project conventions and workflow skills.
- Manually compact older conversation while retaining recent complete turns.

## Requirements

- Windows.
- Python **3.12 or newer**; the repository selects 3.12 in `.python-version`.
- Git.
- `uv` for the recommended installation, or pip for the alternative below.
- A Groq API key and access to the configured model.
- Internet access for installing dependencies and making model requests.

The Windows requirement applies to the CLI as currently wired, because its registered command tool imports the Windows execution backend.

## Installation

The commands below use PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/mohd-Khan-01/HYPA.git
cd HYPA
```

### 2. Install dependencies

With `uv` installed:

```powershell
uv sync --locked
.\.venv\Scripts\Activate.ps1
```

This installs the checkout in editable mode and uses the versions recorded in `uv.lock`.

Alternatively, use Python and pip:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

The pip alternative resolves dependencies from `pyproject.toml`; it does not use `uv.lock`. Prefer the locked installation when reproducing this checkout's environment.

### 3. Configure Groq

Create a `.env` file in the HYPA repository root:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

`GROQ_API_KEY` is required. `GROQ_MODEL` is optional and defaults to `openai/gpt-oss-20b`. If you override the model, choose one compatible with tool calling and the CLI's current Groq settings.

You can set the key for the current PowerShell session instead:

```powershell
$env:GROQ_API_KEY = "your_groq_api_key"
```

`.env` is ignored by Git. Keep real API keys out of source files, prompts, and commits.

### 4. Start HYPA

With the environment activated:

```powershell
hypa
```

HYPA opens an interactive prompt:

```text
What should HYPA do?
```

If you prefer to skip environment activation, run this from the HYPA repository:

```powershell
uv run --locked hypa
```

## Working with HYPA

Enter one task per line. Start with a narrow request:

```text
Read README.md and explain what this project does.
```

Other examples:

```text
Find the definition of run_turn in src/decode and explain its approval loop.
```

```text
Inspect exercises/calculator.py. If you find a bug, explain it, apply the smallest fix, and run python -B exercises/test_calc.py to verify it.
```

HYPA starts in `default` permission mode. When an operation needs approval, it displays the tool name and proposed arguments. Enter `y` to approve; other input refuses the request.

Use `/mode plan` for inspection before requesting changes. Switch back to `/mode default` when you want HYPA to request approval for edits and commands.

### Working on another project

HYPA uses the directory from which you launch it as its working directory. After activating HYPA's environment and configuring your key, move to the target project:

```powershell
Set-Location "C:\path\to\your-project"
hypa
```

File tools operate within that directory. Its `.hypa/` directory holds its own local instructions, skills, and sessions.

## Interactive commands

| Command | Behavior |
| --- | --- |
| `/mode` | Display the current permission mode. |
| `/mode default` | Allow reads; ask before file changes and commands. |
| `/mode plan` | Allow reads; deny file changes and command execution. |
| `/mode edit` | Allow reads and file changes; ask before commands. |
| `/mode bypass` | Allow tools without interactive approval. |
| `/save NAME` | Save the current conversation, replacing an existing snapshot with that name. |
| `/resume NAME` | Replace the current conversation with a saved snapshot. |
| `/compact` | Summarize older history while retaining the latest two complete user turns. |
| `/clear` | Reset the current conversation context. |
| `exit` | Leave HYPA. |

These are interactive commands entered at HYPA's prompt, not PowerShell commands. Tasks are currently single-line input.

## Permissions and execution scope

| Mode | Read, glob, grep, load skill | Write and edit | Execute commands |
| --- | --- | --- | --- |
| `default` | Allow | Ask | Ask |
| `plan` | Allow | Deny | Deny |
| `edit` | Allow | Allow | Ask |
| `bypass` | Allow | Allow | Allow |

Plan mode denies changes to every file type, including Markdown. Unknown tool names use the conservative command-like policy. A denied operation remains denied even if an approval flag was supplied.

File tools check workspace containment. Commands run locally with an argument list and `shell=False`, but **execution is not sandboxed**: the working directory does not restrict a program's filesystem access. The model receives conversation text and selected tool outputs through Groq.

Command results include completion or timeout status, an exit code when available, stdout, stderr, and truncation flags. Background descendants are terminated when the call ends, including after normal completion. This runner is intended for finite checks rather than persistent development servers.

## Available tools

The model selects these tools from the registered schemas; users normally describe the desired task in natural language.

| Tool | Purpose |
| --- | --- |
| `read(path, offset, limit)` | Read a UTF-8 file with one-based line numbers and an optional line window. |
| `glob(pattern)` | Find files using a workspace-relative glob pattern. |
| `grep(pattern, include)` | Search literal, single-line text in matching readable files. This is not a regex search. |
| `write(path, content)` | Create or replace an entire UTF-8 file; the parent directory must exist. |
| `edit(path, old_string, new_string)` | Replace exactly one matching occurrence; reject missing, empty, or ambiguous matches. |
| `execute(argv, timeout)` | Run a program from an argument list and return observed execution evidence. |
| `load_skill(name)` | Load a known workflow's instruction text. Loading does not execute its steps or grant permissions. |

`glob` does not implement `.gitignore` filtering. `grep` excludes `.git`, `.venv`, `node_modules`, and `__pycache__`; it is not a general secret-file filter. Keep inspection requests focused on relevant files.

## Saving and resuming conversations

At HYPA's prompt:

```text
/save calculator-review
exit
```

Start HYPA again from the same project directory, then:

```text
/resume calculator-review
What did we inspect, and what remains to be checked?
```

Snapshots are stored as typed message JSON:

```text
.hypa/sessions/session-calculator-review.json
```

Names accept 1–64 ASCII letters, digits, underscores, or hyphens. Snapshots have a 1,000,000-byte storage limit. Writes use a temporary file followed by replacement; invalid loads preserve the active conversation.

Saving is manual. `/clear` does not save, and `exit` does not automatically save. Resuming restores message history, not filesystem contents, the working directory, or permission mode. A new process starts in `default` mode.

Session files may include prompts and file excerpts. `.hypa/` is ignored by this repository and is not included in a fresh clone.

## Project instructions

Optionally create `.hypa/project.md` in the project where you run HYPA:

```markdown
# Project conventions

- Keep changes focused on the requested task.
- Preserve the project's existing style.
- Run relevant checks before reporting success.
- Explain any check that could not be completed.
```

HYPA reads this UTF-8 file at startup, with a 4,000-byte limit. Missing instructions are optional; unreadable, oversized, or invalid files are skipped with a notice. Restart HYPA after editing the file.

Project conventions supplement the current task. They do not change tool permissions. `/clear` resets conversation history while retaining the startup-loaded conventions.

## Workflow skills

A skill is reusable instruction text loaded on demand. HYPA currently advertises a `review` skill in its Python catalog.

The workflow body is a local file, so create it yourself after cloning:

```powershell
New-Item -ItemType Directory -Force .hypa/skills/review
```

Save the following as `.hypa/skills/review/SKILL.md`:

```markdown
# Review a requested file

1. Read the file named in the user's task.
2. Trace its inputs, outputs, and important failure paths.
3. Report concrete findings with file and line references.
4. Separate observed evidence from assumptions.
5. Do not edit files unless the user requests changes.
6. Report checks as passed only after observing their results.
```

Then ask HYPA:

```text
Load the review skill, then review exercises/calculator.py without editing files or running commands.
```

Skill bodies must be non-empty UTF-8 files of at most 4,000 bytes. The catalog contains names and descriptions; the full body is read only when requested. Adding a new directory alone does not register a new skill: update `SKILLS` in `src/decode/tools/skills.py` too.

## Conversation compaction

Use `/compact` before a long conversation becomes difficult to fit into a model request. It:

1. Validates complete user turns and tool-call/result relationships.
2. Retains the latest two complete turns unchanged.
3. Sends older messages to a separate summarizer agent with no registered tools.
4. Replaces history only if the summary is non-empty, within its size limit, and produces a smaller serialized history.

Save a snapshot first if you want the original transcript available later:

```text
/save before-summary
/compact
```

Compaction preserves the original active history on failure. It requires older history to summarize, accepts at most 8,000 serialized older-history bytes, and rejects summaries over 3,000 UTF-8 bytes. Larger inputs need a future chunked summarizer.

These byte limits are not exact token counts. Summarization makes a model request, can omit detail, and does not reset Groq's quota. Verify current files rather than treating a summary as fresh filesystem evidence.

## Configuration and limits

| Setting | Current value | Location |
| --- | --- | --- |
| Groq API key | Required | `GROQ_API_KEY` environment variable or `.env` |
| Model name | `openai/gpt-oss-20b` | Optional `GROQ_MODEL` |
| File-output formatting | 100 lines / 5,000 bytes | `src/decode/config/settings.py` |
| Command capture | 2,500 retained bytes per stream with the default settings | `src/decode/tools/commands.py` |
| Command display | 50 lines per stream with the default settings | `src/decode/tools/commands.py` |
| Command timeout | 10 seconds by default; accepts greater than 0 up to 30 seconds | `execute` tool argument |
| Requests per coding turn | 5, shared across approval resumes | `src/decode/agent/loop.py` |
| Tool calls per coding turn | 6 | `src/decode/agent/loop.py` |
| Main-model output setting | 1,024 tokens | `src/hypa/cli.py` |
| Main-model request timeout | 30 seconds | `src/hypa/cli.py` |

Output-formatting limits are code settings, not environment-variable options. File truncation keeps whole lines and can retain an oversized first line; command output uses strict per-stream byte clipping. Command cleanup can add waiting time beyond the command timeout.

## Development and checks

Run checks from the HYPA repository root with its environment activated. The repository uses individual assertion scripts and standard-library `unittest` checks.

### Offline checks

These do not make model API requests. Some create temporary fixtures or launch controlled local processes.

```powershell
python -B test/test_factory.py
python -B test/file_test.py
python -B test/output_test.py
python -B test/process_test.py
python -B test/commands_test.py
python -B test/command_limits_test.py
python -B test/session_test.py
python -B test/python_memory_test.py
python -B test/skill_test.py
python -B test/compaction_test.py
python -B test/test_req_lim.py
python -B exercises/test_calc.py
```

The skill test supplies its own temporary workflow file; it does not require your local review skill body. `-B` prevents Python bytecode cache writes.

### Optional live model check

This requires your Groq configuration and consumes API quota:

```powershell
python -B test/agent_test.py
```

It asks the model to read `README.md` and checks for an actual successful read-tool result.

## Project structure

```text
src/
  hypa/
    __init__.py          Installed command entry point
    cli.py               Interactive commands and conversation state
  decode/
    agent/
      deps.py            Shared runtime dependencies and callbacks
      factory.py         Agent instructions and tool registration
      loop.py            Deferred approval and resume handling
      session.py         JSON snapshot storage
      project_memory.py  Optional startup project instructions
      compaction.py      Complete-turn splitting and summarization
    config/              Model selection and output settings
    entities/            Local UI event types
    permission/          Permission modes and policy gate
    tools/
      files.py           Read, glob, grep, write, and edit
      approval.py        Tool approval-state helper
      commands.py        Bounded local program execution
      process_output.py  Bounded output buffers
      windows_job.py     Windows process grouping and cleanup
      skills.py          Skill catalog and body loader
      registry.py        Model-visible tool registration
      truncate.py        File-output formatting and spill files
test/                    Behavioral checks and model integration scripts
exercises/               Calculator example and tests
pyproject.toml           Package metadata and dependencies
uv.lock                  Locked dependency versions
```

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `hypa` is not recognized | Activate the installed environment, or run `uv run --locked hypa` from the HYPA repository. |
| PowerShell blocks activation | Use `uv run --locked hypa` from the repository without activating the environment. |
| `Set GROQ_API_KEY before starting HYPA` | Configure the key in the repository's `.env` or the current terminal, then restart. |
| A Python dependency cannot be imported | Run `uv sync --locked` and use that environment. |
| HTTP 413 / request too large | Narrow the task and file requests. Compact earlier when possible; save before clearing history. Provider limits depend on the model and account. |
| A rate-limit error | Check your Groq account's allowance and retry after its rate window permits. `/compact` also consumes model quota. |
| The request or tool-call limit is reached | Break the task into smaller requests; the per-turn budget is deliberately bounded. |
| A snapshot cannot be resumed | Use the same project directory and saved name; confirm the file exists and contains valid snapshot JSON. |
| The review skill cannot load | Create `.hypa/skills/review/SKILL.md` in the current project; `.hypa/` is not cloned from Git. |
| Project instruction changes have no effect | Restart HYPA; the file is read at startup. |
| A background server exits after execution | The command runner terminates descendants when the call ends. Run persistent servers outside this tool. |

## Current boundaries

Sessions, skills, and compaction are explicit operations. HYPA does not currently provide automatic session saving, automatic skill discovery, automatic compaction, or a complete model-context token budget. Command execution is Windows-specific and local. A failed coding turn may have performed an approved side effect before the CLI reports failure; inspect the resulting files before retrying a mutation.

## Contributing

Keep changes focused, add or update checks for changed behavior, and describe observed results. Update this README when setup, configuration, commands, tools, or supported behavior changes so it remains a current guide to the project.

## Acknowledgments

Inspired by [Building a Coding Agent From Scratch](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course).

## License

MIT. See [LICENSE](LICENSE).
