# HYPA: 10-day project roadmap

Prepared 10 October 2026. Budget: 3 focused hours daily, 30 hours total.

If you start today, Day 1 is 10 October and Day 10 is 19 October 2026. The day numbers remain usable if you start later or take a break.

## Finish line

Finish a complete local HYPA v1: an interactive coding agent that interprets a task, discovers and reads files, proposes and performs permitted edits, runs checks, maintains conversation context, and reports observed outcomes. It must have bounded output/execution, clear errors, permission enforcement, a documented setup, and a small regression/evaluation set.

This is a scoped completion target, not a promise to reproduce every feature in the finished upstream repository in 30 hours. Its remote deployment, full TUI/harness steering, language-server integration, Docker/Modal sandboxing, and Kitaru recording/replay need additional implementation and setup time. The earlier 40–60-hour estimate covered a broader project. We retain those features in the extension map below.

Primary reference: [Building a Coding Agent From Scratch](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course). Our implementation should follow its architecture, with explicitly identified simplifications. Consult the relevant article, source, and current installed APIs before each feature.

## Daily routine: exactly three hours

| Block | Duration | Activity |
| --- | --- | --- |
| Understand | 40 minutes | Explain today's concepts and trace one example; read the relevant course component. |
| Build | 100 minutes | You implement the feature in small pieces; I explain, inspect, and diagnose. |
| Verify | 30 minutes | Run the normal case, a failure case, and the day's acceptance check. |
| Explain and record | 10 minutes | Explain one design decision in your own words; update progress and next steps. |

The build block includes debugging time. Use breaks outside the three focused hours. A feature is complete only when its acceptance check passes, not when a file contains code. If a day runs over, use the next build block to finish it and reduce optional enhancements first; do not skip verification to keep the calendar looking complete.

I may independently modify only Markdown files. You apply code and dependency changes. I review and perform read-only checks that avoid generated files/caches unless explicitly authorized otherwise. No credentials are saved in these notes.

## Starting point

Implemented or demonstrated: CLI input loop, event renderer, AgentDeps callback wiring, manual async approval, positive settings validation, read demo, line-cap notice, and workspace path rejection.

Pending: real permission gate, full file-tool repair, model integration, framework-deferred approvals, command execution, history, and behavioral verification. Existing factory code imports `pydant_ai` rather than `pydantic_ai`; its provider/model choice has not been verified. `PermissionOutcome` currently has inconsistent spelling. These are Day 1/3 work, not completed features.

## Day 1 — Stabilize the foundation and permission policy

**Date if starting today:** 10 October. **Earlier sessions:** 1–5, with existing progress reused.

**Understand:** Event versus UI rendering; dependency injection; policy versus approval interaction; enums; tool kinds; the default/plan/edit/bypass mode table. Trace why allow/ask/deny must be checked before side effects.

**Build:** Finish the callable gate, correct outcome names/values, align the dependency type, and clean up event naming. Inspect import/syntax blockers across project-owned modules. Preserve the working demo as a reference while moving toward real tools. Introduce meaningful checks for the policy table.

**Verify:** All 12 mode/kind combinations match the intended table. Unknown tools use the conservative OTHER kind. Denied operations do not execute. Existing README read, missing-file, and outside-path cases still work.

**Explain back:** Why can an approved request still fail the workspace-boundary check?

**Deliverable:** Working permission policy and a known list of remaining tool/model blockers.

## Day 2 — Complete the essential file tools

**Date:** 11 October. **Earlier sessions:** 6–8.

**Understand:** Tool inputs/outputs, numbered lines, offset/limit versus safety caps, UTF-8 bytes, exact replacement, ambiguity, and model-readable errors. Trace whitespace/index mapping before attempting its optional fallback.

**Build:** Repair read/glob, add bounded grep, and implement write/edit with exact matching first. Reuse containment, settings, and truncation. Separate reusable helpers from the learning demo. Keep permission enforcement before mutation. Delay whitespace-normalized editing if exact editing and checks consume the build budget.

**Verify:** Read a line range, find a definition, replace one exact match, reject ambiguous replacement, and prove a denied edit leaves content unchanged. Exercise line and byte truncation and verify full spill contents. Use disposable fixtures for mutations.

