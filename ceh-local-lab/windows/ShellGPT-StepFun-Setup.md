# Reusable ShellGPT + StepFun setup for Windows

From PowerShell in this folder:

```powershell
.\Setup-ShellGPT-StepFun.ps1 -ComputerName 10.10.10.11 -UserName Win11-Client
```

Keep these five files together: `Setup-ShellGPT-StepFun.ps1`,
`shellgpt_stepfun_setup.py`, `shellgpt_command_guard.py`,
`shellgpt_command_policy.ps1`, and `test_command_guard.py`.
The remote command uploads them into the SSH user's home directory, then runs
setup. Requires Windows PowerShell 5.1, Internet access, and SSH/scp for remote setup.
Normal setup detects Python 3.10+ or downloads and installs signed Python 3.14.10
from python.org when missing. It verifies the installer's Authenticode signature
and Python Software Foundation signer before execution, and bootstraps pip if
needed. Isolated testing requires Python already installed and does not install it.
To install locally on another
Windows PC, copy the five files there and run the PowerShell script without
parameters. Target SSH home must be writable; don't launch setup from the
ShellGPT config directory it deletes.

## Installed configuration

- ShellGPT 1.5.1; compatible CLI dependencies Typer 0.16.0 and Click 8.1.8.
- Model: `step-5-preview` (ShellGPT calls this setting `DEFAULT_MODEL`).
- API base: `https://api.stepfun.ai/step_plan/v1`.
- Reasoning effort: `high`.
- PowerShell commands, guarded function calling enabled, request timeout 300 seconds.
- Per-user Python Scripts directory added to PATH.
- Configuration and caches stored under `%USERPROFILE%\.config\shell_gpt`.

The installer applies checked compatibility patches for high reasoning effort,
StepFun reasoning continuation, and selective command approval. Installing or
upgrading ShellGPT separately can overwrite those patches.

## Execution behavior

```powershell
sgpt "Show the current directory and list running processes"
sgpt --shell "List files in the current directory"
sgpt --repl lab "Help me inspect this Windows PC"
```

The ordinary command and REPL let the model call one guarded execution tool.
The shell option generates one command and passes it to the same guard. Answers
without a tool call do not execute anything. Execution uses the permissions of
the signed-in Windows user; it does not automatically elevate to Administrator.

Automatic execution is limited to literal inspection commands:
`Get-Location`, `Get-ChildItem`, `Get-Content`, `Get-Item`,
`Get-ItemProperty`, `Get-PSDrive`, `Test-Path`, `Resolve-Path`,
`Get-Process`, `Get-Service`, `Get-Date`, and `Get-Host`.
Literal pipelines through `Select-Object`, `Sort-Object`, `Measure-Object`,
`Format-Table`, and `Format-List` are supported. Only the explicit parameters
listed in the policy file are automatically accepted.

Everything else displays an approval prompt. This includes deletion,
installation, uninstall, upgrades, file writes, unknown executables, aliases
such as `dir`/`gci`, Python, scripts, command chains, expressions, variables,
redirection, and dynamic invocation. Use full command names and literal paths
to avoid unnecessary approval prompts.

Type **yes** to execute the exact displayed command. Any other answer, missing
console input, or a policy error refuses execution. Unknown-command displays
escape control characters. Commands run without PowerShell profiles, and
automatic cmdlets are qualified to trusted system modules. Command runtime is
limited to 300 seconds; a timeout may leave child processes to inspect manually.

This is an approval convenience, not an operating-system sandbox. Keep the
guard installed, use the patched execution paths, and review commands requiring
approval. A prompt telling the model to avoid deletion is not the enforcement:
the local guard decides whether approval is required.
`sgpt --shell --no-interaction` prints a command only; it does not execute it.
Do not pipe that output into a shell if you want the guard applied.

## API key

On the lab PC, edit:

```text
C:\Users\Win11-Client\.config\shell_gpt\.sgptrc
```

Set the initially empty line, without quotes:

```ini
OPENAI_API_KEY=your-stepfun-api-key
```

On other PCs, use `%USERPROFILE%\.config\shell_gpt\.sgptrc`.
The config directory and file grant access to the current user and SYSTEM.
Do not embed credentials in reusable scripts. Open a new terminal after setup,
then try `sgpt "Reply with OK"`. Live authentication requires a valid key.

## Reset behavior

**Normal setup is a clean reinstall. It deletes the previous key and ShellGPT
customizations.** It uninstalls the selected Python's ShellGPT distribution,
removes the user's ShellGPT settings, roles and functions, and removes default
ShellGPT temp caches. Custom external cache paths are reported for manual
review. Shared Python dependencies remain installed, though CLI dependencies
are pinned to compatible versions.

The installer clears old per-user provider, shell, function-path and cache
environment settings because these override the config. It refuses conflicting
machine-level values. Other Python installations, virtual environments and
other Windows users are outside this setup's scope.

## Verification without changing the active setup

```powershell
.\Setup-ShellGPT-StepFun.ps1 -ComputerName 10.10.10.11 -UserName Win11-Client -IsolatedTest
```

This installs into new temporary user/package/config directories, skips package
uninstallation, and leaves the active config, saved key, user PATH and user
environment registry untouched. It prints the temporary test path for inspection.

Verification covers the real request JSON, model, endpoint, high reasoning
effort, streaming tool round trip, automatic inspection, explicit approval,
refusal, unavailable input, classifier errors and common hidden-command syntax.
API tests use a dummy key and local mock HTTP transport, with no paid API call.

To run policy tests alone on Windows:

```powershell
python -m unittest discover -v
```

## Live StepFun verification

After installation and saving the API key, run on the target PC:

```powershell
python verify_shellgpt_live.py
```

This optional verifier is included in the ZIP and copied during remote setup
when present beside the installer. It makes three small, billable API requests
to test a text response, automatic shell execution of Get-Location, and an
automatic Get-Date tool call with a response afterward. It fails if an approval
prompt appears. API-key values are redacted from captured output.

The complete setup was also tested on Windows Server 2019 at 10.10.10.19,
including automatic Python installation on a machine without Python.
