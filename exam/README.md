# Exam ShellGPT: one command, one active model

Use **`sgpt`** on Windows or Parrot. Fresh exam installations default to
OpenRouter `deepseek/deepseek-v4.1-flash-1017`; StepFun `step-5-preview` is a
manual alternative for local practice. Switching changes one active
configuration, not your OS account. There is no automatic provider fallback.

The [main README](../README.md) is the one-stop setup guide, ordered Parrot,
Windows, Android, then normal local lab. This page keeps the detailed runtime,
evidence and troubleshooting rules. Keep the full repository when installing.

## Parrot exam setup

Follow the [complete Parrot instructions](../README.md#exam-parrot) for setup,
API keys, use, model switching and removal. Run as your assigned normal account;
our local test account is `attacker`. Check `whoami` first.

From the repository root:

```bash
bash ./exam/setup-exam.sh
```

Paste the OpenRouter key at the hidden prompt. Existing active providers are
retained on reruns. Missing Python/venv or `iproute2` prerequisites require one
consent; sudo authentication can ask separately. Apt simulation rejects
upgrades/removals, and no apt update/upgrade is run. Python packages stay in
the dedicated environment; a healthy environment is not force-reinstalled.

After opening a new terminal:

```bash
sgpt --model-info
sgpt "init the machine"
sgpt --tool-help "nmap"
```

If indexing CEH files, replace the path with the actual provided tools folder:

```bash
sgpt --init-lab --tools-path /PATH/TO/CEH_TOOLS
```

Manual switching, without reinstalling or making an API request:

```bash
bash ./exam/switch-model.sh stepfun
bash ./exam/switch-model.sh deepseek
```

To enter/replace the active key later, preview/reset generated logs, or remove
this account's exam installation:

```bash
python3 ./exam/setup_exam.py --key-only
python3 ./exam/reset_exam_logs.py
# Only if you intend to clear the previewed generated logs:
python3 ./exam/reset_exam_logs.py --clear
python3 ./exam/uninstall_exam.py --dry-run
python3 ./exam/uninstall_exam.py
```

## Windows exam setup

Follow the [complete Windows instructions](../README.md#exam-windows). Use the
account that will run `sgpt`; check `whoami` first. From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1
```

Paste the OpenRouter key at the hidden prompt. Reruns retain the active
provider. Missing prerequisites require one consent; OS authentication may
ask separately. Existing usable Python is preferred. Otherwise signed Python
is installed at `%LOCALAPPDATA%\CEHLab\shellgpt-python`, without adding Python
to PATH or installing a global launcher. The installer does not change SSH,
Defender, firewalls, addresses or DNS, or install CEH tool bundles.

After opening a new terminal:

```powershell
sgpt --model-info
sgpt "init the machine"
sgpt --tool-help "nmap"
```

To index CEH files, replace the example with the actual provided tools folder:

```powershell
sgpt --init-lab --tools-path 'C:\PATH\TO\CEH_TOOLS'
```

Manual switching, without reinstalling or making an API request:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 stepfun
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 deepseek
```

With existing system Python, key entry, log reset and removal use:

```powershell
python .\exam\setup_exam.py --key-only
python .\exam\reset_exam_logs.py
# Only if you intend to clear the previewed generated logs:
python .\exam\reset_exam_logs.py --clear
python .\exam\uninstall_exam.py --dry-run
python .\exam\uninstall_exam.py
```

If `python` is not on PATH, use the app-local bootstrap executable instead:

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\setup_exam.py --key-only
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\reset_exam_logs.py
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\uninstall_exam.py --dry-run
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\uninstall_exam.py
```

## Android exam target

Follow the [Android connection and evidence instructions](../README.md#exam-android-target)
after setting up Parrot or Windows as the controller. ShellGPT runs on the
controller, not on the Android target. Use the exam's assigned IP/ADB port;
do not apply our local Hyper-V addressing to an exam machine. Mobile workflows
are in the [ADB/APKTool reference](../docs/ceh-tools/mobile-and-wireless.md).

## Active configuration and API keys

Each OS account has one active configuration and a separate protected key vault:

| File under your home directory | Purpose |
|---|---|
| `.config/shell_gpt_exam/.sgptrc` | Active endpoint/model and `OPENAI_API_KEY` |
| `.config/shell_gpt_exam/provider-keys.json` | Matching provider keys for later switches |

Paste keys at the hidden prompt, never into command arguments or Git. These
are plaintext files protected by current-user/SYSTEM ACLs on Windows or file
mode 600/directory mode 700 on Linux. The vault is not multiple user profiles.
Provider histories/caches remain isolated internally, including after switching.
Legacy shared chats are retained but not automatically imported.

A switch updates endpoint, model and matching key together. Missing keys are
requested securely; cancellation keeps the active selection. StepFun uses
`https://api.stepfun.ai/step_plan/v1`; DeepSeek uses `https://openrouter.ai/api/v1`.
`sgpt --model-info` is this kit's local metadata helper: it reads the actual
configuration without a paid call or key disclosure. A model's self-description
is not a reliable identity check.

Key entry accepts `--provider stepfun` or `--provider openrouter-deepseek` to
save another provider's key without switching. Enter retains a saved key.
Setup accepts `-ReuseStepFunKey` on Windows or `--reuse-stepfun-key` on Linux to
import the same account's existing StepFun key after checking its endpoint.
`-NoKeyPrompt` / `--no-key-prompt` skips entry. A host-only `.openrouter-api-key`
is ignored by Git and is not pulled into an exam machine.

## Reasoning settings and earlier tests

Official ShellGPT 1.5.1 has no native high/max reasoning-effort option in
[app.py](https://github.com/TheR1D/shell_gpt/blob/1.5.1/sgpt/app.py) or
[handler.py](https://github.com/TheR1D/shell_gpt/blob/1.5.1/sgpt/handlers/handler.py).
The current exam flow removes the earlier custom forced-high adapter settings
and lets the provider choose its reasoning defaults. It does not force high
or max in tests. A default DeepSeek initialization already reported 397
reasoning tokens; that shows reasoning was used in that request, not a speed
or quality guarantee.

[COMPARISON.md](COMPARISON.md) and [LAB-CHALLENGES.md](LAB-CHALLENGES.md) retain
historical measurements and their earlier custom settings. Their timings do
not establish performance for the current provider-default setup. Optional
Google-only Flash/Carbon setup remains available through the installer's
`-Provider gemini-mix` / `--provider gemini-mix` option; the mix uses Flash to
execute and Carbon to review each completed task, without cross-provider fallback.

## Initialize and inspect safely

```text
sgpt "init the machine"
sgpt --shell "Show my current directory"
sgpt --repl work "Help me inspect this machine"
```

Initialization runs the native `collect-host-windows.ps1` or
`collect-host-parrot.sh` collector. Its five checks cover **host addresses,
routes, DNS, cached neighbors and capabilities**. This is passive local
collection, followed by a short model review using provider defaults. It does
not scan neighbors or infer their OS/online status. Missing tools, API quota,
Internet access or permissions can stop work; failures are reported and
collected evidence is retained.

Skip the paid review explicitly:

```text
sgpt --init-lab --local-only
```

Active discovery requires your explicitly authorized IPv4 CIDR, /24 or smaller:

```text
sgpt --init-lab --scope YOUR_AUTHORIZED_CIDR --discover
```

This probes TCP 22, 80, 443, 445, 3389 and 5555 within that supplied range only.
Cached neighbors do not prove reachability; timeouts do not prove a host is
offline. A subnet mask does not establish authorization.

Recognized inspection commands run automatically. Deletion, installation,
writes, scripts, sudo, command chains and unknown commands require approval
of the exact command. Refusal, missing input or policy failure prevents
execution. This guard is an approval aid, not an OS sandbox. Tool continuations
stop after eight API turns; requests have a 90-second timeout and no automatic
retries. Empty responses or exhausted limits produce an incomplete-task message.

## Markdown evidence by IP

The Desktop has two readable evidence files per IP:

```text
Desktop/CEH-Exam/10.10.10.13/
    terminal.md
    findings.txt
```

That IP is an example, not a configured address. The default folder uses the
local IPv4 selected by the routing table. On multihomed machines, select the
intended filing IP explicitly. For observations about another machine:

```text
sgpt --target-ip 10.10.10.9 "Summarize the observations I provide about this machine"
```

`--target-ip` selects a folder only; it does not connect, authorize a scan or
redirect local commands. Initialize without it to inventory the local machine.
Folders belong to each VM/account and are not automatically synced.

`terminal.md` records prompts, commands, actual output, approvals, refusals,
answers, reviews, API usage and timing. It captures sgpt activity, not other
terminals or GUI windows. Known saved keys are redacted; other sensitive
evidence can remain. ANSI codes are removed; indented terminal lines preserve
spacing without turning captured text into Markdown instructions or links.
Old `terminal.txt` files remain historical; new output uses `terminal.md`.

`findings.txt` contains only `Flag:` and `How found:` blocks backed by actual
command output or your reported observations. AI text alone is insufficient.
After observing a GUI result, for example:

```text
sgpt --target-ip 10.10.10.9 "I found FLAG_VALUE in the GUI using these steps: ... Save the flag and how it was found."
```

Small summaries, tool indexes and output byte offsets live under
`.config/shell_gpt_exam/state/<IP>`. Full output is stored once in the transcript;
no duplicate network-dump/review files are created on the Desktop. Old indexed
command evidence still works. [LAB-RULES.md](LAB-RULES.md) supplies static rules;
observed data stays lower-trust context instead of accumulating in chat history.

## Find tools and task guidance

Setup copies the [task-oriented tool guides](../docs/ceh-tools/README.md)
locally. Search without a paid request:

```text
sgpt --tool-help "nmap"
sgpt --tool-help "hashing"
```

During a task, `find_ceh_reference` retrieves bounded excerpts;
`find_ceh_tools` separately checks indexed file paths. Neither installs tools
or proves runtime readiness. Prefer existing, OS-compatible tools and ask
before installing or making critical configuration changes.

Index actual tool files using the path example in your OS section above.

For GUI tasks, sgpt locates an indexed tool or asks where it is, supplies manual
steps and requests your observations. It cannot see GUI results automatically.

## Reset, remove or troubleshoot

Use the reset/removal commands grouped under your OS above. Reset previews
known generated filenames first; `--clear` removes only those files. Nonempty
findings, keys and unrelated files survive. Setup never clears logs.

Removal deletes the dedicated exam environment, keys, configuration and private
state. Desktop evidence, Python itself and the legacy universal StepFun
installation remain. `--keep-config` intentionally retains keys/history.
Open a new terminal after removal.

For 401/403/404/429, check the selected provider's key, model access, network,
quota and billing. `OTHER` means an unspecified provider reason. Preserve the
timestamp, configured model/endpoint and harmless reproduction for support;
exclude the key. Do not disguise a request or disable safety settings. Remote
availability and exam readiness cannot be guaranteed by setup alone.
