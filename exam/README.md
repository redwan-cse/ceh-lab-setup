# Exam ShellGPT with Gemini 4 Carbon

Use your **Google AI Studio / Gemini API** key. This profile uses Google's
direct API, ShellGPT **1.5.1**, and **high** reasoning. Your requested
`google/gemini-4-carbon` gateway name becomes **`gemini-4-carbon`** on Google's
direct endpoint: `https://generativelanguage.googleapis.com/v1beta/openai/`.
No OpenRouter, Vercel or StepFun key is used by this profile.

**Current live-test status (2026-11-12):** Carbon's init review passed on both
VMs, but ordinary command requests still return `content_filter: OTHER`.
**Carbon command execution remains unresolved.** A valid key and successful
native API greeting do not establish that the full sgpt request will work.
Flash has executed real guarded commands on both VMs; the latest Parrot recheck
passed, while the latest Windows repeat stalled and was stopped. See the
diagnostic record below before relying on this setup for an exam.

To explicitly use the tested Flash model for a request:

```text
sgpt --model gemini-3.8-flash "hello"
```

Carbon remains the default; there is no silent model substitution or safety
setting change. That override applies to ordinary chat, shell and tool requests.
The exact `sgpt "init the machine"` shortcut uses the configured default for its
one review. Provider-filtered responses stop without an automatic retry.

## Install in a new exam VM

Have Git access to this private repository and Internet access to Python/PyPI
and Google's API. Run setup as the account that will use ShellGPT. These scripts
configure ShellGPT only; they do not change IP/DNS, SSH, firewalls or Defender.

```text
git clone https://github.com/redwan-cse/ceh-lab-setup.git
cd ceh-lab-setup
```

For an existing checkout, run `git pull --ff-only` instead. Keep the entire
checkout: the exam installer reuses the approved command guards in `universal`.

