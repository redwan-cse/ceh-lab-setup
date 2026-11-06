# Quick setup for a new, temporary lab

Copy **Start-CehLab.ps1** to the Windows target. Open Windows PowerShell as
Administrator, change to that folder, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Start-CehLab.ps1
```

This single file contains the required helper scripts. It configures OpenSSH,
installs Python when missing, installs ShellGPT 1.5.1, selects step-5-preview
with high reasoning effort, and prompts securely for your StepFun API key.
No personal token, API key, SSH password or private key is embedded.

The network can have a completely different address range. The SSH setup
does **not** set IP addresses, prefixes, routes, gateways, DNS or adapter state.
It enables password and public-key authentication. Its default inbound SSH rule
allows Any remote address, which suits a temporary lab with unknown routing.
Limit the rule created by this kit when you know your client address:

```powershell
.\Start-CehLab.ps1 -AllowedClients 192.0.2.25
```

Those are example addresses only; nothing is tied to the local lab's subnet.
Existing firewall rules are preserved. Another existing SSH allow rule may
still permit additional clients; limiting this kit's rule is not a guarantee
that the entire existing firewall policy is equally restrictive.
Host firewall settings cannot bypass cloud security groups, VPN routing,
upstream firewalls, a disabled NIC or an absent network connection. Administrator
rights and access to the relevant download endpoints are still required.
Windows Server 2019/2022 and Windows 11 have been used in the local tests;
an unknown OS/version is not automatically a verified target.

## Useful options

```powershell
# Per-user ShellGPT only; leave the SSH service alone.
.\Start-CehLab.ps1 -SkipSsh

# SSH only; no Python, ShellGPT or API-key prompt.
.\Start-CehLab.ps1 -SkipShellGpt

# Noninteractive setup: leave API-key configuration for later.
.\Start-CehLab.ps1 -NoApiKeyPrompt

# If you specifically need the original lab authentication tuning.
.\Start-CehLab.ps1 -EnableLabAuthTuning
```

The MSI install path avoids waiting on Windows Update when OpenSSH is missing.
`-InstallMethod Capability` requests the Windows optional feature instead.
An already installed SSH service is reused. Downloads and package installation
take time; completion time depends on the lab's Internet connection and policy.
Download the kit to your own PC before a timed lab, then copy the single script
over. This private repository requires GitHub authentication to download from it;
the copied launcher does not need your GitHub login.

Routine inspection commands run automatically. Deletion, installation, scripts
and unknown commands still require approval. The command guard is an approval
convenience, not an operating-system sandbox.

## Source files and Linux

`windows` contains the reviewable PowerShell/Python source and verification
scripts. `linux` contains the separate Debian/Parrot virtual-environment setup.
Use the Linux README on a Linux target; the Windows launcher does not run there.

After source changes, rebuild the single-file Windows launcher on your own PC:

```powershell
.\Build-SingleFile.ps1
```

Keep API keys in the target's protected ShellGPT config, never in these source
files or Git. Check the Windows/Linux READMEs for exact config locations and
live verification commands.
