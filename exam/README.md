# Exam ShellGPT: one command, one active model

For day-to-day usage, see the [sgpt command reference](SGPT-COMMANDS.md), covering
standard options, custom exam commands, parallel sessions and model switching.

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

The working scope includes the machines, services and websites assigned to
your CEH lab session, including public URLs/domains.
You do not need to repeat an authorization statement or provide a tools root
for each task. If a network operation needs an unknown target/range, provide
the assigned URL/domain/IP/range in chat. Reuse a target already supplied in
the task; no second scope confirmation is needed for routine read-only work.

Passive public sources (search results, WHOIS/RDAP, certificate transparency,
passive DNS and public documents) are allowed. Ordinary public-page/header
retrieval and normal DNS queries are also allowed; these make network requests.
They do not require a private CIDR, lab-only DNS, or initialization first.
The local-only startup collector does not limit later research to local hosts.
Active tests remain limited to the assigned task targets; passive-source
permission does not expand them to unrelated or discovered infrastructure.

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
runtime and OS. Edits create a new version. Each new version receives approval
review; clear routine code can be AI-approved, protected or uncertain code
needs a human decision. An unchanged approved version can rerun in that process.
Approvals are not retained across processes. Results are logged, and sgpt
inspects them before deciding what to do next. This is not an OS sandbox.

Output is printed without live redraw so approval prompts remain visible.
Type `yes` at the approval prompt to approve the displayed version/command.
Declining stops that task's remaining actions and API calls, while the chat
remains available. Piped/closed input cannot provide HUMAN approval; automatic
routine approvals can still run without a terminal. For remote human approval,
connect with `ssh -tt`.

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

Recognized routine work runs automatically. On Parrot this includes literal
`cd` plus read-only command chains, grep/sort pipelines, ordinary HTTP(S)
GET/HEAD downloads with curl, and new/append result files inside the exam folder.
The planner validates the entire chain before running any part and executes
literal argument lists without a shell. On Windows, literal read-only pipelines
and statements, Select-String, Get-FileHash, Resolve-DnsName and GET/HEAD
Invoke-WebRequest are recognised; Out-File can create new exam result files.
Use explicit `-Uri`, `-OutFile` and `-FilePath` parameters on Windows.

Downloads ignore curl configuration files and unsupported upload/code options.
New output files must stay inside the exam folder; existing evidence is not
automatically overwritten. A supported append can add to an ordinary report.
The main terminal/findings journals remain managed by the workflow tools.
Other command forms and owned scripts now use the AI reviewer described below.
Deletion, installation, sudo, system changes and uncertain decisions require
human approval of the exact command/version. Refusal, unavailable required
human input or policy failure prevents
execution. This guard is an approval aid, not an OS sandbox. Each request has
a 90-second timeout and no automatic retries. Empty responses produce an
incomplete-task message.

### AI approve for me

The default is layered approval: known literal routine forms run immediately;
otherwise the **same active model and endpoint** review the exact command.
For a generated/edited script, the reviewer also sees its owned, hash-verified
source before execution. Clear routine work is approved without typing `yes`.
This covers compound `find`, `file`, Nmap/report commands and redirections such
as `2>/dev/null` or `2>&1`, even when the literal planner does not support them.
The existing shell/interpreter executes the reviewed operation normally.

The reviewer receives command text, owned script source, task context and paths;
it does not read existing task files. Decisions and API usage are logged. It
uses the current model/key, with no second provider or batch inference. These
are additional billable calls; the forty-round limit counts main-agent rounds.
Successful decisions are cached for the same command/source/task in that process.
Output paths are checked locally on every approval, including cached decisions.

Installation, deletion, privilege escalation and critical changes stay under
human control. Uncertain/invalid/provider-failed reviews defer to the existing
human prompt. A provider refusal never triggers another provider or a retry.
Only a human can supply that remaining approval; closed input cannot do so.
Declining still stops the task. Each terminal keeps its own approvals and can
run independently. Prefer distinct result filenames for parallel tasks.
Short local locks protect shared transcript offsets and the owned-script index;
state JSON is replaced atomically so concurrent terminals do not read partial data.

AI review is an approval aid, not an OS sandbox: approved commands/scripts run
with the account's permissions. To disable AI approval for one invocation while
retaining the literal routine fast path:

```text
sgpt --manual-approval "Your task"
```

### Longer tasks and continuation

The default budget is **40 main-agent rounds per task**, rather than eight;
AI approval checks are additional calls.
One round can contain several tool calls. At the budget boundary an interactive
session asks:

```text
Completed 40 model/tool rounds; current results are retained. Continue for up to 40 more paid API rounds? [y/N]
```

Type `yes` to continue with the same conversation and actual tool results;
successful commands are not automatically replayed. Each extra block needs a
new confirmation and incurs normal API charges. Command/script approvals still
apply. Declining preserves evidence and keeps an interactive chat available;
you can ask it to continue later in that chat. Closed/piped input stops without
another API call and returns an incomplete-task status. Provider refusals/errors
never use this continuation prompt or trigger an automatic retry.

Choose a different block size (1–100) for one invocation:

