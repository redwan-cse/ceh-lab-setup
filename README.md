# ceh-lab-setup

**Exam setup with evidence logs:** see [exam/README.md](exam/README.md) for
OpenRouter DeepSeek for the exam, StepFun for local practice, API keys and
Markdown terminal logs in folders named by IP. [Real tool challenges](exam/LAB-CHALLENGES.md).
The [CEH tools reference](docs/ceh-tools/README.md) includes the local inventory,
commands, workflows and Windows alternatives. It does not install tools.

ShellGPT setup for CEH practice: one `sgpt` command, DeepSeek for exams and
StepFun as a manual choice for local practice. The exam setup below uses
provider-default reasoning and preserves Markdown evidence by IP.

## Quick start

Clone once and enter the repository:

```text
git clone https://github.com/redwan-cse/ceh-lab-setup.git
cd ceh-lab-setup
```

For an existing clone, run `git pull --ff-only`. This private repository requires
GitHub access. Run the following command **on the machine you want to configure**,
from the repository folder.

### Exam setup with IP-based transcripts

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Setup-Exam.ps1
```

Parrot / Debian-based Linux, as your normal user:

```bash
bash ./exam/setup-exam.sh
```

Fresh installs select OpenRouter `deepseek/deepseek-v4.1-flash-1017`, prompt for its key
and save `terminal.md` plus `findings.txt` under `Desktop/CEH-Exam/<IP>`.
They check the private Python environment and local collector prerequisites
first. Only missing prerequisites are offered for installation, with one
consent prompt; declining or running noninteractively installs nothing. Sudo,
UAC or credential authentication may still need its own OS prompt. There are
no CEH bulk-tool installs, OS upgrades/removals, or SSH, firewall, Defender or
network-setting changes. See [the exam guide](exam/README.md) for details.
If Git is unavailable, download and extract the repository ZIP, then run the
same setup command from its folder.

After setup, open a new terminal and check the actual configured selection
without a paid request:

```text
sgpt --model-info
sgpt "init the machine"
```

Initialization runs native local checks for host addresses, routes, DNS, cached
neighbors and capabilities. It does not scan neighbors. To choose a different
provider later, run one switch command from the repository:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\exam\Switch-Model.ps1 stepfun
# To return to the exam default, replace stepfun with deepseek.
```

```bash
bash ./exam/switch-model.sh stepfun
# To return to the exam default, replace stepfun with deepseek.
```

The switch updates one active endpoint/model/key together, with no reinstall
or API call. A missing key is requested securely. There is no automatic
fallback. All normal use remains `sgpt`; provider histories stay isolated.
Setup can recover missing private Python components, but missing Internet,
permissions, quota or an unsupported OS can still stop work with a clear error.

## Legacy universal StepFun / SSH setup

The commands below are the older universal setup. Its StepFun high-reasoning
setting is a custom adapter option, not a native ShellGPT 1.5.1 feature. The
current exam setup above uses provider defaults. Use the exam setup for the
single-command workflow and evidence logging.

### Windows 11 / Windows Server 2019 or 2022

Open **Windows PowerShell as Administrator** under the account that will use
ShellGPT, then run this one command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\universal\Start-CehLab.ps1
```

Sets up OpenSSH, reuses or installs Python, installs ShellGPT, applies the
StepFun configuration and asks for the API key with hidden input. Password and
public-key SSH stay enabled. It does not copy your SSH key automatically.

### Parrot / Debian-based Linux

Open a terminal as your **normal user**, then run this one command:

```bash
bash ./universal/linux/setup-shellgpt-parrot.sh
```

Installs ShellGPT in a private Python environment, applies the StepFun
configuration, checks it offline and asks for the API key with hidden input.
Sudo is used only for missing Python/venv prerequisites. Python 3.10+ is required.
This command configures ShellGPT; it does not install or change Linux SSH.
Parrot Security 7.4 is the tested Linux target; macOS and other distributions
are not supported by this installer.

### Use it

Open a **new terminal** after setup:

```text
sgpt --version
sgpt "Show the current directory"
sgpt --shell "List files in the current directory"
sgpt --repl lab "Help me inspect this machine"
```

Recognized inspection commands run automatically. Deletion, installation,
scripts and other unrecognized commands ask for approval. The guard runs with
your user's permissions; it is not an OS sandbox.

## Legacy universal API key and reruns

Enter the key at the setup prompt. Press Enter to retain the saved StepFun key.
Keys are stored locally in `OPENAI_API_KEY` inside:

| OS | Key file | Protection |
|---|---|---|
| Windows | `%USERPROFILE%\.config\shell_gpt\.sgptrc` | Current user/SYSTEM file permissions |
| Linux | `~/.config/shell_gpt/.sgptrc` | File mode 600, directory 700 |

These files contain plaintext credentials protected by OS permissions. Never
commit them. ShellGPT is configured separately for each user. Rerunning setup
refreshes the pinned installation and its managed settings; it retains a saved
key only when its existing provider is recognized as StepFun. Back up custom
settings before reinstalling. Live requests need Internet access and a valid
StepFun key. Setup checks offline and does not call the paid API automatically.

## Legacy universal options for timed labs

From the repository root on Windows:

```powershell
# ShellGPT only; no SSH changes or elevation required.
powershell -NoProfile -ExecutionPolicy Bypass -File .\universal\Start-CehLab.ps1 -SkipSsh

# SSH only, without Python/ShellGPT.
powershell -NoProfile -ExecutionPolicy Bypass -File .\universal\Start-CehLab.ps1 -SkipShellGpt

# Leave API-key entry for later.
powershell -NoProfile -ExecutionPolicy Bypass -File .\universal\Start-CehLab.ps1 -NoApiKeyPrompt
```

On Linux, append `--no-api-key-prompt` to skip key entry. To enter or replace
it later, from the repository root run:

```bash
python3 ./universal/linux/prompt_api_key.py
```

For Windows without Git, copy only
[Start-CehLab.ps1](universal/Start-CehLab.ps1) and run
`powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-CehLab.ps1` there.
For Linux, copy the entire `universal/linux` folder and run its setup script.

Universal setup does not hard-code the local lab's IP addresses, subnet,
gateway or DNS. Windows SSH preserves networking and existing firewall rules;
its own inbound rule permits any reachable client by default. Use
`-AllowedClients CLIENT_IP_OR_CIDR` to narrow that rule. Other existing rules
may still allow access. Downloads, administrator/sudo permissions and network
reachability remain prerequisites. Setup does not create VMs or exercise roles.

## More help

- [Local Hyper-V lab: daily use, SSH keys, Parrot and Android](ceh-local-lab/README.md)
- [Shared CEHv13 tools library](ceh-local-lab/README.md#shared-cehv13-tools)
- [Verified lab health and outstanding work](ceh-local-lab/HEALTH-REPORT.md)
- [Windows source, recovery options and verification](universal/windows/README.md)
- [Linux details and verification](universal/linux/README.md)

Source lives under `universal/windows` and `universal/linux`. After changing
Windows source, rebuild its portable launcher with
`powershell -NoProfile -ExecutionPolicy Bypass -File .\universal\Build-SingleFile.ps1`.
