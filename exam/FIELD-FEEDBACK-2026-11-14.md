# Exam field feedback and next-version recommendations

Recorded **14 November 2026** against the current wrapper. **Status: findings
and recommendations, not implemented changes.** The earlier short functional
validation did not establish six-hour reliability with multiple active terminals.

## Reported experience

The user reported API/tool failures ending sessions, frequent approval prompts,
hard-to-read findings, difficulty reusing findings across challenges, and poor
Windows/Parrot clipboard transfer. API spending was reported below USD 1. The
dashboard screenshot shows USD 0.66 for its selected period; that period spans
more than one day, so it is not an isolated six-hour benchmark.

The exam screenshots also show multiple assigned subnets and explicit excluded
addresses. They are historical context, not permission or default targets for
future work. No exam questions, credentials or screenshots are reproduced here.

Exact API status codes and approval causes still require the saved exam logs.
Concurrency alone is not proof that every failure was a rate limit.

## Confirmed in the code

| Observation | Current implementation |
| --- | --- |
| No API retry | [providers.py](providers.py) and [exam_runtime.py](exam_runtime.py) set `max_retries=0`. |
| No hosting-provider failover | OpenRouter requests explicitly use `allow_fallbacks=False`. This concerns providers hosting the same model, separately from choosing a different model. |
| API failures can end the process | The normal REPL completion path does not catch and recover general transport/API exceptions. |
| Failed review becomes a human prompt | [ai_approval.py](ai_approval.py) returns false on unavailable, malformed or uncertain reviews; the executor then requests manual approval. |
| Steps lose line breaks | [exam_workflow.py](exam_workflow.py) uses `' '.join(how_found.split())`. |
| No common findings board | Each session has its own findings; there is no cross-challenge, cross-machine verified fact store. |
| No subagent coordinator | The installed 1.5.1 workflow has tools and review calls, but no parent/worker task scheduler. |

These facts explain weaknesses, not the exact cause of each exam incident.

## Recommended direction

Keep `sgpt` as the user-facing command. Use Windows as the control terminal and
SSH into Parrot for Linux work. Add reliability and shared evidence to the
existing wrapper before introducing autonomous workers.

### Recoverable sessions

- Keep the REPL alive after recoverable API errors. Show whether a job is
  running, waiting, needs input, failed, or completed.
- Add bounded retries for temporary connection errors, timeouts, rate limits
  and temporary server failures. Respect `Retry-After` where supplied.
- Save conversation/tool state after each validated event, not only after a
  whole successful turn. Preserve provider metadata and stable tool-call IDs.
- Maintain a command ledger: planned, started, completed, or uncertain. If a
  response fails after execution, resume from the recorded result. Do not replay
  completed commands. A timed-out operation may need inspection before retry.
- Handle malformed tool arguments before execution. Do not extract a convenient
  substring and run it as if it were the original valid command.
- Apply one shared concurrency budget to normal requests and approval/review
  calls. Start with two or three active requests and measure behavior under load.

### Approval workflow

- Establish the assigned scope and routine-work permissions once per session.
  Keep ordinary inspection, searches and approved evidence creation automatic.
- Distinguish technical review failures from a decision that human approval is
  actually needed. A temporary review outage should first enter bounded recovery,
  rather than immediately producing another `yes` prompt.
- Present remaining human decisions in one visible approval queue. A waiting
  job should not hide among unrelated terminal output or stall independent jobs.
- Preserve confirmation for installation, deletion and critical changes under
  the existing policy. Log the precise reason for each request. Never turn a
  human denial into permission through an alternate command or another model.

### Readable findings and a shared fact board

Keep per-challenge transcripts, scripts and results. Preserve multiline steps,
commands and evidence references instead of collapsing them into one paragraph.
For example:

```text
Flag: CONFIRMED_VALUE
How found:
1. Inspected the assigned file on the named machine.
2. Ran the recorded command; see its evidence reference.
3. Verified the returned value.
```

Add a separate shared board containing verified useful facts as well as flags:
host/service observations, relevant paths, confirmed access information, and
dependencies between challenges. Include source machine, challenge, evidence
reference and verification status. Keep conflicting or unverified claims separate.

Use one authoritative store on Parrot with transactional/locked writes and a
readable `shared-findings.md` or text export. Each session can search it and load
only relevant facts. Avoid having several machines overwrite copies of the same
text file through SCP. Sensitive evidence stays local, outside Git.

### SSH and file transfer

Use Windows OpenSSH for the Parrot terminal and SCP/SFTP for files. This avoids
depending on browser-based VM clipboard transfer. Check SSH availability and
permissions before timed practice; do not assume the next exam's account/IP.
The next kit should provide a simple two-way inbox/outbox workflow and key setup.

GUI-only Windows tools still need numbered manual instructions and a precise
description of the results to return. SSH does not provide GUI control itself.

### Availability fallback

Keep DeepSeek as the measured baseline. A backup can use the same OpenRouter
endpoint/key, avoiding an immediate requirement for another API service.

Distinguish hosting-provider failover for the same model from changing models.
Use an explicit policy for temporary technical failures. OpenRouter's generic
model fallback also covers moderation errors by default, so it should not be
enabled blindly for an availability-only policy. Show refusals instead of using
fallback as a way around them.

Test each backup's tools, history format and context limits. Keep the original
conversation and evidence. Provider-specific reasoning/signature fields must not
be forwarded blindly to an incompatible model. Log the model actually serving
the response, not only the requested primary model.

### Optional supervised workers

ShellGPT 1.5.1 has no built-in subagent manager. Custom functions can provide
delegation through our wrapper, but independent terminal chats do not coordinate
automatically. Start with a coordinator and at most two workers after the base
recovery and shared-facts design works. Give each worker a bounded objective,
scope, task ID and private evidence folder. Use the shared request budget and
fact store; prevent duplicate jobs and recursive worker spawning.

### Scope handling

Accept several explicitly assigned CIDRs plus exclusions in an attempt-specific
scope file. Share it with workers. Do not infer authorization from a subnet mask
or reuse a prior exam's network addresses. Preserve assigned public-task handling.

## Readiness checks for the next version

1. Recover from injected 429/503 responses, connection failures and timeouts
   while multiple sessions remain usable.
2. Restart after a command completes but before its next model response, and
   verify that the command is not executed twice.
3. Verify approval behavior using actual routine commands from saved transcripts,
   and distinguish the reasons for any remaining manual decisions.
4. Save and read multiline findings from both operating systems; verify shared
   facts appear without lost updates or invented verification status.
5. Transfer files in both directions through Windows-to-Parrot SSH/SCP.
6. Test backup models with preserved tool history and explicit failure categories.
7. Complete repeated six-hour rehearsals with two or three terminals, deliberate
   interruptions and known-answer tasks. Record accuracy, recovery time and human
   interruptions separately from API cost.

## References

- [ShellGPT 1.5.1 CLI source](https://raw.githubusercontent.com/TheR1D/shell_gpt/1.5.1/sgpt/app.py)
- [OpenRouter model fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks)
- [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [OpenRouter error handling](https://openrouter.ai/docs/api_reference/errors-and-debugging)
