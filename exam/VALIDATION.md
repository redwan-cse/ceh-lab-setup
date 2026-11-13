# Windows and Parrot validation

Checked on **13 November 2026**. No unresolved sgpt failure was found in the
checks below. This validates the current installed setup and these two VMs;
it is not a guarantee about every future cloud image, GUI tool or provider outage.

## Machines and active setup

| Item | Parrot | Windows Server 2022 |
| --- | --- | --- |
| Account / address | `attacker` / `10.10.10.13` | `Administrator` / `10.10.10.22` |
| OS | Parrot Security 7.4 | Windows build 20348 |
| Private Python observed | 3.13.5 | 3.14.10 |
| ShellGPT | 1.5.1 | 1.5.1 |
| OpenAI client / Typer / Click | 2.54.0 / 0.16.0 / 8.1.8 | 2.54.0 / 0.16.0 / 8.1.8 |
| Active model | `deepseek/deepseek-v4.1-flash-1017` | Same |
| Endpoint | OpenRouter `/api/v1` | Same |
| Default after verification | DeepSeek | DeepSeek |

Live inference used the normal model, with no batch inference or provider
fallback. The model-switcher round trip made no API requests. No new CEH
software was installed and no network/security settings were changed.

## Results

| Function | Parrot | Windows |
| --- | --- | --- |
| Pinned dependencies and startup prerequisites | Pass | Pass |
| `--version`, `--help`, `--model-info` | Pass | Pass |
| Local Nmap, hashing and TShark reference searches | Pass | Pass |
| Local-only native initialization: all five checks | Pass | Pass |
| Initialization with model review | Pass | Pass |
| Explicit discovery of the other VM, limited to its `/32` address | Pass | Pass |
| Plain text completion | Pass | Pass |
| `--shell` with actual local command execution | Pass | Pass |
| Normal sgpt tool execution and actual output | Pass | Pass |
| AI approval of a compound inspection command, without typing yes | Pass | Pass |
| SHA256 result compared with an independently computed fixture hash | Pass | Pass |
| Two concurrent command sessions with separate evidence | Pass | Pass |
| Quiet console with API/status records retained in Markdown | Pass | Pass |
| Owned Python script creation, execution, edit and numbered second version | Pass | Pass |
| Confirmed synthetic finding saved in its own session | Pass | Pass |
| Closed input denies deletion; owned test file stays unchanged | Pass | Pass |
| Missing optional tools path is nonfatal | Pass | Pass |
| Named REPL reopens tool-call history and remembers earlier results | Pass | Pass |
| Follow-up messages in that REPL and clean `exit()` | Pass | Pass |
| Code generation and command explanation without execution | Pass | Pass |
| Named one-shot chat persistence, listing and local display | Pass | Pass |
| Long-chat cache keeps complete tool exchanges | Pass | Pass |
| DeepSeek → StepFun → DeepSeek configuration switch; keys preserved | Pass | Pass |
| Cross-machine handoff and GUI procedure response | Pass | Pass |
| Installed runtime matches maintained sources; known-key scan | Pass | Pass |

The peer discovery targets were only `10.10.10.22/32` from Parrot and
`10.10.10.13/32` from Windows. The handoff/GUI check verified generated
instructions; it did not operate a GUI application.

Automated results:

- **Exam suite:** 176 tests per VM; no failures. Parrot skipped 12 tests and
  Windows skipped 20 tests for the other platform or unavailable fixture features.
- **Native command guards:** 10 tests per VM; no failures.
- Offline fixtures also cover malformed tool arguments, provider failures and
  refusals, continuation, installation/deletion approval rules, script ownership,
  setup/repair, PATH activation, key handling and removal/reset behavior.
  Real installed environments were not uninstalled for these tests.

Synthetic acceptance results are filed under
`Desktop/CEH-Exam/127.0.0.1/sessions/challenge-validation-*`. Here `127.0.0.1`
is a filing label only; commands still execute on the current VM. Synthetic
findings in those folders are verification fixtures, not exam answers. Existing
exam evidence and the user's saved conversations were preserved.

## Fixes made during this audit

The old live verifier expected the `Automatically running` banner, which quiet
mode intentionally hides. It could report failure even after a command exited
successfully. The verifier now checks command execution, exit status and expected
output through the installed sgpt launcher. Its regression tests also reject
model text that claims success without a recorded command.

The upstream `--show-chat` path could display history and then continue into an
empty model request. Setup now patches it to return immediately after display.
The real-CLI regression checks that showing a saved tool-call chat makes no API
request, and the installer patch is checked for repeatability.

Upstream's fixed-size cache could also start with a tool result after cutting
away its assistant call. The runtime now retains whole user turns. The latest
long turn stays complete even if it exceeds the cache's target message count;
older complete turns may be pruned. A partial prefix in an older cache is
excluded from the request/display copy without rewriting the disk file on read.
Full terminal transcripts remain available for earlier evidence.

The saved-chat `KeyError` fix was checked again: tool-only messages remain in
the API history, while their display no longer assumes a text `content` field.

## Repeat the small live smoke check

From the repository root after setup and key entry. These three checks make
billable API requests, inspect only the local machine and stop on failure.
They do not install software or clear evidence.

**Parrot/Linux:**

```bash
"$HOME/.local/share/shellgpt-exam/venv/bin/python" ./exam/verify_exam.py
```

**Windows PowerShell:**

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-exam\venv\Scripts\python.exe" .\exam\verify_exam.py
```

Expect `PASS: live check text`, `PASS: live check shell` and
`PASS: live check tool`. Evidence goes to a new `validation-smoke` session
under the filing address `127.0.0.1`.

For normal lab work, continue with:

```text
sgpt --challenge 1 --repl challenge1
```

[Command reference](SGPT-COMMANDS.md) · [Setup and troubleshooting](README.md)

Audit transport note: direct SSH from the physical host to Server 2022 timed
out during the audit. Windows checks used Parrot as an SSH jump host. This
transport issue was separate from the guest's successful sgpt checks; network
and firewall configuration was left unchanged.
