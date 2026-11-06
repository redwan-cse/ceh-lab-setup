# CEH Lab Setup

SSH and StepFun ShellGPT setup kits for an authorized CEH lab.

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

Passwords, API keys, private keys, runtime configs and logs are excluded.
The user's future Gemini summary can be added under ceh-local-lab after removing
credentials. No unsupplied conversation summary has been invented.
