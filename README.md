# ceh-lab-setup

SSH and StepFun ShellGPT setup kits for an authorized CEH lab.

**New to the project? Read the [beginner guide](ceh-local-lab/BEGINNER-GUIDE.md).**
It explains which computer to type on, starting the existing VMs, building a
lab, SSH, ShellGPT, Android recovery and basic troubleshooting.

| Folder | Purpose |
|---|---|
| [ceh-local-lab](ceh-local-lab/README.md) | Proven local scripts, known hosts and setup notes. Includes the two original SSH scripts unchanged. |
| [universal](universal/README.md) | Generic Windows copy-and-run launcher and separate Linux installer, independent of the local subnet. |

For a fresh Windows lab, copy `universal/Start-CehLab.ps1` onto the target and
run it from elevated Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-CehLab.ps1
```

ShellGPT uses version 1.5.1, model `step-5-preview`, endpoint
`https://api.stepfun.ai/step_plan/v1`, and `REASONING_EFFORT=high`.
Recognized inspection commands execute automatically; file deletion,
installation, scripts and unknown commands require approval.

The generic SSH setup preserves the target's network configuration. A different
IP/subnet is supported; network reachability, permissions and download access
are prerequisites. The universal README explains firewall scope and limitations.

For a read-only local check from the Hyper-V host:

```powershell
.\ceh-local-lab\Test-CehLab.ps1
```

Run it in Administrator PowerShell for Hyper-V inventory, or add `-SkipHyperV`
for network checks without elevation. Read the [latest health report](ceh-local-lab/HEALTH-REPORT.md)
for verified results and outstanding items; an open port alone is not a full
application-health test.

Passwords, API keys, private keys, runtime configs and raw logs are excluded.
The supplied Gemini guide is preserved with [provenance and corrections](ceh-local-lab/reference/README.md),
and the [setup summary](ceh-local-lab/conversation-summary.md) connects it to the
tested project. The archived guide is historical reference, not the default
script to run on a new machine.