**Windows — from the repository root:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1
```

Missing/old Python is replaced for the current user with a signed Python
3.14.10 installer. It reuses existing Python 3.10+. Administrator rights are
normally unnecessary for this per-user setup.

**Parrot / Debian-based Linux — from the repository root, as a normal user:**

```bash
bash ./exam/setup-exam.sh
```

Sudo is used only if Python/venv prerequisites are missing. Python 3.10+ is
required. Parrot Security is the tested Linux target; other distributions may
need their own prerequisite installation.

Both commands install an isolated environment, prompt for the API key with
**hidden input**, and make `sgpt` select this exam profile. Open a new terminal.
`sgpt-exam` always explicitly selects the exam profile. Neither installer
overwrites the StepFun configuration or uninstalls its packages. On Linux,
an existing `sgpt` wrapper is backed up as `sgpt.before-exam` before replacement.
On Windows, the exam command directory is prepended to your user PATH.

## Where to paste the API key

Paste it into the installer's hidden **Google AI Studio API key** prompt.
Press Enter to keep a saved exam key. The key is stored in `OPENAI_API_KEY`:

| OS | Protected per-user file |
|---|---|
| Windows | `%USERPROFILE%\.config\shell_gpt_exam\.sgptrc` |
| Linux | `~/.config/shell_gpt_exam/.sgptrc` |

This config contains plaintext protected by user/SYSTEM ACLs on Windows, or
directory 700/file 600 on Linux. It is separate from StepFun's `shell_gpt`
directory. Never put a real key in scripts, Git, screenshots or command arguments.
The installer does not reuse another provider's key.

To replace a key later, from the repo root:

```powershell
python .\exam\setup_exam.py --key-only
```

```bash
python3 ./exam/setup_exam.py --key-only
```

Use `-NoKeyPrompt` on the Windows installer or `--no-key-prompt` on Linux for
setup without interactive key entry. Enter a key later before live use.

## Use and approval behavior

```text
sgpt --version
sgpt "Explain this command output"
sgpt --shell "Show my current directory"
sgpt --repl exam "Help me inspect this machine"
```

Recognized inspection commands run automatically. Examples: `pwd`, `ls`, `id`
and `date` on Linux; `Get-Location`, `Get-Process` and `Get-Date` on Windows.
Deletion, installation, file writes, scripts, sudo, command chains and unknown
commands require typing **yes** for the exact displayed command. A refusal,
missing input or policy error prevents execution. This is an approval aid,
not an OS sandbox. Do not pipe `--shell --no-interaction` output into a shell;
that bypasses guarded execution. Tool continuations stop after eight API turns.

The adapter uses complete nonstreaming API messages so Gemini tool metadata
and thought signatures survive continuation. Output appears after each model
response, rather than streaming token by token. REPL requests retain their
conversation history; completion caching is intentionally disabled by the adapter.

## Desktop logs, findings and lab initialization

Every command executed through the exam `sgpt` guard (including `--shell`)
is recorded under **Desktop → CEH-Exam → machine hostname**. Private report
files remain local and are ignored by Git:

| File | Contents |
|---|---|
| `terminal.txt` | Text printed by sgpt, with real line breaks and ANSI color codes removed |
| `commands.txt` | Readable commands and returned output, including exit status/refusals |
| `commands.log` | Structured command evidence for verification and reuse |
| `findings.txt` | Only `Flag:` and `How found:` for each confirmed result |
| `network-info.txt` | Readable local addresses, routes, cached neighbors and any explicitly requested discovery |
| `init-review.txt` | The short model review of the collector output, plus API usage if returned |
| `network-info.json`, `tool-index.json` | Machine-readable context and filenames; not pasted wholesale into paid requests |

Initialize with either command:

```text
sgpt "init the machine"
sgpt --init-lab
```

Local scripts collect the facts first. Then **one** Google request checks a
compact summary for failures, missing fields or inconsistencies. That review
uses low reasoning, at most 5,000 characters of input facts and 1,536 completion
tokens, a 90-second timeout, and no retries or execution tools. This bounds
cost, but is not a fixed price. Missing API access does not lose local results.
The review is advisory: it cannot prove discovery is complete or correct.
Normal task requests keep their configured high reasoning.

For collection with **no API call**, use:

```text
sgpt --init-lab --local-only
```

To index available course tools, add the actual mounted/local directory:

```powershell
sgpt --init-lab --tools-path T:\
```

```bash
sgpt --init-lab --tools-path /mnt/ceh-tools
```

On the current Server 2022 VM, the local library path `C:\CEH-Tools` is also
available and avoids relying on an SMB connection. On another exam machine,
supply its actual path. Indexing lists filenames; it never executes the tools.

Initialization does **not** automatically scan every connected network. If the
exam explicitly authorizes a target range, supply it yourself (example only):

```text
sgpt --init-lab --scope 10.10.10.0/24 --discover
```

The explicit range is limited to IPv4 /24 or smaller. The collector probes TCP
22, 80, 443, 445, 3389 and 5555 inside that range only. Cached neighbors and past
observations are not proof of current reachability; timeouts do not prove a
machine is offline. Discovery does not authorize subsequent attacks.

Rules are saved in [LAB-RULES.md](LAB-RULES.md) and installed beside the exam
runtime. A compact, capped context summary accompanies later requests, rather
than the full network dump or tools index. Ask, for example:

```text
sgpt "Find the installed email-header analysis tool. Give its verified path and the manual steps. Tell me which results you need back."
sgpt "I found flag FLAG_VALUE in the GUI using these steps: ... Save the flag and how it was found."
```

The adapter can save a flag only if it occurs in captured command output or an
observation you supplied. It refuses guesses; `findings.txt` contains no extra
report narrative. Do not treat an AI-suggested value as a confirmed flag.
For GUI tasks, sgpt must use an indexed existing path or ask you for the tool
directory/executable. It gives a short procedure and asks for the relevant
observations. It cannot see a GUI result or capture commands you run directly
in another terminal unless you provide those results.

`terminal.txt` is readable text, not a pixel-perfect copy of terminal colors or
GUI windows. Known configured API-key values are redacted from logs and guarded
command results. Other sensitive target data may be present: protect the folder.
The uninstaller preserves these reports; remove them separately only after
saving anything needed for your exam/report.

Workflow validation on 2026-11-12: 19 offline regression tests passed. Two
installed-CLI integration checks on each VM verified that both `--shell` and
tool commands produce readable audit records, with the API mocked to avoid
extra charges. Real bounded init reviews succeeded on both VMs: Parrot used
522 input/349 output tokens; Server 2022 used 1,000 input/359 output tokens.
No active discovery was run during those tests. The configured local tools
roots are `/mnt/ceh-tools` for Parrot and `C:\CEH-Tools` for Server 2022.

## Exam-day smoke test

First check `sgpt --version` reports 1.5.1. For a small paid live check:

```text
sgpt --no-cache --no-functions "Reply exactly READY"
sgpt --shell "Show my current directory"
```

For the full three-test suite, from the repository root:

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-exam\venv\Scripts\python.exe" .\exam\verify_exam.py
```

```bash
~/.local/share/shellgpt-exam/venv/bin/python ./exam/verify_exam.py
```

These use your paid quota. They verify text, automatic inspection and an actual
tool round trip without prompting for approval. High reasoning can take longer
and cost more; no exam-VM performance or API access is guaranteed.

Offline protocol tests (no key or paid request):

```text
python -m unittest discover -s exam -p test_protocol.py -v
```

## Troubleshooting and switching back

- **Command missing:** open a new terminal; on Linux `~/.local/bin/sgpt-exam`
  is an explicit fallback. Windows: use
  `%LOCALAPPDATA%\CEHLab\shellgpt-exam\bin\sgpt-exam.cmd`.
- **401/403/404/429:** check the saved key, paid project/model access, network,
  quota and billing in AI Studio. Keep the direct model ID `gemini-4-carbon`.
  Diagnostic errors omit provider response bodies to avoid exposing secrets.
