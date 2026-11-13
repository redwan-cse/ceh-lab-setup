# ShellGPT command reference

For this repository's **exam setup with ShellGPT 1.5.1** on Parrot/Linux and
Windows PowerShell. Install it first using the [main setup guide](../README.md).
Custom exam options require that setup; a stock ShellGPT installation does not
provide them. Use the account where you installed sgpt.

## Start here

```text
sgpt
sgpt "init the machine"
sgpt --challenge 5 --repl challenge5
```

- `sgpt` opens normal interactive chat. Type tasks and follow-up messages there.
- `sgpt "Your task"` handles one request: it can run commands, inspect real
  output and choose the next action. You do not need `--shell` for execution.
- `sgpt --challenge 5 --repl challenge5` starts a named conversation and labels
  its evidence folder. Use Ctrl+C to stop the chat.

Routine operations use automatic approval. Installations, deletions, critical
changes and uncertain operations still require a human decision. Required
approval needs an interactive terminal; use `ssh -tt` for interactive SSH work.

## Standard ShellGPT options

These come from ShellGPT; the exam wrapper adds its workflow and logging.

| Command | Use |
| --- | --- |
| `sgpt --help` | Show standard ShellGPT options. The custom options below are documented here separately. |
| `sgpt --version` | Show the installed version. |
| `sgpt "Calculate SHA256 for sample.txt in the current folder"` | Perform a task through the normal command/action loop. |
| `sgpt --repl work` | Open an interactive conversation named `work`. |
| `sgpt --chat work "Continue from the previous results"` | Send one request using a saved conversation. |
| `sgpt --list-chats` | List saved conversation names for the active provider. |
| `sgpt --show-chat work` | Display that saved conversation; it may contain sensitive lab data. |
| `sgpt --shell "Show my current directory"` | Use ShellGPT's shell-command generation/execution interface. It can show its own interaction menu; prefer normal chat for multistep automatic work. |
| `sgpt --describe-shell "Get-ChildItem"` | Explain a command rather than execute it. Use an OS-appropriate command. |
| `sgpt --code "Write a Python function to calculate SHA256"` | Generate code text. This mode does not itself execute the generated code. |
| `sgpt --no-functions "Explain what a SHA256 digest represents"` | Request a text-only answer without tool calls. |

`--chat` keeps conversation history; `--challenge` labels evidence. They serve
different purposes. History is separated by provider. Each new process still
gets a new output folder, even when reusing a chat name.

## Custom exam options

These are implemented by this repository's `sgpt` wrapper.

| Option or request | Effect |
| --- | --- |
| `sgpt --model-info` | Show the configured provider, model and endpoint locally, without an API request. |
| `sgpt "init the machine"` | Collect local host/network facts using the native OS collector, then request a short model review. |
| `sgpt --init-lab` | Explicit form of initialization. |
| `sgpt --init-lab --local-only` | Collect local facts without the paid model review. |
| `sgpt --tool-help "nmap"` | Search the bundled tool reference locally, without an API request. Also try `hashing`, `SMB` or `tshark`. |
| `--challenge 5` | Label this process's session folder. Labels may contain 1–40 letters, digits, underscores or hyphens. |
| `--target-ip 10.10.10.9` | File evidence under that IPv4 address. This does **not** connect to the machine or change where commands execute. |
| `--tools-path "PATH"` | Remember an optional existing tool/file/folder location. It is never a prerequisite for normal work. |
| `--tool-rounds 60` | Set the main-agent continuation block to 60 rounds; range 1–100, default 40. A round can include multiple tool calls. Approval reviews are additional calls. |
| `--verbose` | Also display API usage, timing and routine status details. These are saved in the transcript even when hidden. Reasoning settings are unchanged. |
| `--manual-approval` | Disable AI approval review for this invocation. The literal routine-command fast path remains automatic. |
| `--profile NAME` | Advanced per-invocation provider selection using its saved key. Normally use the model switcher below to change the persistent default. |

Advanced profile names are `openrouter-deepseek`, `stepfun`, `gemini-carbon`
and `gemini-mix`. Fresh exam installs default to normal
`deepseek/deepseek-v4.1-flash-1017`; no batch model or automatic provider
fallback is selected. The stock `--model` option changes the requested model
on the active endpoint; it does not switch the provider's endpoint/key.

At the continuation limit, an interactive chat offers another block of rounds.
Reply `y` or `yes` to continue with existing results; successful commands do
not need to be repeated. This does not approve protected operations.

### Initialization and explicit discovery

```text
sgpt "init the machine"
sgpt --init-lab --local-only
```

Initialization collects addresses, routes/DNS, cached neighbors, host identity
and core capabilities. Cached neighbors do not prove current reachability.
Initialization does not actively discover other machines.

For explicitly authorized active discovery, replace the example range with the
range assigned in your task:

