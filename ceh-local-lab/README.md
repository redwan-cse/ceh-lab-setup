# CEH local lab

This folder records the tested local environment and preserves the two original
working SSH scripts. For another network, use ../universal instead.

Start with the [beginner guide](BEGINNER-GUIDE.md) and [current health report](HEALTH-REPORT.md).
The [Gemini reference](reference/README.md) records the supplied original guide
and explains corrections made after inspecting the real machines.

| Host | User | Verified system |
|---|---|---|
| 10.10.10.11 | Win11-Client | Windows 11 |
| 10.10.10.19 | Administrator | Windows Server 2019 Standard |
| 10.10.10.22 | Administrator | Windows Server 2022 Standard |
| 10.10.10.13 | redwan / attacker | Parrot Security 7.4; attacker has tested sudo and key/password SSH |
| 10.10.10.9 | Android root console / ADB | Android-8.1-Target, Mobile Target (ADB), verified TCP/5555 |

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

The Windows guests are currently standalone WORKGROUP machines. AD/DNS and the
planned web/FTP/SQL roles need separate provisioning. The standalone resolver
pair is 8.8.8.8 and 1.1.1.1; do not use .19 as a DNS server until it actually runs DNS.

Useful maintenance tools:

- [Android ADB guide](ANDROID-ADB.md): verified mobile target and checkpoint recovery.
- [Parrot accounts](PARROT-ACCOUNTS.md): attacker sudo/key access and reusable
  `Create-ParrotAttacker.sh` helper with an interactive password prompt.
- `Test-CehLab.ps1`: read-only host inventory and network checks.
- `Get-HostLabState.ps1`: elevated Hyper-V snapshot; `-KeepAwakeOnAC` additionally
  disables automatic host sleep/hibernation on AC, leaving battery/display settings alone.
- `keep-parrot-awake.sh`: apply persistent guest sleep/hibernate blocking on Parrot;
  `--check` verifies the masks without changes.
- `disable-unused-parrot-services.sh`: local static-address VM only; disables
  only the four named optional services if currently failed, without uninstalling tools.
- `Set-StandaloneLabDns.ps1`: known local workgroup guests only; refuses domain
  members/DCs and active DNS servers before setting public resolvers.

No passwords, API keys or private SSH keys are included. The supplied guide and
reviewed [conversation summary](conversation-summary.md) are now included.
