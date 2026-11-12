# Exam ShellGPT: one command, one active model

Use **`sgpt`** on Windows or Parrot. The exam default is OpenRouter
`deepseek/deepseek-v4.1-flash-1017`; StepFun `step-5-preview` is a manual choice
for local practice. Switching changes one active configuration, not your OS
account. There is no automatic fallback between providers.

## Install or refresh after cloning

Run on the machine you want to configure, as the account that will use sgpt:

```text
git clone https://github.com/redwan-cse/ceh-lab-setup.git
cd ceh-lab-setup
```

For an existing clone, run `git pull --ff-only`. Keep the full repository:
the exam setup uses the guards in `universal` and references in `docs/ceh-tools`.
If Git is unavailable, extract the repository ZIP and enter its folder.

**Windows PowerShell:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1
```

**Parrot / Debian-based Linux, as your normal user:**

```bash
bash ./exam/setup-exam.sh
```

Paste your **OpenRouter API key at the hidden prompt**, then open a new terminal.
Setup checks Python 3.10+, the private environment (ShellGPT **1.5.1**, OpenAI
**2.54.0**, Typer **0.16.0**, Click **8.1.8**) and native collector prerequisites.
Windows uses built-in PowerShell networking commands; Linux needs Bash and
`iproute2`. Only missing prerequisites are offered for installation, with
**one consent prompt**. Declining or running noninteractively installs nothing.
Sudo, UAC or credential authentication may still require an OS prompt.

If Windows has no usable Python, the signed bootstrap installs an app-local
runtime at `%LOCALAPPDATA%\CEHLab\shellgpt-python`, without adding Python to
PATH or installing a global launcher. Existing usable Python is preferred.

Rerunning the native setup command retains the active provider, refreshes managed
runtime/reference files and can recover missing private Python components.
Linux previews prerequisite installation and stops if it would upgrade or
remove an existing package; it does not run an apt update/upgrade. It does not force-reinstall
a healthy environment, install CEH tool bundles, upgrade/remove OS packages,
or change SSH, firewall, Defender, IP or DNS settings. Downloads, permissions,
unsupported OS versions or unavailable prerequisites can stop setup clearly;
existing evidence is preserved. Do not assume a fresh machine is ready merely
because its OS name matches a tested machine.

## Check and switch the active model

```text
sgpt --version
sgpt --model-info
```

`--model-info` is this kit's local metadata helper. It shows the **actual
configured provider, model and endpoint**, with no paid request or key
disclosure. Asking the model to identify
itself is not a reliable configuration check.

Choose one of these commands from the repository root on Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 deepseek
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 stepfun
```

Or on Linux:

```bash
bash ./exam/switch-model.sh deepseek
bash ./exam/switch-model.sh stepfun
```

The switch updates the **endpoint, model and matching key together**, without
installing packages or calling an API. If the provider has no saved key, it
asks securely; cancellation keeps the active selection. Then keep using `sgpt`
for every task. StepFun uses `https://api.stepfun.ai/step_plan/v1`; DeepSeek
uses `https://openrouter.ai/api/v1`.

Each OS account has one active configuration and a separate protected key vault:

| File under your home directory | Purpose |
|---|---|
| `.config/shell_gpt_exam/.sgptrc` | Active endpoint/model and `OPENAI_API_KEY` |
| `.config/shell_gpt_exam/provider-keys.json` | Separate provider keys for later switches |

The vault holds credentials, not multiple user profiles. Keys are plaintext
protected by current-user/SYSTEM ACLs on Windows, or directory mode 700/file
mode 600 on Linux. Keep them out of Git, screenshots and command arguments.
Keys never cross provider endpoints. Chats and caches remain isolated by
provider internally, so switching does not send another provider's history.
Legacy shared chats remain on disk and are not automatically imported.

To enter or replace the active key later:

```text
python ./exam/setup_exam.py --key-only
```

Use `python3` on Linux. To store another provider's key without switching,
append `--provider stepfun` or `--provider openrouter-deepseek`. Enter retains
a saved key. Setup also accepts `-ReuseStepFunKey` on Windows or
`--reuse-stepfun-key` on Linux to explicitly import the same account's existing
StepFun key after checking its endpoint. `-NoKeyPrompt` / `--no-key-prompt`
skips key entry. A host-only `.openrouter-api-key` is not deployed to exam VMs.

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

Index your actual tools directory without executing its files:

```powershell
sgpt --init-lab --tools-path C:\CEH-Tools
```

```bash
sgpt --init-lab --tools-path /mnt/ceh-tools
```

For GUI tasks, sgpt locates an indexed tool or asks where it is, supplies manual
steps and requests your observations. It cannot see GUI results automatically.

## Reset, remove or troubleshoot

Preview first; `--clear` removes only known generated log/state filenames.
Nonempty findings, keys and unrelated files survive. Setup never clears logs.

```text
python ./exam/reset_exam_logs.py
python ./exam/reset_exam_logs.py --clear
```

Use `python3` on Linux. To remove the exam installation as the same user:

```text
python ./exam/uninstall_exam.py --dry-run
python ./exam/uninstall_exam.py
```

Removal deletes the dedicated environment, keys, configuration and private
state. Desktop evidence and the legacy universal StepFun installation remain.
`--keep-config` intentionally retains keys/history. Open a new terminal afterward.

If `python` is not on PATH because Windows used that app-local bootstrap, run
the same removal command with its explicit executable:

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\uninstall_exam.py --dry-run
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\uninstall_exam.py
```

Python itself is retained, as with the existing system Python prerequisite.

For 401/403/404/429, check the selected provider's key, model access, network,
quota and billing. `OTHER` means an unspecified provider reason. Preserve the
timestamp, configured model/endpoint and harmless reproduction for support;
exclude the key. Do not disguise a request or disable safety settings. Remote
availability and exam readiness cannot be guaranteed by setup alone.