```text
sgpt --tool-rounds 60 "Complete this task using existing results"
```

The current process keeps its conversation in memory. If an earlier one-shot
process has already exited, start a new request naming its saved reports or
use a saved `--chat` conversation; it cannot recover unsaved process memory.

## Markdown evidence by IP

Every sgpt process creates a unique session folder under the filing IP. Its
commands/output and confirmed findings stay together, separate from other
terminals and challenges:

```text
Desktop/CEH-Exam/10.10.10.13/
    sessions/
        challenge-5_<UTC-time>_<unique-id>/
            terminal.md
            findings.txt
            scripts/                 (only if needed)
        challenge-6_<UTC-time>_<unique-id>/
            terminal.md
            findings.txt
```

Optional labels work the same in PowerShell and Bash:

```text
sgpt --challenge 5 "Work on this challenge"
sgpt --challenge 6 --repl challenge6
```

If the initial prompt says `challenge 5`, that number labels the folder
automatically. Otherwise the folder starts with `session_`; no question is
asked. Starting two sessions with the same label still creates distinct folders.
The label is chosen when the process starts. Use another process for a separate
challenge; an ongoing chat stays in its original folder. One-shot calls also
get separate folders. To resume later, name the earlier report paths or use your
saved `--chat` conversation; new output is saved in the new session.

That IP is an example, not a configured address. The default folder uses the
local IPv4 selected by the routing table. On multihomed machines, select the
intended filing IP explicitly.

All final result files belong inside this exam folder: tool lists, reports,
scan exports, extracted results, hashes, decoded data and captures. A tools
directory or share is an input location. Every model request includes the exact
session output paths; child commands can also use `$env:CEH_EXAM_DIR` in
PowerShell or `"$CEH_EXAM_DIR"` in Bash. sgpt must verify each saved file and
report its path. Existing evidence is preserved. Final chat text already goes
to `terminal.md`, so a separate duplicate summary file is not needed for every
reply. This is a workflow rule, not a filesystem sandbox; review output paths
when approving commands or scripts.

For observations about another machine:

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
Old top-level `terminal.md`, `terminal.txt` and findings remain untouched.

Normal terminal output shows the conversation, commands, actual results,
required approvals and errors. API usage, model/timing records and routine
approval status are still saved in that session's transcript but are hidden
from the console. This changes display only; provider-default reasoning and
stored tool metadata are preserved, including in `--shell` mode. For diagnostics:

```text
sgpt --verbose "Your task"
```

`findings.txt` contains only `Flag:` and `How found:` blocks backed by actual
command output or your reported observations. AI text alone is insufficient.
After observing a GUI result, for example:

```text
sgpt --target-ip 10.10.10.9 "I found FLAG_VALUE in the GUI using these steps: ... Save the flag and how it was found."
```

Host facts and optional tool settings remain shared under
`.config/shell_gpt_exam/state/<IP>`. Session status, owned-script indexes and
command-output offsets live in its `sessions/<session>/` subfolder. Findings
use that session's command evidence or observations you explicitly supply;
another session's output is not silently treated as current evidence. Full
output is stored once in the transcript. [LAB-RULES.md](LAB-RULES.md) supplies static rules;
observed data stays lower-trust context instead of accumulating in chat history.

### Another machine or a GUI-only tool

When a required check belongs on another assigned Windows/Server/Parrot/Android
machine, sgpt asks you to handle the handoff. It provides the destination
machine/IP and OS if known, the objective and verified context, a copyable
request for sgpt there, and the exact fields/output to return. Install sgpt on
that machine if needed, run that part, then paste the results into the original
chat with the source machine. It can continue independent local checks while
waiting. It does not assume remote access or automatically sync sessions.

For a GUI-only tool, it gives short numbered steps, including what to open,
options/fields to use and which results to copy back. A particular missing tool
path may be requested when needed; a global tools folder remains optional.
Reported GUI/remote observations are identified as user-reported, never as
commands executed here. Confirmed findings still contain only the flag and how
it was found, including the source machine/manual step when relevant.

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

### Windows: sgpt is not recognized

This means the terminal cannot locate the launcher; it does not establish that
the provider key or Python configuration is missing. Setup saves the per-user
PATH, broadcasts an environment-change notification to the desktop and checks
the launcher. A terminal opened from an older CMD/PowerShell or a lab launcher
can still inherit a stale PATH. A child installer cannot rewrite its parent's
environment.

In the same PowerShell window, run (also works with older installs and a
restricted script execution policy):

```powershell
$env:Path = "$env:LOCALAPPDATA\CEHLab\shellgpt-exam\bin;$env:Path"
sgpt --model-info
```

Or bypass PATH entirely, including from a terminal with a stale environment:

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-exam\bin\sgpt.cmd" --model-info
```

CMD equivalent:

```bat
"%LOCALAPPDATA%\CEHLab\shellgpt-exam\bin\sgpt.cmd" --model-info
```

If the launcher itself is missing, confirm `whoami` matches the account used
for setup, then rerun the complete OS installer from the updated repository.
Capture its output if it stops. Keys remain per-user; do not expose them in
diagnostic screenshots.

### Reset, removal and provider troubleshooting

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
