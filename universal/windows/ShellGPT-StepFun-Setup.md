# ShellGPT + StepFun for any Windows CEH lab

Copy this entire folder to the target Windows PC. In a local PowerShell terminal:

```powershell
.\Setup-ShellGPT-StepFun.ps1 -PromptForApiKey
```

Keep `Setup-ShellGPT-StepFun.ps1`, `shellgpt_stepfun_setup.py`,
`shellgpt_command_guard.py`, `shellgpt_command_policy.ps1`, and
`test_command_guard.py` together. `verify_shellgpt_live.py` is optional.
Requires Windows PowerShell 5.1 and Internet access. No IP address or account
name is built in. Setup uses the current Windows account and its permissions.
Do not run setup from inside `%USERPROFILE%\.config\shell_gpt`.

Python 3.10+ is reused when available. Otherwise setup downloads Python 3.14.10
from python.org, verifies its Authenticode signature and Python Software
Foundation signer, then installs it for the current user with pip. It pins
ShellGPT 1.5.1, Typer 0.16.0 and Click 8.1.8 and adds the user Scripts directory
to the user PATH. Open a new terminal after installation.

The configured model is `step-5-preview`, endpoint
`https://api.stepfun.ai/step_plan/v1`, reasoning effort `high`. Checked patches
forward reasoning effort and preserve StepFun streaming tool reasoning across
requests. Upgrading ShellGPT separately can overwrite these patches.

## Credentials and reruns

`-PromptForApiKey` reads a hidden SecureString after successful installation.
The installer converts it only while writing the protected current-user
`%USERPROFILE%\.config\shell_gpt\.sgptrc` file and frees the BSTR in a
finally block. The key is stored as plaintext in that current-user/SYSTEM ACL
protected config, as required by ShellGPT. No command-line key argument or
source secret is used. Blank input keeps the saved key.

A normal rerun preserves the saved config API key only when its existing
API_BASE_URL is HTTPS on exactly api.stepfun.ai (default HTTPS port, no URL
credentials). Missing, foreign or malformed provider settings discard the old
key from the regenerated config and advise using the secure local prompt; no
key or old URL value is printed. This prevents reusing an OpenAI or other
provider key with StepFun. The rerun replaces ShellGPT's
settings, functions, roles and caches inside its own configuration directory.
`-ResetConfig` discards the saved key; combine it with `-PromptForApiKey` to
enter a replacement. Generic `%TEMP%\cache` / `%TEMP%\chat_cache` and custom
external caches are left alone. Shared Python dependencies remain, with the
CLI dependencies pinned above.

ShellGPT environment variables take precedence over its config. Before any
uninstall or config removal, setup refuses nonempty conflicting process,
per-user or machine environment settings and names them without exposing their
values. Review/unset the listed settings for the intended lab account, then
open a new terminal and retry. Setup never deletes persistent environment
credentials belonging to other applications. Use a dedicated Windows account
if those settings must remain for another application.

## Guarded commands

```powershell
sgpt "Show the current directory and list running processes"
sgpt --shell "List files in the current directory"
sgpt --repl lab "Help me inspect this Windows PC"
```

The ordinary and REPL modes use a guarded execution tool; `--shell` routes its
generated command through the same guard. Literal inspection commands run
automatically: Get-Location, Get-ChildItem, Get-Content, Get-Item,
Get-ItemProperty, Get-PSDrive, Test-Path, Resolve-Path, Get-Process,
Get-Service, Get-Date and Get-Host. Literal pipelines using Select-Object,
Sort-Object, Measure-Object, Format-Table and Format-List are supported.
Only parameters explicitly listed in the policy are automatic.

Other commands require typing **yes** to run the exact displayed command.
This includes installation, deletion, file writes, aliases, executables,
scripts, variables, expressions and compound commands. Refusal, unavailable
input or classifier failure prevents execution. Automatic commands are
qualified to trusted system modules and run without profiles. The guard is
an approval aid, not an OS sandbox. `--shell --no-interaction` prints only;
piping that output into a shell bypasses the guard. Runtime is limited to
300 seconds; timed-out child processes may need manual inspection.

## Optional remote setup

```powershell
.\Setup-ShellGPT-StepFun.ps1 -ComputerName TARGET_HOST -UserName TARGET_ACCOUNT
```

Requires SSH/scp and an existing writable SSH account on the target. Omitting
UserName uses the initiating process's USERNAME, which may differ from the
target's account. Setup uploads only nonsecret setup files to that account's
home and runs noninteractively. `-ResetConfig` and `-IsolatedTest` are forwarded.
`-PromptForApiKey` is rejected for normal remote setup because noninteractive
SSH cannot securely prompt there. Copy/run locally with that switch on the
target to enter a key. IsolatedTest ignores PromptForApiKey.

## Offline verification

```powershell
.\Setup-ShellGPT-StepFun.ps1 -IsolatedTest
python -m unittest discover -s . -v
```

IsolatedTest requires existing Python. It installs test packages/config under
a fresh temporary directory and leaves the active key, packages, user PATH
and persistent environment unchanged. It still downloads packages from pip.
It never prompts for a key. Setup checks request JSON, model, endpoint, high
reasoning, streaming tool continuation and guarded execution using a dummy key
and local HTTP mocks. No setup mode calls the real API by default.

After saving a key, explicitly run the optional live verifier:

```powershell
python verify_shellgpt_live.py
```

It makes billable requests for plain text, Get-Location shell execution, and
a Get-Date tool round trip, redacts the key in captured output, and fails on
unexpected approval prompts. No install or deletion is requested by those
live checks. Test results from another machine do not guarantee network or
provider availability in a new lab.
