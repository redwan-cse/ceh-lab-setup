# Exam ShellGPT with Gemini 4 Carbon

Use your **Google AI Studio / Gemini API** key. This profile uses Google's
direct API, ShellGPT **1.5.1**, and **high** reasoning. Your requested
`google/gemini-4-carbon` gateway name becomes **`gemini-4-carbon`** on Google's
direct endpoint: `https://generativelanguage.googleapis.com/v1beta/openai/`.
No OpenRouter, Vercel or StepFun key is used by this profile.

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

Sources: [Google OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai)
and [Gemini 4 Carbon availability](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-carbon-now-available/).