**Explain back:** Why must a successful tool result contain evidence from execution rather than a guessed answer?

**Deliverable:** Small reliable file-tool layer.

## Day 3 — Connect the model and drive tool calls

**Date:** 12 October. **Earlier sessions:** 9–10.

**Understand:** Provider versus model, instructions, tool schemas, RunContext, tool registration, factory construction, requests/results, and bounded iteration. Explain which behavior Pydantic AI supplies and which our harness owns.

**Build:** Correct factory imports, choose one supported configured provider/model, and load credentials through configuration. Add a minimal registry and loop. Begin with read-only tools and a deterministic fake/test model before an optional live call. Verify the installed Pydantic AI APIs rather than copying incompatible examples.

**Verify:** A natural-language request causes a real read tool call and an evidence-based answer. A missing-file request produces recoverable feedback. A request limit stops an unproductive run.

**Explain back:** Who executes a tool call, and what reaches the model afterward?

**Deliverable:** First model-connected, read-only HYPA.

## Day 4 — Integrate the reference approval mechanism

**Date:** 13 October. **Earlier sessions:** 10–11.

**Understand:** Coroutine execution, tool-call IDs, ApprovalRequired, DeferredToolRequests, DeferredToolResults, and pause/resume. Distinguish our manual approval demo from the framework mechanism.

**Build:** Connect file mutation tools through the real gate and deferred approvals. Wire the CLI to the actual loop and event stream. Preserve history within a session. Avoid duplicate execution on resume and communicate denial to the model.

**Verify:** The model requests an edit; approval applies it once; refusal leaves the file unchanged. Plan mode refuses mutation. The user can ask a follow-up about the completed change.

**Explain back:** What state must survive an approval pause so that the same call resumes correctly?

**Deliverable:** Local agent that can inspect and perform approved file changes.

## Day 5 — Execute checks and complete a coding task

**Date:** 14 October. **Earlier sessions:** 12 and the execution-boundary concept from 15.

**Understand:** Subprocesses, argv versus shell strings, working directories, stdout/stderr, exit codes, timeouts, output caps, and local execution versus a sandbox. Path guards in file tools do not constrain arbitrary shell behavior.

**Build:** Add one command-execution tool appropriate to Windows/PowerShell, with explicit permission, time limits, output caps, and process cleanup. Work in a disposable exercise repository. Add task-list/user-question support only if the main workflow is reliable.

**Verify:** HYPA reads a toy bug, edits it with permission, runs a meaningful test, and reports its observed outcome. Also run a failing check and a timeout case. No result should claim a check passed merely because the command launched.

**Explain back:** Why does a successful command-launch operation differ from a passing test?

**Deliverable:** First complete inspect → edit → test → report workflow. This checkpoint takes precedence over later enhancements.

## Day 6 — Persist sessions and load project memory

**Date:** 15 October. **Earlier sessions:** 11 and 16.

**Understand:** In-memory history versus serialized messages, JSONL, resume, project instructions, durable memory, prompt assembly, and evidence for saved facts.

**Build:** Add session save/resume using framework-supported message serialization. Load project instruction/memory files with size limits and clear precedence. Keep credentials out of logs and memory. Start with deliberate memory updates rather than uncontrolled automatic writes.

**Verify:** Restart and resume a conversation about an earlier edit. A fresh session follows a saved project convention. An unreadable optional memory file gives a clear outcome rather than breaking startup.

**Explain back:** Which information belongs in transcript history, and which belongs in reusable project memory?

**Deliverable:** Agent continuity across turns and restarts.

## Day 7 — Add skills and control context growth

**Date:** 16 October. **Earlier sessions:** 17–18.

**Understand:** Skill metadata/body separation, progressive disclosure, instructions versus actions, context occupancy versus cumulative usage, summary tradeoffs, and valid tool-call/result boundaries.

**Build:** Implement a small skills catalog with on-demand loading and one useful skill. Add manual conversation compaction with retained recent messages and an explicit failure outcome. Automatic thresholds and multiple compaction tiers are extensions if the basic version consumes the budget.

