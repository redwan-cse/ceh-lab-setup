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
Old Python (including 3.8) or missing `ensurepip` uses a private Python 3.12
download through a pinned, checksum-verified uv bootstrap. This avoids stale
Python/venv APT packages without changing the distribution's Python or repositories.

After opening a new terminal:

```bash
sgpt --model-info
sgpt "init the machine"
sgpt --tool-help "nmap"
```

Optional only: if you want to index a custom folder, replace the path below.
Normal Parrot tools and Desktop wordlists do not require this step:

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
"$HOME/.local/share/shellgpt-exam/venv/bin/python" ./exam/setup_exam.py --key-only
"$HOME/.local/share/shellgpt-exam/venv/bin/python" ./exam/reset_exam_logs.py
# Only if you intend to clear the previewed generated logs:
"$HOME/.local/share/shellgpt-exam/venv/bin/python" ./exam/reset_exam_logs.py --clear
python3 ./exam/uninstall_exam.py --dry-run
python3 ./exam/uninstall_exam.py
```

Use system Python for removal only if it is 3.10+. If setup had to bootstrap
Python for an old cloud image, select that cached interpreter (no download):

```bash
task_python="$(bash ./exam/bootstrap-python-linux.sh --find)"
"$task_python" ./exam/uninstall_exam.py --dry-run
"$task_python" ./exam/uninstall_exam.py
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

Optional only: to index CEH files, replace the example with the actual provided
tools folder. A folder is not required to initialize or start a task:

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

The working scope is the machines/resources assigned to your CEH lab session.
You do not need to repeat an authorization statement or provide a tools root
for each task. If a network operation needs an unknown target/range, provide
the assigned IP/CIDR in chat. This does not authorize unrelated Internet assets.

## Normal chat, optional paths and scripts

Start an interactive conversation with `sgpt` alone, or use the native
`sgpt --repl work` to choose a chat name. Type the task and follow-up messages
at that prompt; Ctrl+C stops it. `sgpt "task"` remains a one-shot request.

The normal workflow is direct commands: run a command, inspect actual output,
then choose the next command. Scripts are created only when required or
requested. A GUI-only task gets a manual procedure when terminal execution
cannot perform it.

A custom tools path is optional on both platforms. Parrot lookup prefers
installed PATH commands, then bounded Desktop folders and relevant standard
wordlist locations. Files in the current working folder are checked too.
Desktop names vary; no CEH share is assumed or required.
On Windows, you can provide a CEH tool folder, script, executable or wordlist
when a particular task needs it. Type it as an ordinary chat message:

```text
Use ~/Desktop/MyWordlists only when this task needs a wordlist.
Use C:\Users\Administrator\Desktop\Tools for this task.
```

Use the example matching your OS and replace it with a real path. There is no
separate path dialog. `set_tools_path` remembers an explicitly supplied path;
it never executes files. The optional CLI form is `sgpt --tools-path "PATH"`.
Missing paths are nonfatal; sgpt continues with available tools and asks only
for a particular missing file if the task cannot otherwise proceed.

`sgpt "task"` uses the command/output/action loop; `--shell` and `--chat` are
optional stock modes, not prerequisites for execution. For example:

```text
sgpt "Calculate SHA256 for the file sample.txt in the current folder"
```

### Existing ShellGPT installations

Run the same OS setup script after `git pull --ff-only` to install or repair
this private ShellGPT copy. Reinstallation is supported; reruns retain the
active provider, saved keys, Desktop evidence and findings. A launcher in this
setup's per-user command location is moved to a unique `sgpt.before-exam-*`
(Windows: `sgpt.cmd.before-exam-*`) backup before replacement. A pipx symlink
is moved as a link, leaving its package unchanged. The selected backup is
recorded privately in `cli-backup.json` and restored on uninstall. Other
system installations and unrelated aliases are preserved.

Open a new terminal and run `sgpt --model-info` to verify the active endpoint
and model. A shell alias/function named `sgpt` can take precedence over PATH;
check `type -a sgpt` on Parrot or `Get-Command sgpt -All` on Windows if the old
command still runs. Remove only your conflicting alias/function, then reopen
the terminal. Stop an existing sgpt chat before updating its runtime.

When a script is needed, its source and numbered versions stay under
`Desktop/CEH-Exam/<IP>/scripts/`, for example `scripts_check_1.py`,
`scripts_check_2.py`, or `.sh`, `.ps1`, `.bat`/`.cmd` according to the installed
runtime and OS. Edits create a new version. Each new version requires visible
approval; an unchanged approved version can rerun within that chat process.
Approvals are not retained across processes. Results are logged, and sgpt
inspects them before deciding what to do next. This is not an OS sandbox.

Output is printed without live redraw so approval prompts remain visible.
Type `yes` at the approval prompt to approve the displayed version/command.
Declining stops that task's remaining actions and API calls, while the chat
remains available. Piped/closed input cannot approve commands; for remote
interactive use, connect with `ssh -tt`.

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

Custom indexing is optional. `find_ceh_tools` also resolves PATH commands and
performs bounded Desktop/wordlist lookup without any catalog.

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

For old Parrot APT `404 Not Found` errors requesting `python3.8-venv`, pull the
updated kit and rerun `bash ./exam/setup-exam.sh`. The installer checks the
Python version before selecting dependencies and uses the private Python
fallback; it does not try to repair EOL distribution repositories. GitHub
release downloads and PyPI must be reachable. [Astral's Python management
documentation](https://docs.astral.sh/uv/guides/install-python/) describes the
managed Python distributions used by this fallback.
