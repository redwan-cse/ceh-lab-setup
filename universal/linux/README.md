# ShellGPT + StepFun on Debian/Parrot Linux

Verified on Parrot Security 7.4 with Python 3.13. These scripts contain no
target IP address, subnet or login user and are separate from the Windows installer.

Copy this folder to the target, SSH in as the normal user, then run:

```bash
cd /path/to/ceh-lab-setup/universal/linux
bash setup-shellgpt-parrot.sh
```

Keep these five files together: `setup-shellgpt-parrot.sh`,
`configure_shellgpt.py`, `linux_command_guard.py`, `test_linux_guard.py`,
and `verify_shellgpt_parrot.py`. Setup needs Internet access and Python 3.10+.
It uses sudo/apt only if Python or the virtual-environment prerequisite is
missing. It installs ShellGPT 1.5.1, Typer 0.16.0 and Click 8.1.8 into:

```text
~/.local/share/shellgpt-stepfun/venv
```

Parrot's system Python packages are kept separate. Setup creates a command at
`~/.local/bin/sgpt` and adds that directory to the user shell PATH. Reconnect
SSH or open a new terminal after setup. The wrapper clears inherited provider
settings, so this installation uses its protected config file consistently.
Existing system/pipx ShellGPT installations are left untouched; `command -v
sgpt` should resolve to the new user wrapper after reconnecting.

## Model and API key

The configuration uses:

```ini
DEFAULT_MODEL=step-5-preview
API_BASE_URL=https://api.stepfun.ai/step_plan/v1
REASONING_EFFORT=high
OPENAI_USE_FUNCTIONS=true
```

Save the StepFun key in `~/.config/shell_gpt/.sgptrc`:

```ini
OPENAI_API_KEY=your-stepfun-api-key
```

The config directory uses mode 700; the config file uses mode 600. No key or
SSH password belongs in these scripts. Re-running setup preserves an existing
key only if its saved HTTPS provider is api.stepfun.ai; a foreign/missing provider
leaves the key empty so another service's credential is never sent to StepFun.
Setup refreshes the dedicated environment and replaces this setup's settings.
Guarded functions and roles use dedicated `functions-stepfun` and
`roles-stepfun` directories, leaving other user customizations separate.

## Commands and approvals

```bash
sgpt 'Show my current directory'
sgpt --shell 'List files in the current directory'
sgpt --repl lab 'Help inspect this Parrot PC'
```

The normal mode/REPL offers one guarded execution tool. `--shell` sends its
generated command through the same guard. Literal inspection commands such as
`pwd`, `ls`, `cat`, `head`, `tail`, `wc`, `id`, `whoami`, `uname`, `ps`, `df`,
`du`, `stat` and `readlink` run automatically. Read-only forms of `date`,
`hostname`, `ss`, `ip`, `sort` and `systemctl` are explicitly checked.
Pipelines of recognized inspection commands are supported.

Automatic execution passes literal arguments directly to trusted, root-owned
system executables; it does not evaluate a shell, expand variables, expand
globs or apply user aliases. Use literal paths to avoid extra prompts.
Deletion, installation, sudo, scripts, interpreters, unknown programs,
redirection and command chains require typing **yes**. Any other answer,
unavailable input or a policy failure refuses execution. Approved commands run
through Bash without profiles. Commands time out after 300 seconds, and the
runner terminates process groups it started on timeout or launch failure.
Interactive programs and sudo password entry should be run directly in your
terminal; captured tool execution has no interactive standard input.

This guard is an approval convenience, not an OS sandbox. It runs with the
signed-in user's permissions. Keep the patched installation in place; manually
upgrading ShellGPT can overwrite the compatibility and approval patches.
`--shell --no-interaction` only prints a command; piping that output into Bash
would bypass this guard.

## Verification

Setup runs the command-policy suite and offline SDK/CLI checks automatically.
To repeat offline checks without reinstalling:

```bash
~/.local/share/shellgpt-stepfun/venv/bin/python -m unittest discover -s . -p test_linux_guard.py -v
~/.local/share/shellgpt-stepfun/venv/bin/python ./verify_shellgpt_parrot.py --offline
```

After saving a valid API key, run three small, billable live API tests:

```bash
~/.local/share/shellgpt-stepfun/venv/bin/python ./verify_shellgpt_parrot.py --live
```

These verify a text response, automatic `pwd` execution and an automatic `date`
tool round trip, including StepFun's reasoning-content continuation. The live
verifier redacts the configured key from captured output.