**Verify:** Invoke the skill without bypassing normal tool gates. Compact a synthetic long conversation, retain the current goal and recent evidence, and preserve valid message pairs. A failed summary must not destroy the usable original history.

**Explain back:** Why should every skill body not be inserted into every model request?

**Deliverable:** Reusable workflows and a demonstrated manual context-management path.

## Day 8 — Add personas and one bounded exploration subagent

**Date:** 17 October. **Earlier sessions:** 20–21.

**Understand:** Persona versus model instance, tool allowlists, parent/child histories, narrowed dependencies, bounded requests, concise evidence-based reports, and partial failure. Parallel fan-out is explained, but comes after one reliable child.

**Build:** Define build/plan/review configurations and enforce their tool capabilities. Add a single read-only exploration subagent with a request ceiling and no recursive spawning. If Day 5's core checkpoint is still unfinished, use this day's build block for recovery and retain this as the first post-roadmap extension.

**Verify:** A plan/explore run cannot edit through the tool layer. The child returns findings with paths/evidence; the parent uses the report without swallowing an explicit child failure.

**Explain back:** When does a separate context help, and when does delegation add unnecessary work?

**Deliverable:** Capability-aware personas and a minimal child exploration path, subject to the core checkpoint.

## Day 9 — Observe and evaluate outcomes

**Date:** 18 October. **Earlier sessions:** 22–23.

**Understand:** Structured logs/events, trace correlation, latency/usage, deterministic checks versus stochastic agent evaluations, repeated runs, baselines, and outcome-based scoring.

**Build:** Add useful local trace records and a small evaluation runner. Prepare tasks covering discovery, toy-bug repair, permission refusal, workspace rejection, and failure reporting. External Opik integration is optional after local evidence is reliable.

**Verify:** Score actual diffs and check results, not persuasive text. Compare two prompt/configuration choices on the same small task set. Record failures and limitations, including cases not run with a live provider.

**Explain back:** How would you detect an agent claiming to fix a bug while leaving the source unchanged?

**Deliverable:** Reproducible small evaluation set and evidence of strengths/weaknesses.

## Day 10 — Capstone, recovery checks, and release documentation

**Date:** 19 October. **Earlier sessions:** 26, with local headless entry from 24 only if time permits.

**Understand:** End-to-end boundaries, acceptance criteria, packaging, recovery, and accurate result reporting. Explain the complete prompt-to-tool-to-result trace without relying on memorized snippets.

**Build:** Resolve capstone failures, polish the plain CLI, and document installation, configuration, permission modes, examples, limitations, and known issues. Verify installed packaging includes the implementation package as well as the public command package. A minimal headless command is optional after the interactive acceptance checks pass.

**Verify:** From a documented setup, complete a small exercise-repository task; inspect the diff; run tests; refuse a proposed edit; reject an outside path; recover from a tool failure; and resume a saved session. Review the evaluation results and state which paths were actually exercised.

**Explain back:** Draw HYPA's architecture and justify each boundary. Identify one extension you can implement with fewer hints.

**Deliverable:** Complete local HYPA v1, runnable demonstration, and honest project documentation.

## v1 acceptance checklist

- [x] CLI accepts natural-language tasks and reports errors (raw provider-error display still needs polish).
- [x] A configured model calls real tools through a bounded loop.
- [x] File read/search/edit/write behavior is verified on fixtures.
- [ ] Denied/refused mutations leave files unchanged.
- [x] Workspace containment and output limits are demonstrated.
- [ ] Command results include observed output/exit status and timeout handling.
- [ ] A toy bug is fixed and verified with meaningful checks.
- [ ] Conversation save/resume and project-instruction loading work.
- [ ] Manual compaction and a skill are demonstrated, or explicitly recorded as unfinished.
- [ ] Persona/subagent work is verified, or explicitly recorded as deferred to protect the core finish line.
- [ ] A small evaluation set measures outcomes and records failures.
- [ ] Installation/usage documentation matches the shipped behavior.

If a checkbox remains unfinished, report it as unfinished rather than calling the whole scope complete. The daily roadmap is a target, not proof of achievement.

## Extension map toward the full reference