- **Approval asks unexpectedly:** use literal inspection commands. Dynamic
  expressions and scripts are deliberately not automatic.
- **Rerun:** the dedicated exam venv is refreshed; a saved Google exam key is
  retained. The existing StepFun config remains intact. Back up custom exam
  settings before rerunning; they are regenerated.
- **StepFun again:** rerun the existing universal StepFun installer to select
  that profile, or restore the backed-up Linux wrapper. On Windows remove the
  exam `bin` entry from your user PATH to expose the original command again.

## Remove after use

Run as the same user who installed the exam profile, from the repository root:

```powershell
python .\exam\uninstall_exam.py
```

```bash
python3 ./exam/uninstall_exam.py
```

This removes the dedicated exam venv, command wrappers, exam key and chat/cache
directory. It restores a saved Linux `sgpt` wrapper or removes the Windows exam
PATH entry, exposing the original command. Shared Python, Git and the StepFun
profile are kept. Changed/unrelated wrappers and redirected folders are refused
rather than overwritten. Open a new terminal afterward.

Use `--dry-run` first to inspect the planned directory removals. `--keep-config`
intentionally retains the key/history; omit it for complete exam-profile cleanup.
It does not delete the repository checkout or a key file you saved elsewhere.

## Validation on 2026-11-11

Parrot `attacker@10.10.10.13` and Server 2022 Administrator at `.22` each passed
all three live Gemini checks using the user's AI Studio key: six live checks
total. Three offline adapter tests cover tool metadata, unknown-tool rejection
and the continuation limit. Four removal tests cover command restoration,
unrelated-file protection, directory scoping and dry-run behavior. Seven Linux
guard tests and six Windows guard tests also passed in the exam environments.
On 2026-11-12 both installed command paths and uninstall previews were rechecked;
the working profiles remain installed. Existing shared command guards are reused.
No key values or provider error bodies are committed.

### Real sgpt-only verification on 2026-11-12

Both VMs were invoked through the documented `sgpt "init the machine"` entry
point over SSH. No native network verification commands were run outside sgpt.
Parrot reported `10.10.10.13/24`, default gateway `10.10.10.1`; Server 2022
reported `10.10.10.22`, the same gateway, and DNS `8.8.8.8`/`1.1.1.1`.
These match the documented lab configuration and each other's cached-neighbor
observations. Current peer reachability was not independently established.
Scope remained unset, and no active discovery was performed.

Gemini's init review identified collection limits (including Windows prefix
length absent from the address summary, and missing Linux DNS/IPv6-routing
sections). Those are not silently counted as complete inventory coverage.
Review usage was 607 input/268 output tokens on Parrot and 1,092 input/294 output
tokens on Windows. Requests to execute fresh verification commands through
sgpt's tool failed at the provider as described above, before those commands
ran. The former AttributeError for a missing assistant message was fixed and
covered by a regression test; an unusable provider-filtered completion now exits
with its known unspecified reason and code 2. Later controlled comparisons found
that Carbon could answer a greeting on Parrot while still failing `pwd` tool
execution. Flash executed `pwd` (evidence `2e37288cd81a`) and `Get-Location`
(evidence `e8ff45996f12`) through sgpt on the two VMs. These prove those command
paths work with Flash, not that Carbon's provider-side issue has been resolved.

### Provider request diagnosis on 2026-11-12

Carbon answered minimal greetings through both Google's native and
OpenAI-compatible APIs with high reasoning. The complete captured sgpt greeting
request failed on both paths; changing transport alone was not a fix. Removing
tools did not resolve that failure. Static rules and saved-context text each
worked separately in controlled greeting diagnostics.

Keeping all rules and observations but separating their message roles let the
controlled greeting succeed. The runtime now keeps static rules in the system
message and observations in a separate, lower-trust user message. Real Windows
`sgpt "hello"` then passed. Actual tool messages and thought signatures persist
in chat history; transient observations do not accumulate. Carbon's subsequent
`pwd` and `Get-Location` tool requests still failed on both VMs. Google supplied
only `OTHER`, meaning an unknown reason, with no further diagnostic details;
these results do not establish a particular safety rule or a complete fix.

After that change, Flash again executed `pwd` on Parrot (evidence
`81509c9bf9c3`). A repeat Windows live Flash request stalled before producing
command output and was stopped; it is not counted as a pass. The local suite
passed 24 tests with two installed-only tests skipped. Both installed-only
checks passed separately on each VM using mocked API responses and real sgpt
logging/guard paths; those checks do not validate provider availability.

For provider support, retain the endpoint, model, timestamp and harmless
reproduction. Never include your API key. Temporary request-capture helpers and
captured payload files were removed after diagnosis.

Sources: [Google OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai)
and [Google response finish reasons](https://aistudio.google.com/api-reference/generate-content#Resource:Candidate).
