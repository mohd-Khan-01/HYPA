# HYPA: learning to build a coding agent

Prepared on 7 October 2026. This is our teaching sequence, adapted to your current code; it is not the course author's session numbering.

Scheduling update, 10 October 2026: the user requested a 10-day roadmap at 3 hours daily. Follow ROADMAP_10_DAYS.md for the active daily schedule and local v1 completion criteria. Retain this document's 26 sessions as the concept inventory and extension path; the 30-hour schedule does not imply every upstream infrastructure feature is included.

## Goal and pace

Build an agent you can explain, debug, and extend: it can inspect a project, plan a change, use tools, request permission, edit code, run checks, and report what actually happened. Then extend it with context management, isolation, subagents, evaluation, remote execution, and replay.

Plan for 26 sessions of roughly 60–90 minutes, with some sessions needing a second sitting. This is an estimate for learning and implementing, not a deadline. We move forward when the feature works and you can explain its important decisions. Sessions 1–12 form the first usable local agent; the remaining sessions deepen and extend it.

Our teaching routine in every session:

1. Recap the previous feature and state today's runnable outcome.
2. Explain the problem and all concepts needed for this step, including Python prerequisites.
3. Trace a small example by hand before building.
4. Implement in small pieces; explain each new line or logical block and its inputs, outputs, and failure paths.
5. Run a demonstration and meaningful checks, including an edge case or intentional failure.
6. Give you a small variation to implement and an understanding question.
7. Record code progress separately from concepts demonstrated and unresolved questions.

When a concept is unfamiliar, use a tiny standalone example first. Code generation alone is not evidence of learning. The session descriptions below are the syllabus; the full explanations happen during the sessions as we build.

## What exists today

All 20 project files were scanned, excluding dependency internals and Git metadata. The lockfile records Pydantic AI 2.42.0. Python is configured for 3.12 or newer.

| Area | Current state | Where we use it |
| --- | --- | --- |
| Project setup | `pyproject.toml`, `uv.lock`, Python version, minimal README | Session 1 |
| CLI | `src/hypa/__init__.py` prints a greeting | Sessions 1 and 11 |
| Events | Several dataclasses and an event union; a duplicate class and spelling inconsistencies | Session 2 |
| Dependencies | `AgentDeps` with paths and callbacks; broken import and inconsistent resolver names | Sessions 3–4 |
| Permissions | Modes and kinds started; gate and permission entity modules empty | Session 5 |
| Read/glob | Partly implemented; missing settings and approval implementation | Session 6 |
| Truncation | Substantial implementation; misplaced future import prevents compilation | Session 7 |
| Edit | Exact and whitespace matching started; synchronous function contains `await` | Sessions 4 and 8 |
| Agent factory | Empty | Session 9 |
| Agent loop, tests, UI, context, sandbox | Not yet implemented | Subsequent sessions |

The `src/hypa` entry point and `src/decode` implementation currently use two package names. Session 1 will explain packaging and choose one coherent arrangement. Empty `__init__.py` files are normal package markers; empty factory/gate/approval files represent unfinished behavior.

We will revisit these concrete bugs while teaching their concepts:

- `decode.entitie.events` references a package that does not exist.
- Dependency resolver field names do not match their intended callers.
- `_render_numbered` creates a set for `line_limit`, passes keyword-only parameters positionally, and returns the untruncated string.
- `ApprovalRequired` is not imported, and a function is raised as though it were an exception.
- `_normalized_with_positions` strips the normalized text without trimming its position map, so leading whitespace can shift a replacement to the wrong original location.
- `await` must occur inside an appropriate asynchronous function; a future import must appear before ordinary executable statements/imports.

## How the reference informs this plan