| Extension | Prerequisite | Learning outcome |
| --- | --- | --- |
| Rich TUI, steering/follow-up queues, cancellation | Stable loop/events/approval | Concurrent input and lifecycle handling |
| Docker/Modal sandbox backend | Reliable executor and file seam | Execution isolation and workspace transport |
| LSP client and diagnostics | Stable file tools | Semantic navigation and structured feedback |
| Parallel subagent fan-out | One bounded child | Concurrency limits and partial-failure aggregation |
| Opik integration | Useful local traces/evaluations | External observability and experiment comparison |
| Headless Modal deployment, webhook/cron | Bounded headless local run | Remote configuration, secrets, artifacts, triggers |
| Kitaru recording and replay | Stable execution records | Controlled experiments with explicit replay boundaries |
| Advanced automatic compaction/memory maintenance | Validated manual compaction | Context management and failure recovery |

Budget another roughly 15–30 focused hours for selected extensions, with additional time possible for unfamiliar infrastructure. Re-estimate from actual progress on Day 5. Do not attempt all cloud/runtime integrations in the final hour of Day 10.

## Progress

Day 1 started on 10 October 2026. Source inspection confirms gate.py is empty, PermissionOutcome has value/name typos, and AgentDeps still uses the temporary Literal decision type. The CLI still uses demo_gate. Event cleanup has one remaining description spelling error. A read-only compile scan found await outside an async function in files.py; factory.py also has the misspelled pydant_ai import. No day is marked complete. First implementation batch: permission modes and CLI wiring, followed by all 12 mode/kind checks and import/blocker review. Keep the detailed concept inventory and historical evidence in LEARNING_PLAN.md.

11 October update: the learner implemented the gate and corrected the outcome enum, then reported all combinations passing. Independent read-only execution verified all 12 mode/kind combinations and conservative unknown-tool handling in every mode. Day 1 remains in progress: connect the gate to AgentDeps/CLI, fix the event description spelling, and verify integrated read/error/containment behavior. The original calendar is a target; finish these acceptance checks before moving to Day 2.

Integration review, 11 October: AgentDeps now uses PermissionOutcome and PermissionGateCallback, and the event description typo is corrected. Saved cli.py still defines and passes demo_gate, so production CLI wiring remains unfinished. Isolated demo checks passed for a real default gate, missing path, outside path, and explicit denial; the denial check used a cwd that raises on filesystem resolution, verifying early return before path access. These checks manually drove non-suspending coroutines and did not verify the interactive event loop. No application files were modified.

Day 1 closed by the learner on 11 October 2026 after the final saved CLI check confirmed PermissionGate imports and default-mode wiring. Completed scope: permission mode/kind table, all 12 combinations, unknown-tool policy, shared dependency types, event spelling cleanup, and working demo containment/read/output-limit integration. The learner asked about dynamic modes; switching the shared gate's mode was explained. Policy, containment, and truncation responsibilities were clarified after the learner initially attributed path rejection to truncation. Independent explanation of that distinction can be revisited briefly on Day 2. A fresh interactive CLI run after the last wiring save was not independently verified; the earlier isolated behavior checks passed.

The learner plans to push the code themselves and continue Day 2 tomorrow, 12 October 2026. No push or scheduling action was requested of the assistant. Day 2 starts with the existing files.py syntax/import blockers, then reusable containment, numbered reads, glob/search, and exact write/edit tools with denied-operation checks. Deferred defects include await in a synchronous edit function, missing approval implementation, and the factory's pydant_ai typo; these are not completed model/tool features.

Day 2 started at the learner's request on 11 October 2026; the earlier planned continuation date is superseded. Initial source review: files.py still contains await in synchronous edit, incorrect numbered-render arguments/set/return, and invalid approval raising. approval.py is now populated, but imports decode.permissions.types while the local package is decode.permission. Today starts with an implementation summary, then repair and verify read/glob before adding grep/write/exact edit. No code edits were requested or applied by the assistant.