```text
sgpt --init-lab --scope 10.10.10.0/24 --discover
```

Discovery accepts IPv4 ranges of `/24` or smaller. An address mask/default route
does not establish permission to scan. The startup collector does not restrict
later assigned tasks to local hosts: supplied public lab URLs and ordinary
passive/public research are supported. [Scope details](README.md#initialize-and-inspect-safely).

## Parallel challenges and saved evidence

Run each command in a separate terminal:

```text
sgpt --challenge 5 --repl challenge5
sgpt --challenge 6 --repl challenge6
```

Then type each challenge's task into its chat. The initial one-shot prompt can
also supply the label naturally:

```text
sgpt "Challenge 5: calculate SHA256 for sample.txt in the current folder"
```

Each process creates a unique folder, including when labels match:

```text
Desktop/CEH-Exam/<IP>/sessions/
  challenge-5_<UTC-time>_<unique-id>/
    terminal.md
    findings.txt
    scripts/          (only when a script is needed)
  challenge-6_<UTC-time>_<unique-id>/
    terminal.md
    findings.txt
```

Without a label, the folder starts with `session_`. An ongoing chat stays in
its original folder. All final reports and work files belong in that session
folder; the exact path is printed at startup and supplied to sgpt.

`terminal.md` captures prompts, commands, actual output, replies and diagnostic
records. `findings.txt` contains only confirmed flags and how they were found.
It is not a general summary. Existing evidence is preserved. These files cover
sgpt activity, not unrelated terminal windows or GUI actions.

To save an observed finding, say in chat:

```text
The GUI on Android 10.10.10.9 displayed FLAG_VALUE after these steps: ...
Save that flag and how it was found, identifying it as my reported observation.
```

Replace placeholders with your actual observations. To resume after exiting,
reuse `--chat NAME` or tell sgpt the earlier report paths. Unsaved process
memory cannot be recovered. [Evidence details](README.md#markdown-evidence-by-ip).

## Useful requests inside normal chat

These are ordinary messages, not additional CLI flags:

| Message | Expected behavior |
| --- | --- |
| `Find the installed tshark command and show its version.` | Locate an available tool and check actual output. |
| `Use ~/Desktop/MyWordlists when this task needs a wordlist.` | Remember a real optional Linux location. |
| `Use C:\Users\Admin\Desktop\Tools for this task.` | Remember a real optional Windows location. |
| `If a script is needed, save a numbered version in this session and inspect its output.` | Create a script only when needed; keep versions in the evidence folder. |
| `Continue from the results already collected; do not repeat successful commands.` | Continue with available context/evidence. |
| `This check needs another Windows VM. Give me the request to paste into sgpt there and the results to bring back.` | Prepare a machine handoff without assuming remote access. |
| `This tool is GUI-only. Give me numbered steps and tell me exactly what output to report.` | Provide manual steps and request the observations needed to continue. |

Use real paths for your account. Tool paths are optional; ask for a specific
tool or wordlist when needed. For a machine handoff, paste the returned results
into the original conversation and identify the source machine/IP. Sessions
are not automatically connected or synced.

### Internal tools sgpt calls itself

These names are model tools, **not standalone terminal commands**:

| Tool | Purpose |
| --- | --- |
| `execute_shell_command` | Execute a command through the configured approval mechanism. |
| `init_machine` | Run the local native collector. |
| `find_ceh_tools` | Look up installed commands and bounded local tool/wordlist candidates. |
| `find_ceh_reference` | Search the bundled command/workflow reference. |
| `set_tools_path` | Remember an optional path you explicitly supplied. |
| `write_lab_script` | Create a numbered script version inside this session. |
| `run_lab_script` | Verify and run an owned script version after approval review. |
| `save_finding` | Save a confirmed flag and how it was found using command or user evidence. |

Ask for the task in normal language; sgpt chooses the needed tools.

## Switch models and update the setup

Run these helper scripts **from the repository root**, outside the sgpt chat.
The switcher selects the model and matching endpoint/key without reinstalling.
It asks for the selected provider's key if one has not been saved. Restart an
existing sgpt process after switching, then verify with `sgpt --model-info`.

**Parrot/Linux:**

```bash
bash ./exam/switch-model.sh stepfun
bash ./exam/switch-model.sh deepseek
sgpt --model-info
```

**Windows PowerShell:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 stepfun
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 deepseek
sgpt --model-info
```

The examples switch to StepFun and then back to DeepSeek; run only the switch
you want. For code updates, stop sgpt, run `git pull --ff-only`, rerun your
[OS setup command](../README.md), and open a new terminal. Pulling alone does
not refresh the installed runtime. Setup preserves keys and evidence.

For key replacement, log-reset previews, removal and Windows PATH recovery,
use the [full setup and troubleshooting guide](README.md#reset-remove-or-troubleshoot).
Never paste an API key into a chat prompt or command example.
