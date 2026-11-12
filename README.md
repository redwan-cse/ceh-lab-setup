# ceh-lab-setup

One `sgpt` command for CEH Practical preparation. Fresh exam installs use
OpenRouter `deepseek/deepseek-v4.1-flash-1017`; StepFun `step-5-preview` is a
manual alternative and our local-practice choice. There is no automatic fallback.

- [Exam: Parrot](#exam-parrot)
- [Exam: Windows](#exam-windows)
- [Exam: Android target](#exam-android-target)
- [Normal local lab](#normal-local-lab)
- [All documentation](#all-documentation)

Clone the private repository on the machine you will configure, then enter it:

```text
git clone https://github.com/redwan-cse/ceh-lab-setup.git
cd ceh-lab-setup
```

For an existing clone, run `git pull --ff-only`. GitHub access is required.
If Git is unavailable, download/extract the repository ZIP. Keep the full kit:
`exam`, `universal` and `docs` are used together. All commands below start from
this repository folder unless stated otherwise.

## Exam: Parrot

Use the exam's assigned normal account. Our local testing used `attacker`;
ShellGPT and API keys are per-user, so check `whoami` before setup.

### Install and enter the API key

```bash
bash ./exam/setup-exam.sh
```

Paste your **OpenRouter API key at the hidden prompt**, then open a new terminal.
Fresh installs choose DeepSeek; reruns retain the active provider. Setup checks
Python 3.10+, the private pinned ShellGPT environment, Bash and `iproute2`.
Missing prerequisites require one installation consent; sudo may separately
request your password. Declining or noninteractive input installs nothing.
No CEH tool bundle, OS upgrade/removal, SSH or network changes are performed.
If the lab has Python 3.8 or no usable venv support, setup downloads a
checksum-verified private Python 3.12 instead of requesting obsolete Python
packages from APT. The system Python and repository configuration stay unchanged.

If ShellGPT is already installed, run this same setup. It installs/repairs our
private copy and activates `sgpt`; an existing per-user launcher is backed up,
including pipx links. Keys, findings and exam evidence are retained on reruns.
Open a new terminal after setup so the updated command takes precedence.

Active settings/key: `~/.config/shell_gpt_exam/.sgptrc`.
Saved provider keys: `~/.config/shell_gpt_exam/provider-keys.json`.
These are protected local plaintext files, excluded from Git. To replace the
active key later:

```bash
"$HOME/.local/share/shellgpt-exam/venv/bin/python" ./exam/setup_exam.py --key-only
```

### Check, initialize and work

```bash
sgpt --version
sgpt --model-info
sgpt "init the machine"
sgpt --tool-help "nmap"
sgpt --repl work "Help me inspect this machine"
```

For a normal conversation, run **`sgpt`** without a prompt. Type your task at
the chat prompt and continue replying there; Ctrl+C stops the chat. The
one-shot commands above remain available. A tools path is never a prerequisite:
Parrot uses installed commands first and checks the current folder, relevant Desktop folders or
standard wordlists when needed. If you want a custom folder, say in chat:
`Use ~/Desktop/MyWordlists when this task needs a wordlist` (use a real path).

`--model-info` reads the actual configuration without an API call. Initialization
runs the native Bash collector for host identity, addresses, routes/DNS, cached
neighbors and available tools, followed by one bounded model review. It does
not scan other machines. See [scope and evidence rules](exam/README.md#initialize-and-inspect-safely).

New commands/output go to `~/Desktop/CEH-Exam/<IP>/terminal.md` (or the configured
Desktop location). Confirmed flags and how they were found go to `findings.txt`.
Old evidence is preserved. Inspection commands follow the existing approval guard;
installation, deletion, writes, scripts and unknown commands require approval.

All saved final results—including tool lists, reports and scan exports—belong
in this exam folder. Tools folders remain input locations. sgpt receives the
exact destination and must verify saved files and report their paths.

Long tasks get 20 model/API rounds, then an interactive **continue? [y/N]**
prompt. `yes` continues with the existing results. Use `--tool-rounds 30` to
choose a larger block; [continuation details](exam/README.md#longer-tasks-and-continuation).

### Switch models without reinstalling

```bash
bash ./exam/switch-model.sh stepfun
# Return to the exam model:
bash ./exam/switch-model.sh deepseek
sgpt --model-info
```

The switch updates one active endpoint/model/key together. A missing matching
key is requested securely; cancellation retains the current selection.

### Remove after use

Preview first, then remove as the same account:

```bash
python3 ./exam/uninstall_exam.py --dry-run
python3 ./exam/uninstall_exam.py
```

This removes the dedicated exam environment, keys and private state, while
retaining Desktop evidence and Python itself. [Full exam guide](exam/README.md).
On an older cloud image whose system Python is below 3.10, use the cached
bootstrap interpreter for removal instead:

```bash
task_python="$(bash ./exam/bootstrap-python-linux.sh --find)"
"$task_python" ./exam/uninstall_exam.py --dry-run
"$task_python" ./exam/uninstall_exam.py
```

## Exam: Windows

Run Windows PowerShell under the account that will use `sgpt`. Check `whoami`.
The exam installer changes the per-user ShellGPT setup; it does not configure
OpenSSH, Defender, firewall rules, IP addresses or DNS.

### Install and enter the API key

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1
```

Paste your **OpenRouter API key at the hidden prompt**, then open a new terminal.
Fresh installs choose DeepSeek; reruns retain the active provider. Missing
prerequisites require one installation consent; OS authentication may ask
separately. Existing usable Python is preferred. If needed, signed Python is
installed under `%LOCALAPPDATA%\CEHLab\shellgpt-python`, without adding Python
to PATH or installing a global launcher.

An existing ShellGPT installation is supported: run this same setup to
install/repair the private copy and activate `sgpt`. Any launcher replaced in
our per-user command location is backed up; existing keys and exam evidence
are retained. Open a new terminal after setup.

Setup notifies the Windows desktop about PATH changes and checks the launcher.
If an already-open terminal still says `sgpt` is not recognized, activate it
in that PowerShell window without reinstalling:

```powershell
$env:Path = "$env:LOCALAPPDATA\CEHLab\shellgpt-exam\bin;$env:Path"
sgpt --model-info
```

This also works for older installations and does not require changing PowerShell's
execution policy.
The [Windows command lookup guide](exam/README.md#windows-sgpt-is-not-recognized)
includes a direct-launch fallback.

Active settings/key: `%USERPROFILE%\.config\shell_gpt_exam\.sgptrc`.
Saved provider keys: `%USERPROFILE%\.config\shell_gpt_exam\provider-keys.json`.
The files are protected for the current user/SYSTEM and excluded from Git.
To replace the active key later, use existing Python:

```powershell
python .\exam\setup_exam.py --key-only
```

If setup used its app-local Python and `python` is not on PATH:

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\setup_exam.py --key-only
```

### Check, initialize and work

```powershell
sgpt --version
sgpt --model-info
sgpt "init the machine"
sgpt --tool-help "nmap"
sgpt --repl work "Help me inspect this machine"
```

Initialization selects the native PowerShell collector for host identity,
addresses, routes/DNS, cached neighbors and available tools, followed by one
bounded model review. It does not scan other machines. New evidence goes to
`Desktop\CEH-Exam\<IP>\terminal.md` and `findings.txt` under this account's actual
Desktop. Existing evidence and the command-approval guard are retained.

All saved final results—including tool lists, reports and scan exports—belong
in this exam folder. Tools folders remain input locations. sgpt receives the
exact destination and must verify saved files and report their paths.

Long tasks get 20 model/API rounds, then an interactive **continue? [y/N]**
prompt. `yes` continues with the existing results. Use `--tool-rounds 30` to
choose a larger block; [continuation details](exam/README.md#longer-tasks-and-continuation).

Run **`sgpt`** alone to open normal chat and continue typing at its prompt.
There is no separate tools-path input dialog. A path is optional: for example,
type `Use C:\Users\Administrator\Desktop\Tools for this task` in chat, replacing
it with the actual path. A specific executable or wordlist file is accepted too.

### Switch models without reinstalling

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 stepfun
# Return to the exam model:
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 deepseek
sgpt --model-info
```

The switch updates one active endpoint/model/key together. A missing matching
key is requested securely; cancellation retains the current selection.

### Remove after use

Use existing system Python, as the same account:

```powershell
python .\exam\uninstall_exam.py --dry-run
python .\exam\uninstall_exam.py
```

If setup used its app-local Python instead:

```powershell
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\uninstall_exam.py --dry-run
& "$env:LOCALAPPDATA\CEHLab\shellgpt-python\python.exe" .\exam\uninstall_exam.py
```

The dedicated exam environment, keys and private state are removed. Desktop
evidence and Python itself remain. [Full exam guide](exam/README.md).

## Exam: Android target

Use Parrot or Windows as the controller and the exam-provided Android machine
as the target. This kit does not install ShellGPT on Android. Use the assigned
Android IP and ADB port; the local lab's `10.10.10.9:5555` is only a practice
example. Keep the exam machine's provided network/debugging configuration.

### Check the controller and connect

ADB must already be available on the controller. Check its command path with
`command -v adb` on Parrot or `Get-Command adb` on Windows. If missing, locate
the provided CEH tools first; request approval before installing anything.

The following ADB syntax works on both systems. Replace **`ANDROID_IP`** and
**`ADB_PORT`** with the assigned values before running:

```text
adb version
adb devices -l
adb connect ANDROID_IP:ADB_PORT
adb -s ANDROID_IP:ADB_PORT shell getprop ro.build.version.release
adb -s ANDROID_IP:ADB_PORT shell ip -4 addr show
adb -s ANDROID_IP:ADB_PORT shell ip route
```

Expect the selected device to appear as `device`. For `unauthorized`, review
the intended device's authorization prompt. For `offline` or a failed connection,
check the assigned address/port and device state before retrying. Some Android
versions use pairing/dynamic ports; do not assume every device uses TCP/5555.
Do not reset networking, restart ADB on the target or enable debugging unless
the exam task permits that configuration change.

### Capture Android evidence

Have `sgpt` run the approved ADB commands to capture their output in its Markdown
transcript; ADB commands run separately are not captured automatically. Use
`sgpt --target-ip ANDROID_IP "..."` to file the task under the Android IP.
This filing option does not connect or grant permission by itself. For a GUI
finding, provide the actual flag and steps to `sgpt` so it can save them.

See [ADB, APKTool and mobile workflows](docs/ceh-tools/mobile-and-wireless.md).
For building/configuring our own Android-x86 VM, use the
[local Android guide](ceh-local-lab/README.md#android-mobile-target) and its
historical source. Local IP assignment and checkpoint recovery belong to the
practice lab; they are not automatic exam setup steps.

## Normal local lab

The existing practice environment is on physical Hyper-V host **Redwan-PC**.
Follow the [complete local lab guide](ceh-local-lab/README.md) for daily use,
accounts, SSH keys, sleep prevention, shared tools and Android recovery.
Its addresses are specific to our practice network, not exam defaults.

| Machine | Local address | Role |
|---|---|---|
| ParrotOS Sec | `10.10.10.13` | Linux workstation; `attacker` / `redwan` |
| Win11-Client | `10.10.10.11` | Windows workstation |
| WinServer-2019 | `10.10.10.19` | Windows server |
| WinServer-2022 | `10.10.10.22` | Windows server and tools share |
| Android-8.1-Target | `10.10.10.9` | Android 8.1 mobile target, ADB TCP/5555 |

The local switch is `CEH-Lab-Switch`, network `10.10.10.0/24`, gateway
`10.10.10.1`. Recheck current availability using the local guide; a historical
health report is not a guarantee that every VM is running now.

### Local ShellGPT and SSH setup

For the current single-command workflow with evidence logs, use the matching
OS setup above, then manually select StepFun with its model switcher. Configure
each account separately. Our latest exam-flow testing was under Parrot
`attacker` and Server 2022 `Administrator`; `redwan` retains its older setup.

The older universal StepFun installers remain available for reproducing the
original lab setup. Their high-effort setting is a custom adapter, not a native
ShellGPT 1.5.1 option. The current exam kit uses provider-default reasoning;
it does not force `high` or `max`.

Windows, Administrator PowerShell for SSH configuration:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\universal\Start-CehLab.ps1
```

This sets up OpenSSH and legacy StepFun ShellGPT, retaining password/public-key
SSH. Use `-SkipSsh` for ShellGPT only, `-SkipShellGpt` for SSH only, or
`-NoApiKeyPrompt` to enter the key later. It does not copy your SSH key itself.
See [Windows options and verification](universal/windows/README.md).

Parrot, as the normal user:

```bash
bash ./universal/linux/setup-shellgpt-parrot.sh
```

This sets up legacy StepFun ShellGPT without changing Linux SSH. Use
`--no-api-key-prompt` to enter the key later. See
[Linux options and verification](universal/linux/README.md).
Legacy keys are under `.config/shell_gpt/.sgptrc`, separate from the current
exam kit's `.config/shell_gpt_exam/.sgptrc`. Never commit either file.

### Local health, Android and shared tools

On physical Redwan-PC, from this repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Test-CehLab.ps1 -SkipHyperV
```

- [Daily use, Hyper-V checks and SSH keys](ceh-local-lab/README.md#machines-and-daily-use)
- [Parrot accounts and sleep prevention](ceh-local-lab/README.md#parrot-accounts-and-sleep-prevention)
- [Android-x86 configuration and checkpoint recovery](ceh-local-lab/README.md#android-mobile-target)
- [Read-only shared CEHv13 tools and mounted drives](ceh-local-lab/README.md#shared-cehv13-tools)
- [Dated lab health and outstanding work](ceh-local-lab/HEALTH-REPORT.md)

Local Windows/Defender/network helpers are documented in the local guide.
They are not part of the exam installer. Review their effects before use.

## All documentation

All maintained guides are kept in this repository and published together:

- [Full exam setup, scope, evidence, reasoning and recovery guide](exam/README.md)
- [Normal chat, optional tools paths and versioned scripts](exam/README.md#normal-chat-optional-paths-and-scripts)
- [ShellGPT task rules](exam/LAB-RULES.md)
- [CEH tool commands and workflows](docs/ceh-tools/README.md)
- [Local tool inventory summary](docs/ceh-tools/inventory.md), [Parrot inventory](docs/ceh-tools/inventory-linux.md), [Windows inventory](docs/ceh-tools/inventory-windows.md)
- [Earlier model comparison](exam/COMPARISON.md) and [terminal challenges](exam/LAB-CHALLENGES.md), with their historical settings
- [Complete local lab guide](ceh-local-lab/README.md) and [health report](ceh-local-lab/HEALTH-REPORT.md)
- [Original Gemini Hyper-V build notes](ceh-local-lab/reference/gemini-hyper-v-guide.md), retained as historical reference
- [Windows universal source](universal/windows/README.md) and [Linux universal source](universal/linux/README.md)

API keys, passwords, private keys, VM tools archives and runtime evidence stay
out of Git. Setup does not guarantee Internet/API access or install permissions
on an unknown exam machine.
