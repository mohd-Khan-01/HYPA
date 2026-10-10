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

- Current position: Day 1 of the active 10-day roadmap closed by the learner on 11 October 2026. Next: Day 2 file tools, planned for 12 October. The earlier session numbers remain the concept inventory.
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
- Next action: guide a mode-based callable PermissionGate, correct PermissionOutcome enum spelling/values, and align AgentDeps' decision type with that enum. Retain the current demo call contract; add structured requests, deny/allow rules, tool registry, and framework-deferred approval in subsequent increments. Independent explanation of async execution and verification of full spill contents remain pending. No non-Markdown edits are authorized without explicit permission.

After each session record: date, outcome built, checks performed, concepts you explained back, unresolved questions, exercise status, and next step.