The course has eight lessons covering architecture, the agent loop, sandboxing, context, subagents, deployment, evaluation, and replay. We expand these into smaller implementation sessions. See the [course outline](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course#-course-outline).

For the initial comparison I inspected the course README and source structure, its dependency object, factory, file-tool implementation, permission gate, registry, loop, glossary, and architecture-decision index. This was a targeted architectural scan, not a line-by-line audit of every upstream file or every linked article. We will read each relevant lesson and implementation more closely when its session starts.

The reference's current implementation is more developed than your scaffold. We will build simplified versions first and explicitly explain later upgrades. We will check framework compatibility at implementation time rather than assuming snippets from different revisions fit together.

## Sessions

### 1. Understand the whole agent and make the project structure clear

**Concepts:** A model generates responses; a tool is a callable operation; an agent loop repeatedly exchanges model requests and tool results. The harness supplies execution policy, state, interfaces, and services around that loop. Explain packages, modules, imports, the `src` layout, virtual environments, `uv`, lockfiles, build configuration, and a CLI entry point.

**Build:** Trace the existing files, settle the HYPA/decode package arrangement, and make the CLI enter a small application function. Keep incomplete future modules outside today's startup path.

**Demonstration:** Launch the CLI from the intended environment and identify the function that runs. Draw a prompt → model → tool → tool result → model → answer trace.

**Your exercise/check:** Explain why the model itself cannot read a local file without an execution mechanism. Trace how `hypa` reaches Python code.

### 2. Represent what happens using events

**Concepts:** Classes and objects, dataclasses, type annotations, union types, immutable event records, `frozen=True`, `slots=True`, and events versus direct UI printing. A text delta is a small fragment of a streamed response.

**Build:** Clean up `entities/events.py`; define consistent start, text, tool, error, and finish events. Make a simple printer consume simulated events.

**Demonstration:** Render a fake agent turn without contacting a model.

**Your exercise/check:** Add one event and explain why the agent core should emit data instead of importing terminal widgets.

### 3. Give tools their dependencies and configuration

**Concepts:** Dependency injection means explicitly passing the services and state a function needs. Explain callbacks, `Callable`, `Literal`, `Path`, per-run versus process-wide state, `field(default_factory=list)`, configuration defaults, environment variables, and secret handling.

**Build:** Repair `agent/deps.py`, agree on callback names, and add minimal `config/settings.py` for model selection and output limits. Use fake callbacks initially.

**Demonstration:** Two dependency objects have independent task lists; changing settings affects an output limit predictably.

**Your exercise/check:** Substitute a collecting event sink for a printing sink. Explain what would go wrong if every run shared one mutable list.

### 4. Understand asynchronous execution before wiring approvals

**Concepts:** `def` versus `async def`, coroutine objects, `Awaitable`, `await`, the event loop, cooperative waiting, blocking I/O, tasks, cancellation, and basic `try/finally` cleanup. Waiting for an API or human response differs from computing a result immediately.

**Build:** Write a tiny fake async permission resolver and caller. Use the existing `await` syntax error to understand the rules. Choose a coherent boundary for synchronous file helpers and asynchronous orchestration.

**Demonstration:** Trace creation and awaiting of a coroutine. Show what happens when an async function is called without awaiting it.

**Your exercise/check:** Implement a fake async question resolver and explain when its body actually runs.

### 5. Decide which actions are allowed

**Concepts:** Policy versus interaction; tool kinds; permission requests, decisions, and outcomes; modes; rule matching; precedence; and checking permission before a side effect. A permission gate decides; a resolver obtains the human response.

**Build:** Implement permission entities and `permission/gate.py`. Start with a mode/kind table, then introduce deny/allow rules and subjects such as paths or commands. Correct the default mode value.

**Demonstration:** Read is allowed in plan mode; edit is denied; default mode asks for an edit; a deny rule overrides an allow rule.

**Your exercise/check:** Predict decisions for a small table before running it. Explain why plan mode's prompt alone cannot enforce read-only behavior.

### 6. Let the agent inspect files

**Concepts:** Relative and absolute paths, `resolve`, containment, traversal, symlinks, glob patterns, text encoding, numbered lines, slices, keyword-only arguments, exceptions, and model-readable retry messages. Path containment is one boundary; it does not isolate arbitrary shell commands.

**Build:** Repair `read`, `glob`, `_resolve_in_cwd`, `_number_lines`, and `_render_numbered`. Introduce the approval helper contract using fakes; real model pause/resume comes in Session 10.

**Demonstration:** Read a line range, discover Python files, and handle a missing file, directory, empty file, and outside-workspace path. Include Windows absolute-path cases.

**Your exercise/check:** Predict the result of offset 3 and limit 2. Explain why a keyword-only function rejects positional arguments.

### 7. Keep tool output manageable

**Concepts:** Characters versus UTF-8 bytes versus model tokens; line limits; byte limits; preserving line boundaries; temporary files; context managers; and retaining complete output while showing a bounded result.

**Build:** Repair `truncate.py` and ensure the file renderer returns its capped output and spill notice. Define behavior for zero/invalid limits and for a first line larger than the byte cap.

**Demonstration:** Try short output, many lines, a long line, and non-ASCII text; verify the spill file contains the original.

**Your exercise/check:** Explain why a character count is not a byte count and why byte caps alone are not exact token accounting.

### 8. Edit and create files predictably

**Concepts:** Side effects, preconditions, exact replacement, ambiguous matches, whitespace normalization, index maps, preserving surrounding content, encoding/newlines, and optional atomic replacement.

**Build:** Repair `edit`, add `write`, and start with exact matching. Introduce normalized matching only after tracing the position-map invariant. Gate before mutation and use temporary exercise files.

**Demonstration:** Replace one match; reject zero or multiple matches; demonstrate permission denial leaves content unchanged; trace leading whitespace in a normalized match.

**Your exercise/check:** Repair an index-map example by hand and explain how a wrong index could alter unrelated code.

### 9. Connect a model to a tool registry

**Concepts:** Model versus provider, request messages, instructions, function schemas, argument validation, decorators, `RunContext`, tool registration, and a factory. The model requests a tool call; our program executes it.

**Build:** Implement the minimal factory and a registry whose entries contain name, function, and kind. Use one provider initially and a fake/test model for deterministic exercises. Verify APIs against the installed Pydantic AI version.

**Demonstration:** A scripted tool call reads a fixture; optionally repeat with a configured live model. Inspect the arguments rather than inferring execution from the answer text.

**Your exercise/check:** Add one small read-only tool and explain how its signature becomes a model-facing interface.

### 10. Drive the loop and pause for approval

**Concepts:** Model-request nodes, tool-call nodes, tool results, final responses, async iteration, tool-call IDs, retry budgets, `ApprovalRequired`, deferred requests/results, and deny outcomes. A pause must preserve enough state to resume the same call.

**Build:** Add a small `agent/loop.py`, translate framework events into our event types, and implement approval pause/resume. Keep the gate's decision separate from the human-input resolver.

**Demonstration:** Trace read → proposed edit → ask → approve → edit → final response, then repeat with denial. Confirm the action happens once.

**Your exercise/check:** Explain the difference between a tool error, a retry, and a paused approval. Predict the next loop step after each.

### 11. Carry conversation history through a usable CLI

**Concepts:** A turn versus a session, message history, user/model/tool messages, serialization, JSONL, append-only logs, and resume. Persisted conversation is distinct from a reusable project memory file.

**Build:** Replace the greeting with a basic prompt loop, maintain history, and add a small session log/resume path. Start with plain terminal input/output.

**Demonstration:** Ask a question about a file, refer to it in a second turn, restart, and resume a saved conversation.

**Your exercise/check:** Explain why tool results must stay associated with their calls and what information a fresh process otherwise loses.

### 12. Complete the first local coding workflow

**Concepts:** Search versus reading, subprocesses, argv versus shell strings, stdout/stderr, exit codes, timeouts, working directories, task state, network results, and human questions. Explain each tool separately before combining them.

**Build:** Add search, a bounded command executor, a task-list tool, web fetching, and `ask_user` in small increments. Adapt the course's `bash` contract to the shell actually available on Windows. Reuse permissions and truncation.

**Demonstration:** In a disposable exercise project, find a bug, read the code, propose/edit a fix, run its checks, and report the observed result.

**Your exercise/check:** Interpret a failed command using its exit code and output. Explain why task-list state does not prove a code change succeeded.

**Checkpoint A:** A basic local coding agent works, and you can trace a complete tool-calling turn.

### 13. Give the agent a terminal interface

**Concepts:** Presentation versus core behavior, terminal rendering, input handling, streaming display, prompts, status, and dependency boundaries.

**Build:** Introduce a small TUI incrementally; display text deltas, tool activity, errors, and approval questions through the same event contract.

**Demonstration:** The same core works with both the simple printer and the terminal UI.

**Your exercise/check:** Add a display feature without changing file-tool logic.

### 14. Accept steering and stop work cleanly

**Concepts:** Queues, safe loop boundaries, steering versus follow-up, single active turns, locks, futures, a shared decision channel, cancellation, and cleanup.

**Build:** Add a harness runner that queues new input, applies steering before a model request, and handles cancellation and approval responses without confusing their destinations.

**Demonstration:** Redirect a running task at a safe point, enqueue a follow-up, and cancel while waiting. Confirm no second overlapping turn mutates the same state.

**Your exercise/check:** Explain why a new user instruction should not be inserted into a partially executed file write.

### 15. Put execution behind a sandbox boundary

**Concepts:** Permission versus isolation, host versus isolated workspace, executor interfaces, containers, mounts, credential boundaries, file transport, artifact return, and cleanup.

**Build:** Introduce a narrow execution backend contract, test it with a fake, then add a local container backend when available. Route both commands and file access through the intended workspace boundary.

**Demonstration:** Change an exercise file inside isolation and deliberately return the intended result. A backend failure must not silently execute the command on the host.

**Your exercise/check:** Explain why checking a path in the read tool does not restrict every path a shell command can access.

### 16. Give the agent project memory

**Concepts:** Instructions, durable memory, conversation history, loading precedence, prompt assembly, size limits, and explicit evidence for stored facts.

**Build:** Load project instruction and memory files into the run; add a deliberate memory-write path with appropriate mutation policy.

**Demonstration:** A new conversation follows a saved project convention without needing the previous transcript.

**Your exercise/check:** Classify several examples as configuration, current task state, transcript history, or durable project memory.

### 17. Load reusable skills on demand

**Concepts:** Reusable instructions, Markdown/frontmatter, catalogs, validation, dispatch, progressive disclosure, and instruction content versus executable actions.

**Build:** Discover skill metadata, expose a compact catalog, and load a selected skill body and resources when needed.

**Demonstration:** Invoke a small review skill; subsequent edits still pass their normal permission checks.

**Your exercise/check:** Explain why loading every skill body into every request wastes context.

### 18. Manage a growing context window

**Concepts:** Context occupancy versus cumulative token usage, token estimates, old tool-output reduction, summarization, recent-message retention, tool-call/result boundaries, and information loss.

**Build:** Add a context gauge, then cheap output reduction and a summary-based compaction path with explicit success/failure outcomes.

**Demonstration:** Compact a long synthetic history while preserving recent goals and valid call/result pairs. Show how a failed summarizer leaves usable state.

**Your exercise/check:** Identify a valid history cut point and a fact that a summary must preserve.

### 19. Ask a language server about code

**Concepts:** Text search versus semantic code intelligence, language servers, LSP, JSON-RPC, message framing, initialization, request IDs, diagnostics, definitions, and references.

**Build:** Start with one LSP operation, then attach bounded diagnostics after an edit. Make the service optional and best-effort.

**Demonstration:** Edit an exercise file and display a real diagnostic; the agent still works when the server is unavailable.

**Your exercise/check:** Explain a case where grep finds text but a semantic reference lookup answers a different question.

### 20. Define build, plan, and review personas

**Concepts:** Prompt specialization, tool allowlists, configuration validation, permission-mode defaults, and persona definitions versus distinct model instances.

**Build:** Add a small agents catalog and switch active instructions/tool visibility through the existing dependencies.

**Demonstration:** A plan persona inspects and proposes work; a build persona can request edits; a reviewer produces evidence-based findings.

**Your exercise/check:** Explain why changing the prompt alone does not remove edit capability.

### 21. Delegate bounded work to subagents

**Concepts:** Parent/child context, task scope, narrowed capabilities, fan-out, concurrency limits, semaphores, separate histories, report synthesis, budgets, and partial failures.

**Build:** Add one read-only exploration child first, then bounded parallel exploration. Prevent recursive spawning and aggregate concise reports with file/line evidence.

**Demonstration:** Explore two independent code areas and combine their findings. One failed child produces an explicit failure record.

**Your exercise/check:** Decide whether three sample tasks benefit from delegation and explain its context and latency costs.

### 22. Observe what the agent actually did

**Concepts:** Logs, structured events, traces, spans, session IDs, latency, model usage, cost accounting, error attribution, and sensitive-data handling.

**Build:** Add local structured records first, then integrate the course's Opik tracing approach when configured.

**Demonstration:** Follow a turn from model request through approval and tool execution; identify the slow or failing step using recorded evidence.

**Your exercise/check:** Distinguish successful API completion from successful completion of the user's coding task.

### 23. Evaluate behavior and prevent regressions

**Concepts:** Unit tests versus integration tests versus agent evaluations, fixtures, outcome-based checks, stochastic behavior, repeated trials, baselines, benchmark tasks, and regression cases.

**Build:** Create a small evaluation set: locate a definition, fix a toy bug, obey a denied edit, and complete a check-and-report workflow. Verify file diffs and command results, not just confident prose.

**Demonstration:** Compare two configurations on the same fixtures and report pass rates, failures, usage, and latency. Keep deterministic harness checks alongside live-model evaluations.

**Your exercise/check:** Design an evaluator that detects a claimed fix when the underlying code is unchanged.

### 24. Run the same core headlessly and remotely

**Concepts:** Non-interactive execution, explicit policy, request budgets, entry points, serializable inputs, environment configuration, remote secrets, serverless functions, artifact retrieval, webhooks, and scheduled triggers.

**Build:** Add a headless local command first, then an optional Modal runner using the same factory and loop. Define what happens when a remote run needs a human answer; add a request ceiling before unattended runs.

**Demonstration:** Execute a bounded fixture task locally and remotely and retrieve its result and logs. Study webhook/cron entry paths after a manual remote run works.

**Your exercise/check:** Explain what disappears when there is no terminal input loop and which configuration must travel with the task.

### 25. Record and replay controlled experiments

**Concepts:** Rerun versus replay, recording boundaries, tool-output capture, identifiers, compatibility, provenance, and controlled comparison. A replay may reuse recorded tool evidence while changing model/prompt behavior; it is not automatically a fresh execution of every side effect.

**Build:** Inspect the course's current Kitaru integration and dependency requirements, then add a recording/replay path compatible with our chosen versions. Define exactly which steps execute and which outputs are restored.

**Demonstration:** Compare a baseline with a changed model or prompt against recorded evidence, and label the experiment's limits.

**Your exercise/check:** Explain why replayed shell output cannot prove that a newly proposed patch passes a freshly executed test.

### 26. Capstone: build, diagnose, and explain HYPA

**Concepts:** Architectural tradeoffs, failure recovery, evidence-based reports, acceptance criteria, and explaining a system end to end.

**Build:** Complete a small real coding task in an exercise repository, inspect its trace and diff, run meaningful checks, improve one weak component, and document the result.

**Demonstration:** Repeat with a denied action, tool failure, and cancellation/resume scenario. Draw the complete architecture and explain why each component exists.

**Your exercise/check:** Implement one extension with limited hints and explain its data flow, permission boundary, and verification strategy.

**Checkpoint B:** You can build and explain the local agent independently. **Checkpoint C:** You can evaluate and extend the advanced harness with clear limits on what has been verified.

## Course mapping and reference reading

| Course lesson | Our sessions | Reference |
| --- | --- | --- |
| 1: Building a coding agent | 1–4 | [README and architecture](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course) |
| 2: Bare-bones loop | 5–14 | [Agent source](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/tree/main/src/decode/agent), [file tools](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/src/decode/tools/files.py), [registry](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/src/decode/tools/registry.py), [permission gate](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/src/decode/permissions/gate.py) |
| 3: Sandboxing | 15 | [Sandbox guide](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/running_the_code/03_sandboxing.md) |
| 4: Context engineering | 16–20 | [Glossary](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/docs/glossary.md), [architecture decisions](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/tree/main/docs/adr) |
| 5: Subagents | 21 | [Source structure](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/tree/main/src/decode) and glossary |
| 6: Deployment | 24 | [Deployment guide](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/running_the_code/04_deploy.md) |
| 7: Evaluations | 22–23 | [Evaluation guide](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/running_the_code/05_evals.md) |
| 8: Replay evaluations | 25 | [Replay guide](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course/blob/main/running_the_code/06_evals_replays.md) |
| Our capstone | 26 | HYPA plus a disposable exercise project |

Reference reading accompanies the session; you do not need to understand the finished repository before starting. Cloud/provider setup is chosen when needed, and current availability/costs are verified then.

## Progress record

- Current position: Day 3 in progress on 14 October 2026: model-injected factory and read-only registry are saved; learner has obtained a Groq API key and wants to prioritize the first live read-only run. The earlier session numbers remain the concept inventory.
- Implemented during this planning task: no application changes.
- Scan verification: the existing `files.py` and `truncate.py` have syntax errors; no project test suite was found.
- Concepts demonstrated by the learner: distinguished the model's read request from tool execution, proposed inspecting both candidate files, correctly traced the AgentDeps import, and supplied the corrected events import. Search-before-create and clarification-versus-permission were explained; independent application of those distinctions still needs practice.
- Questions to explore in Session 1: package/import structure and the distinction between model, tools, loop, and harness.
- Session 1 initial verification (7 October 2026): the existing virtual-environment Python discovers both `hypa` and `decode` under `src`; importing `hypa` and calling `hypa.main()` prints the greeting. Discovery of `decode` does not prove its unfinished modules import successfully. Application code has not been changed.
- Session 1 exercise (8 October 2026): the learner corrected the import to `from decode.entities.events import Event` and reported `Import successful`; the saved source confirms the correction. Class versus instance, event unions, and top-level import execution were introduced.
- Sessions 1–2 implementation evidence (8 October 2026): the learner reported successful greeting, empty-input, exit, repeated-input, and simulated-event runs. Source inspection confirms `cli.py` contains the input loop and event renderer. A trailing `return` in the simulated-event branch currently ends the CLI after one valid task; fix this before treating repeated tasks as verified for the latest version. Event naming/duplicate/field cleanup is still pending in the saved source. Dataclass `frozen`/`slots` behavior and event-union design have not yet been assessed.
- Teaching preferences: move faster through basic Python, retain explanations for agent concepts, and use activated-environment commands in learner instructions.
- File-read milestone (8 October 2026): source inspection confirms `demo_turn` accepts an EventSink, reads UTF-8 content, handles missing/non-file paths and read/decode errors, and emits real ToolResult content. The CLI's trailing return has been removed. The learner reports the demo working; the assistant has inspected source but has not independently executed these cases. Event cleanup remains pending unless subsequently verified.
- Dependency-wiring review (9 October 2026): resolver names are corrected; the CLI constructs AgentDeps before the loop and passes it into demo_turn. In the current saved demo.py, the earlier file-reading body was removed and the function ends after resolving target. Direct execution verified: allowed README read emits no events, allowed missing-file read emits no events, and denied read emits Read denied. Restore the file checks/read/event block with deps.emit before considering the refactor complete. The duplicate AssistantTextDelta and event naming/field typos remain. No application files were changed by this review.
- Follow-up verification (9 October 2026): the learner restored the read body; direct execution confirms one ToolCallStarted followed by a ToolResult exactly matching README.md, one missing-file message for an absent path, and one denial message for a denied read. TurnStarted and the duplicate event class are corrected; PermissionRequested.desription still needs renaming. The pasted output contained two start messages, but the inspected code and direct execution emit one per read. Next core exercise: async approval handling, followed by configuration; understanding of coroutine execution is not yet assessed.
- Async approval repair (9 October 2026): the CLI awaits demo_turn via asyncio.run and uses ask_permission, but the latest demo function again lacked its file-read body. The assistant restored only the existing path/read/event block after approval. Branch checks with immediate async fake resolvers passed for approved readme.md (exact contents), refusal (no read result), and approved missing file (message). Event-loop-based checks hung in the tool environment and were stopped; these checks manually advanced the coroutine with non-suspending fakes, so end-to-end interactive async execution remains for the learner to confirm. This remains a teaching demo, not the reference's Pydantic AI deferred-approval implementation.
- Settings milestone (9 October 2026): source inspection and read-only execution confirm the learner's frozen Settings object exposes 2000 lines / 50000 bytes and rejects a zero line limit. The learner reports the provided checks working. truncate.py still fails compilation because its future import is at line 5; next exercise moves it to the top and connects truncate output/spill notices to the demo's ToolResult. No non-Markdown files were changed during this check.
- Truncation integration review (9 October 2026): source inspection confirms the future import is now correctly placed first in truncate.py. demo.py still imports neither settings nor truncate and emits raw content in its final ToolResult. Permission handling and the existing read body are intact. The learner's next edit is to add those imports and replace only the final emission with truncation plus a spill notice. No application files were modified or spill files created during this review.
- Subsequent review (9 October 2026): settings/truncate imports and capped-result emission are present, but the file resolution/read block was removed again. Read-only execution reproduced NameError: content is not defined for an allowed read; denial still returns its message. Give the learner the complete function with permission, read, and truncate blocks to avoid ambiguity from partial replacement snippets. No code or spill files were changed/created by this review.
- Learner truncation demonstration (9 October 2026): with max_output_lines set to 1, an approved read of readme.md displayed its first line plus a truncation notice naming a temp spill file. This demonstrates visible integration; full spill-file contents and the byte-limit edge case have not yet been independently checked. Next guided exercise is workspace path containment. Remind the learner to restore the normal output cap after the experiment.
- Workspace-boundary milestone (9 October 2026): the learner reports Not a file for an absent in-workspace path and Path is outside the working directory for a parent-directory path. Source inspection confirms correct guard indentation and preserved reading/truncation logic; normal settings are restored. Current position: starting Session 5's mode/kind policy, with Sessions 6–7 concepts already exercised in the demo.
- Day 1 policy milestone (11 October 2026): the learner implemented PermissionGate and corrected PermissionOutcome.ALLOW from alLow to allow. Both learner output and independent read-only checks confirm all 12 mode/kind cases; unknown-tool classification also passed in every mode. Next is dependency/CLI integration and remaining event cleanup. No application files were modified by the assistant.
- Day 1 closure (11 October 2026): saved CLI wiring and event cleanup confirmed; isolated default read, missing path, outside path, and deny-before-path-access checks passed. Dynamic-mode behavior and separate policy/containment/truncation responsibilities were explained. The learner is pushing their own changes and continuing Day 2 tomorrow. Next lesson: repair files.py and extract the demo's behavior into reusable actual tools; do not push or edit non-Markdown files on the learner's behalf without explicit authorization.
- Day 2 import milestone (11 October 2026): the learner reports successful import of read/glob/edit after the approval package-name/import/raising fixes and replacing synchronous await with deferred approval. Saved read/glob and approval imports confirm those changes. Next exercise repairs numbered rendering (set versus scalar, keyword-only arguments, returning capped text) and empty-file behavior before direct read/glob verification. No non-Markdown files were modified by the assistant.
- Day 2 numbered-output milestone (13 October 2026): learner reports all helper checks passing; saved source confirms corrected scalar limit, keyword arguments, capped-text return, and empty-file handling. Independent read-only checks passed for a two-line window, empty content, and zero limit. TestModel and RunUsage construction were checked without model calls. Next: consistently return ModelRetry for escaping paths, reject Windows-anchored glob patterns, cap glob output, and verify actual read/glob using an approved RunContext with no live model requests.
- Day 2 read/glob milestone (13 October 2026): learner provided passing output for a numbered README read, discovery of tools/files.py, and ModelRetry rejection of outside read, missing file, directory read, parent-directory glob, and Windows drive pattern. This verifies direct approved-context behavior, not a live agent run. Next: test unapproved-call deferral and bypass/already-approved helper cases, extract shared capped-output rendering, apply it to glob, and then implement bounded grep.
- Day 2 approval milestone (13 October 2026): learner provided passing output showing read/glob defer before any cwd access, approved resumes do not defer, and bypass does not defer. The supplied fake context intentionally omitted cwd. These are helper/tool-boundary checks rather than full agent-loop approval integration. The separate cap demonstration output has not yet been supplied; next is literal grep with path/line evidence, containment, explicit skipped-file reporting, and shared output caps.
- Day 2 grep milestone (13 October 2026): learner provided matching definition with file/line evidence and successful empty-search, absent-match, and outside-include rejection cases. Saved source confirms shared cap use and skipped-file reporting. Next: write/create-or-replace and exact-only edit, shared mutation permission check, ModelRetry on expected file failures, and disposable-fixture verification of success, ambiguity, absence, denial, and approval pause. Full spill/byte-limit verification remains pending.
- Day 2 mutation milestone (13 October 2026): learner supplied passing output for empty/absent/ambiguous/overlapping match rejection, outside write/edit, plan-mode write/edit denial, unapproved write/edit/create pause, and temporary cleanup. The source was previously inspected and matched the intended implementation. These mutation checks were executed by the learner, not independently rerun by the assistant. The reusable script is saved as file_test.py at the project root rather than tests/test_file_tools.py. Next is line/UTF-8-byte cap, first-long-line exception, complete spill contents, and shared-cap integration for read/glob/grep.
- Day 2 completion (13 October 2026): the learner reports all output tests passing, including line/UTF-8-byte cuts, the oversized-first-line exception, original spill contents, and read/glob/grep cap integration. Mutation and output scripts are saved under test/. The assistant independently scanned all src Python files using compile() with -B; all compile. This does not verify runtime imports or provider/model execution. File-creating tests were run by the learner and were not rerun by the assistant. Day 2 concepts were explained; independent explain-back remains unassessed.
- Day 3 initial verification (14 October 2026): installed Pydantic AI is 2.42.0. Agent/run_sync/TestModel/UsageLimits signatures were inspected. In-memory construction with TestModel, registration of read/glob/grep, and string-or-deferred output succeeded without executing tools or contacting a provider. Learner will implement the registry/factory and run a scripted no-tool smoke check before a deterministic real-tool-call exercise. Scripted responses demonstrate wiring only, not language understanding.
- Day 3 saved-source check (14 October 2026): registry and model-injected factory match the guided implementation. The learner saved the no-tool smoke test as test/test_factory.py. FunctionModel/AgentInfo and tool-call/result message signatures were inspected in the installed package. An attempted local smoke plus deterministic-read execution stalled without output, including with a process-local Windows selector policy, and was stopped; no success is claimed for that run. Provide test/test_agent_read.py for the learner to execute in their activated terminal. It uses a read-only registry, a test-only bypass gate, two scripted model responses, a real README read, matching call/result IDs, and bounded usage. Production gate and CLI remain unchanged. No non-Markdown files were modified and no provider calls were made.
- Day 3 provider choice (14 October 2026): learner obtained a Groq key; do not ask them to paste it or read secret files. Native provider/model modules exist but the groq SDK is not installed. Official Groq docs and installed Pydantic AI source were checked; use a Groq-hosted tool-capable model with configurable ID and session environment authentication. Live read-only runner should show actual successful read returns, apply usage/time/output limits, and keep mutation tools unregistered. No live provider calls have been made by the assistant.
- Day 3 first live read (14 October 2026): learner ran test/agent_test.py against Groq and supplied the actual numbered README tool result and a grounded answer. The run then failed only while displaying usage: TypeError because result.usage() was used. Installed packages are pydantic-ai/slim 2.42.0 and groq 1.7.0. Source confirms AgentRunResult.usage is decorated with @property; use result.usage.requests, not result.usage().requests. Earlier assistant snippets used the wrong accessor syntax; do not attribute this to an unverified dependency upgrade. No code edits or additional live calls were made by the assistant. Natural-language tool selection and real read evidence are now demonstrated; missing-file recovery, request-limit failure, and CLI integration remain pending.
- Day 3 live-run correction confirmed (14 October 2026): learner reports the usage-access correction working. Next guided increment connects Groq to hypa through async run_turn with a normal DEFAULT gate, automatic read-only deferred approval/resume, shared cumulative RunUsage/UsageLimits across legs, and tool event emission. Inspecting current settings shows load_dotenv is already present; do not overwrite it or inspect .env. GroqModel settings and Agent.run/deferred-result signatures were checked locally without any live calls. Keep model factory and read-only registry unchanged; human approval, streaming, cross-turn history, and mutating registrations remain later work.
- Day 3 CLI size failure (14 October 2026): saved CLI now constructs GroqModel and calls run_turn with the normal DEFAULT gate. The loop carries message history and shares usage limits across deferred approval/resume legs. Learner reports Groq HTTP 413: requested 16,286 tokens against an 8,000 TPM allowance. Exact triggering prompt/tool output is unknown; settings still permit 2,000 lines / 50,000 bytes per tool output, which can produce oversized requests as history accumulates. Request/tool-call limits bound counts, and max_tokens bounds generation; none is an input-context cap. Installed native GroqModel does not implement pre-request count_tokens, so do not recommend count_tokens_before_request=True for this provider. Proposed first guided mitigation: 100 lines / 4,000 bytes per result, restart CLI, and retry only a small README read. This is a practical reduction, not a guaranteed aggregate token budget; the first-oversized-line exception and cumulative history remain relevant. No application files were changed and resolution is not yet verified.
- Day 3 smaller-request confirmation (14 October 2026): learner reports the CLI working after reducing output limits. Saved settings actually use 100 lines / 5,000 bytes, rather than the proposed 4,000 bytes; record the implemented values. This establishes a successful smaller request, not general protection against oversized histories. Next exercise requests an absent file followed by a small README fallback to demonstrate ModelRetry recovery. Understanding of token-budget distinctions has not yet been demonstrated by explain-back.
- Day 3 missing-file recovery (14 October 2026): learner reports the missing-file-to-README fallback exercise working. This is learner-reported end-to-end recovery; no transcript or independent execution was supplied. ModelRetry feedback and model-selected corrective actions were explained; independent explain-back remains unassessed. Next is a local FunctionModel that repeatedly requests a one-line README read through the real run_turn/DEFAULT approval path, expecting UsageLimitExceeded before a sixth model request. This checks the shared five-request budget across resume legs without Groq calls. Test not yet reported as passed.
- Day 3 acceptance closure (14 October 2026): learner reports the scripted request-limit exercise passed. Saved test is test/test_req_lim.py, not the proposed test/test_request_limit.py; source confirms use of run_turn, a repeating FunctionModel, normal PermissionGate, and assertions for five model requests plus request_limit in UsageLimitExceeded. The assistant inspected the script but did not rerun it. Day 3 functional milestones are now complete on inspected source and learner-reported execution: native Groq configuration, injected factory/read-only registry, real tool-grounded answer, CLI integration with automatic read-only approval/resume, missing-file recovery, and shared request-budget enforcement. Independent explain-back remains unassessed. Large aggregate histories and the oversized-first-line exception remain unresolved; smaller output limits are a mitigation. Earlier separate factory/deterministic-read exercises are not retroactively marked passed.
- Day 3 architecture clarification (14 October 2026): learner explicitly reports confusion about how the model selects tools, what information it sees, and how the loop works. Functional acceptance does not establish conceptual understanding. Pause the move to Day 4 and explain registration-to-schema conversion, automatic model tool choice versus scripted FunctionModel responses, local RunContext injection, structured call/result IDs, and Pydantic AI's inner execution loop versus our outer deferred-approval loop. Trace a normal DEFAULT-mode read through pause, local gate, approved resume, filesystem read, model-visible result, and final answer. Console event rendering is separate from model feedback; seen_results deduplicates display only. Current CLI starts fresh model history for each entered task. Understanding remains pending a learner trace.
- Day 3 framework-source walkthrough (14 October 2026): learner paraphrased framework responsibilities but placed its loop in cli.py. Clarified three layers: CLI input loop, our approval/resume loop, and framework model/tool iteration. Learner then asked exactly where function invocation is implemented. Inspected installed agent/__init__.py registration, toolsets/function.py name-to-Tool storage and call_func routing, tool_manager.py name resolution/argument validation, _function_schema.py context injection and sync/async call dispatch, and _utils.py's actual func(*args, **kwargs) call. Explain Python functions as stored objects, dictionary lookup by tool name, and argument unpacking alongside the actual local source links. No dependency or application files changed. Independent learner trace is still pending.
- Day 4 started (15 October 2026) at the learner's request. Revisit the Day 3 responsibility split during a concrete mutation trace; do not claim earlier explain-back was completed. Saved loop still raises on ASK, CLI already supplies async ask_permission, and registry/factory still expose only read/glob/grep. First increment: connect ASK to the existing callback with exact tool name/call ID/full arguments, retain gate ALLOW/DENY behavior, then add a separate full file-tool registry while preserving the read-only registration helper. Keep history/usage/resume machinery unchanged. Guide a user-run scratch Markdown write with approval, then refusal and unchanged-file evidence; once-only execution, plan-mode behavior, and cross-task history remain subsequent verification. No non-Markdown edits or live model calls made by the assistant.
- Day 4 first live mutation evidence (15 October 2026): pasted transcript shows write arguments, explicit y, successful Wrote result, and final answer. Read-only inspection confirms day4_scratch.md contains exactly 'Day 4 approve works'. Saved loop, full registry, and factory instructions match the guided changes. Do not infer exactly-once execution from final file contents alone. Refusal is NOT yet demonstrated: the proposed edit was split across separate CLI input() submissions, and its old_string ('Day 4 approval works.') differs from actual saved content. The incomplete first submission searched broadly and reached the five-request limit; the next fragment elicited a model-text refusal without any human approval prompt. This is not evidence of approvals=False enforcement. Guide a single-line request using the actual text, answer n at the tool prompt, and compare file hashes before/after. Broad glob output includes .venv dependencies, unlike grep; record as a separate pending discovery-quality issue. No application files changed by the assistant.
- Day 4 refusal check reported (15 October 2026): learner reports True from the before/after SHA-256 comparison after the guided single-line edit/refuse exercise. This is learner-reported unchanged-byte evidence; no new approval-prompt transcript was supplied, so do not claim independent observation of n or deferred-denial messages. Next is a live approved edit that preserves the old substring and appends ' [approved]': duplicate execution would append the marker twice, making final content a useful witness for that specific call. Verify one approval and one successful edit result, plus exact final content. This does not establish crash-safe exactly-once guarantees.
- Day 4 approved-edit confirmation (15 October 2026): learner reports the marker edit working. Independent read-only inspection confirms exact scratch content 'Day 4 approve works [approved]' with one marker; duplicate application of the same old/new pair would have produced two. This is evidence for the ordinary resume case, not crash-safe exactly-once execution. Next guided change is a CLI /mode command using one shared PermissionGate instance, enum validation, local command interception before model dispatch, and a plan-mode unchanged-hash exercise. Existing _check_mutation rejects plan-mode edits before path resolution and before approval deferral; the model receives ModelRetry policy feedback. No non-Markdown files were edited by the assistant.
- Day 4 runtime-mode confirmation (15 October 2026): learner reports the /mode and plan-mode exercise working. Saved CLI confirms a shared gate, enum validation before assignment, and local command interception; no new hash/denial transcript was supplied, so plan-mode execution evidence remains learner-reported. Next guided increment adds optional ModelMessage history to run_turn's first agent.run, keeps full history for approval resumes, and stores successful result.all_messages() in the CLI for the next task. Important display fix: use result.new_messages() when emitting tool results so earlier tasks' returns are not printed again. Installed result APIs and Agent.run(message_history=...) were verified in source. Add local /clear as a manual context reset; persistence/compaction and failed-turn partial-history recovery remain unfinished. No application files changed by the assistant.
- Day 4 functional acceptance (15 October 2026): learner reports cross-task history and /clear working. Saved source confirms history is created outside the CLI loop, passed to the initial agent.run, replaced from successful result.all_messages(), and cleared locally; event emission uses new_messages(), while approval resumes retain all_messages(). run_turn's optional history parameter is implemented without the proposed keyword-only star; that is valid and does not affect existing keyword calls. Independent read-only compile() scan passed all 20 src Python files with -B; no runtime/mutating tests were rerun and no live calls were made. Day 4 functional milestones are covered by inspected source plus learner-reported checks: approved write/edit, ordinary single-application marker, refusal unchanged hash, runtime modes/plan rejection, and follow-up memory. Understanding checks remain unanswered, so conceptual mastery is not marked complete. Known gaps: dependency-heavy glob, aggregate context budget/first-line exception, failed-turn partial-history recovery, persistent sessions, and crash-safe execution guarantees.
- Next action: brief Day 4 learner trace of call ID, approval decision, carried messages, and new_messages versus all_messages; then Day 5 controlled command execution and a verified coding task. Keep context-budget and glob exclusion work visible as unfinished. No non-Markdown edits are authorized without explicit permission.

After each session record: date, outcome built, checks performed, concepts you explained back, unresolved questions, exercise status, and next step.
