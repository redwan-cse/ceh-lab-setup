# CEH local lab

This folder records the tested local environment and preserves the two original
working SSH scripts. For another network, use ../universal instead.

| Host | User | Verified system |
|---|---|---|
| 10.10.10.11 | Win11-Client | Windows 11 |
| 10.10.10.19 | Administrator | Windows Server 2019 Standard |
| 10.10.10.22 | Administrator | Windows Server 2022 Standard |
| 10.10.10.13 | redwan | Parrot Security 7.4 |

`enable-ceh-ssh-windows-server.ps1` contains the local 10.10.10.0/24 settings
and can assign 10.10.10.19 when its expected subnet is absent. Treat it as a
local-lab script. `setup-openssh-windows-universal.ps1` here is the original
tested version, retained unchanged for reference. The improved generic version
is under ../universal/windows.

`Copy-SSHKey-To-Windows.ps1` adds the host PC's public key to a Windows
Administrator key file while keeping password authentication enabled. A key
installed from one client/account does not authorize a different client/account.
Use `hostname` and `whoami` to check whether a terminal is already inside SSH.

The `windows` folder preserves the tested ShellGPT setup used earlier in this
lab. It uses ShellGPT 1.5.1, step-5-preview, the Step Plan API endpoint, high
reasoning effort and selective command approval. Its original clean reinstall
behavior resets configuration and keys; read its instructions before rerunning.
The generic Linux version under ../universal/linux was also tested on Parrot.

No passwords, API keys or private SSH keys are included. The future Gemini
conversation summary belongs in conversation-summary.md after the user supplies it.