Day 2 implementation and verification closed on 13 October 2026. The learner implemented read/glob/literal grep/write/exact edit, shared containment and output rendering, and deferred-approval guards. Reported checks passed for numbered reads, path/glob rejections, grep evidence and invalid requests, mutation success/rejections/unchanged bytes, approval pause, and all output-limit/spill integrations. Reusable scripts are now saved as test/file_test.py and test/output_test.py. The assistant independently verified source compilation without executing file-creating tests; no live model or full deferred-resume loop has been verified. Concepts explained include RunContext, ModelRetry versus ApprovalRequired, offset/limit versus safety caps, exact-match ambiguity including overlaps, fixtures/postconditions, UTF-8 bytes, the first-long-line exception, and complete spill evidence. Independent explain-back for these Day 2 concepts remains unassessed; revisit briefly during Day 3 rather than claiming it was demonstrated. Next: fix the factory import, select/configure one supported provider/model, register tools, and drive a bounded read-only model/tool loop.

Day 3 started on 14 October 2026. Learner has no provider API key yet. Start with injected local test models: read-only registry, factory accepting a model object, and a bounded scripted run. The assistant verified Pydantic AI 2.42.0 Agent construction, registration of read/glob/grep, and output_type=[str, DeferredToolRequests] support in memory. No live calls were made, and model execution has not yet been verified. After local wiring, exercise an actual tool call with deterministic arguments, then choose/configure a live provider with the learner. Do not treat scripted TestModel output as natural-language reasoning or a completed live-model milestone.

Groq steering update, 14 October: the learner now has a Groq API key and explicitly wants to prioritize a live model run. Keep the key local; no secret value has been requested or read. Installed Groq model/provider modules are present, but the groq SDK is absent; guide the learner to install it with uv. Groq's current official production/model docs list openai/gpt-oss-20b with tool use, and native Pydantic GroqModel/GroqProvider APIs were checked in installed source and official documentation. Next is model-name configuration, session-only key entry, and a bounded live read-only runner that inspects ToolReturnPart evidence. A dedicated BYPASS dependency instance isolates this initial read-only run from unfinished approval orchestration; the registry exposes no mutation tools and the normal CLI policy remains unchanged. Live execution is not yet verified. TestModel/FunctionModel checks remain useful regression work, not reported as passed.

First live result, 14 October: learner's Groq run executed a real README read and returned a grounded project description. A trailing usage-display error remains: change result.usage().requests to result.usage.requests because usage is a property in the installed 2.42.0 source. No live call was made by the assistant. Day 3 stays in progress until remaining recovery/limit and application wiring checks are completed.

Day 3 CLI update, 14 October: learner confirmed the usage correction working and implemented Groq-backed CLI/deferred read-only approval handling. A CLI turn now fails with HTTP 413 (16,286 requested tokens versus 8,000 TPM). Current per-tool limits of 2,000 lines / 50,000 bytes allow too much content for this tier; exact triggering output is not yet known. Guide a reduction to 100 lines / 4,000 bytes and a narrow README retry. This does not establish an aggregate context budget or resolve the oversized-first-line exception. No code edits or live provider calls were made by the assistant. Day 3 remains in progress; successful CLI recovery is pending.

Subsequent CLI confirmation, 14 October: learner reports working with smaller output limits; saved values are 100 lines / 5,000 bytes. The narrow-request failure is resolved for that run. Missing-file recovery and request-limit enforcement remain to be demonstrated before Day 3 closes. Full context-budget protection remains unfinished.

Missing-file recovery, 14 October: learner reports that the absent-file request successfully falls back to a small README read. Request-limit enforcement is the remaining Day 3 acceptance exercise: a local scripted model will repeatedly request reads through run_turn, verifying the shared five-request budget across approval resumes. No result is claimed before the learner executes it.

Day 3 functional acceptance completed, 14 October: learner reports the request-limit check passed; saved as test/test_req_lim.py. Source inspection confirms the real run_turn path and assertions for five model requests and a request_limit exception. No independent execution was performed. Completed milestones: Groq-backed read-only CLI, actual tool-grounded answers, automatic read-only approval/resume, missing-file recovery, and bounded iteration across resume legs. Explain-back remains unassessed. Aggregate context-budget protection remains unfinished; output caps only mitigate the observed 413. Next is Day 4 human-approved mutations, refusal/plan-mode unchanged-file evidence, and session history.
