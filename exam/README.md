# Exam ShellGPT: StepFun first, optional Gemini review

**Recommended default: StepFun `step-5-preview`, high reasoning.** Both profiles
passed all six matched local cases. StepFun used fewer requests and finished
faster. See [measured results](COMPARISON.md). Carbon's earlier direct command
failures remain unresolved; the mix uses **Flash to execute and Carbon to
review every completed task**, including each REPL turn.

Choose **one provider at a time**. There is no automatic switching between
Google, StepFun or OpenRouter. Flash and Carbon in the mix both use Google.

## Install after cloning

Run as the account that will use sgpt. Internet access to Python/PyPI and the
selected provider is required. No IP/DNS, SSH, firewall or Defender settings
are changed. Setup has no hardcoded lab IPs.

```text
git clone https://github.com/redwan-cse/ceh-lab-setup.git
cd ceh-lab-setup
```

For an existing clone, use `git pull --ff-only`. Keep the entire repository:
the exam installer reuses the command guards in `universal`.

**Windows PowerShell — StepFun:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1
```

**Parrot / Debian-based Linux — StepFun, as your normal user:**

```bash
bash ./exam/setup-exam.sh --provider stepfun
```

Paste your **StepFun API key at the hidden prompt**, then open a new terminal.
ShellGPT 1.5.1 is pinned in its own environment. Windows reuses Python 3.10+ or
installs signed Python 3.14.10 for the current user. Linux uses sudo only for
missing Python/venv prerequisites. Other distributions need their own
prerequisites. Existing universal StepFun packages/configuration are retained.

**To install/select the Gemini mix instead:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1 -Provider gemini-mix
```

```bash
bash ./exam/setup-exam.sh --provider gemini-mix
```

Paste a **Google AI Studio / Gemini API key** for that profile. Flash
`gemini-3.8-flash` executes with high reasoning. Carbon `gemini-4-carbon`
reviews each completed task without tools, using low reasoning, a 1,536-output-
token cap and bounded evidence. Initialization makes one review request.
Review failure is reported without retrying or substituting another model.
In normal REPL mode each completed answer is reviewed. In shell REPL mode the
review follows execution with `e`, so it can check actual output.

## Keys and quick switching

Each OS account has its own protected configuration under its home directory:

| File | Purpose |
|---|---|
| `.config/shell_gpt_exam/.sgptrc` | Active profile and its `OPENAI_API_KEY` |
| `.config/shell_gpt_exam/provider-keys.json` | Separate StepFun and Google keys |

These are plaintext credentials protected by current-user/SYSTEM ACLs on
Windows, or directory mode 700/file mode 600 on Linux. Never put keys in Git,
screenshots or command arguments. StepFun uses
`https://api.stepfun.ai/step_plan/v1`; Gemini uses
`https://generativelanguage.googleapis.com/v1beta/openai/`. Keys never cross
those endpoints.

On an **existing exam installation**, switch the default without reinstalling:

```powershell
python .\exam\setup_exam.py --profile-only --provider stepfun
```

```bash
python3 ./exam/setup_exam.py --profile-only --provider stepfun
```

Use `--provider gemini-mix` for the mix. Paste that provider's key if missing;
Enter retains a saved key. `--reuse-stepfun-key` explicitly imports the existing
same-account key from `.config/shell_gpt/.sgptrc` after checking its endpoint.
`--no-key-prompt` skips entry. To replace the active key later:

```text
python ./exam/setup_exam.py --key-only
```

Use `python3` on Linux. Once both keys are saved, override one request:

```text
sgpt --profile stepfun "Show my current directory"
sgpt --profile gemini-mix "Show my current directory"
```

## Use, approval and evidence

```text
sgpt --version
sgpt "init the machine"
sgpt --shell "Show my current directory"
sgpt --repl work "Help me inspect this machine"
```

Recognized inspection commands run automatically. Deletion, installation,
writes, scripts, sudo, command chains and unknown commands require approval of
the exact command. Refusal, missing input or policy failure prevents execution.
This is an approval aid, not an OS sandbox; independently piping generated
commands to another shell bypasses it. Tool continuations stop after eight API
turns. Requests have a 90-second client timeout and no automatic retries.

The Desktop has **two readable evidence files per IP**:

```text
Desktop/CEH-Exam/10.10.10.13/
    terminal.txt
    findings.txt
```

The example IP is not set by setup. The default folder uses the local IPv4
selected by the machine's routing table. On multihomed machines, choose the
intended filing IP explicitly. For work about another machine:

```text
sgpt --target-ip 10.10.10.9 "Summarize the observations I provide about this machine"
```

`--target-ip` selects a folder only. It does not connect, grant scan permission
or redirect local commands. Initialize without it to inventory the machine
running sgpt. Folders are local to each VM/account, not automatically synced.

`terminal.txt` records prompts, generated commands, actual output, approvals,
refusals, answers, reviews, API usage and timing. ANSI codes are removed. It
captures sgpt activity, not other terminals or GUI windows. Known saved keys
are redacted; other sensitive evidence may remain.

`findings.txt` contains only `Flag:` and `How found:` blocks. A finding must
occur in actual command output or your reported observations; AI text alone
is insufficient. After you actually observe a result, for example:

```text
sgpt --target-ip 10.10.10.9 "I found FLAG_VALUE in the GUI using these steps: ... Save the flag and how it was found."
```

Small summaries, tool indexes and command-output byte offsets are kept under
`.config/shell_gpt_exam/state/<IP>`. Full command output is stored once in
the transcript. No duplicate commands/network-dump/review files are created
on the Desktop. [LAB-RULES.md](LAB-RULES.md) contains the static rules; observed
data stays lower-trust request context and does not accumulate in chat history.

## Initialize, scope and tools

`sgpt "init the machine"` records local addresses, IPv4 routes and cached
neighbors, then asks for one short AI review. It does not scan other machines.
`sgpt --init-lab --local-only` explicitly skips the paid review.

Index the actual CEH tools directory without executing its files:

```powershell
sgpt --init-lab --tools-path C:\CEH-Tools
```

```bash
sgpt --init-lab --tools-path /mnt/ceh-tools
```

For GUI tasks, sgpt uses an indexed path or asks you where the tool is. It
provides manual steps and asks for relevant observations; it cannot see the GUI.
Active discovery requires your explicitly authorized IPv4 CIDR, /24 or smaller:

```text
sgpt --init-lab --scope YOUR_AUTHORIZED_CIDR --discover
```

This probes TCP 22, 80, 443, 445, 3389 and 5555 inside that supplied range only.
Cached neighbors do not prove current reachability; timeouts do not prove
offline status. A subnet mask does not establish authorized scope.

## Reset and reproduce the comparison

Preview first; `--clear` removes only known generated log/state filenames.
Nonempty findings, keys and unrelated files survive. Setup never clears logs.

```text
python ./exam/reset_exam_logs.py
python ./exam/reset_exam_logs.py --clear
```

Use `python3` on Linux. The matched live tests consume paid quota. They invoke
the real installed sgpt entry point, check actual command evidence and reject
missing/empty reviews:

```powershell
$py="$env:LOCALAPPDATA\CEHLab\shellgpt-exam\venv\Scripts\python.exe"
& $py .\exam\compare_profiles.py --profile stepfun
& $py .\exam\compare_profiles.py --profile gemini-mix
```

```bash
~/.local/share/shellgpt-exam/venv/bin/python ./exam/compare_profiles.py --profile stepfun
~/.local/share/shellgpt-exam/venv/bin/python ./exam/compare_profiles.py --profile gemini-mix
```

This covers integration and simple evidence reasoning, not complete exam
readiness. No test flags or active subnet discovery are created.

## Remove after use

Run system Python as the same user, from the repository root:

```text
python ./exam/uninstall_exam.py --dry-run
python ./exam/uninstall_exam.py
```

Use `python3` on Linux. Removal deletes the dedicated exam environment, keys,
configuration and private state. Desktop evidence and the original universal
StepFun installation remain. `--keep-config` intentionally retains keys/history.
Open a new terminal afterward.

`OTHER` means an unspecified provider reason. No safety setting is disabled or
purpose disguised to obtain a response. Preserve the timestamp, model, endpoint
and harmless reproduction for provider support; exclude the key. For
401/403/404/429, check that provider's key, model access, network, quota and
billing. Check access shortly before use; remote API availability is not guaranteed.
