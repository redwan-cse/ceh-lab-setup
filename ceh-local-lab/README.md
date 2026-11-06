# Local Hyper-V lab

For a new target or network, use the [main setup commands](../README.md).
This folder covers the existing lab on physical Windows host **Redwan-PC**.

## Machines and daily use

Verified topology: `CEH-Lab-Switch` (Internal), NAT `10.10.10.0/24`, host gateway
`10.10.10.1`. All five CEH VMs were Running during the audit.

| VM | Address | Login / role |
|---|---|---|
| Win11-Client | 10.10.10.11 | Win11-Client; workstation |
| ParrotOS Sec | 10.10.10.13 | redwan or attacker; Linux workstation |
| WinServer-2019 | 10.10.10.19 | Administrator; standalone WORKGROUP server |
| WinServer-2022 | 10.10.10.22 | Administrator; standalone WORKGROUP server |
| Android-8.1-Target | 10.10.10.9 | Android 8.1.0; Mobile Target (ADB), TCP/5555 |

AD/DNS, IIS/FTP and SQL exercise roles are not provisioned. Do not use `.19`
as DNS until it runs a working DNS service. Standalone Windows DNS is
`8.8.8.8`, `1.1.1.1`; domain members need their domain DNS.
See [verified health and limits](HEALTH-REPORT.md).

1. Keep the physical host on AC. Host AC sleep/hibernation are Never; battery
   sleep remains 10 minutes.
2. Start Parrot and the needed targets in Hyper-V Manager. Each should use
   `CEH-Lab-Switch`. **Connect** opens a guest's local screen.
3. Connect from the host terminal:

```powershell
ssh attacker@10.10.10.13
ssh Win11-Client@10.10.10.11
ssh Administrator@10.10.10.19
ssh Administrator@10.10.10.22
```

Use `hostname` and `whoami` to identify the current machine/account. The host's
`J:` project path does not exist inside a guest SSH session. Check a new SSH
host fingerprint against the intended VM before accepting it.

From the repository root on the physical host, check networking:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Test-CehLab.ps1 -SkipHyperV
```

Omit `-SkipHyperV` in Administrator PowerShell for Hyper-V inventory. An open
port proves connectivity, not full application health. If SSH fails, first try
`Test-NetConnection 10.10.10.13 -Port 22`, then check power, IP, switch and SSH.

For host inventory and optional AC keep-awake settings, run in Administrator
PowerShell on **physical Redwan-PC**, from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Get-HostLabState.ps1 -KeepAwakeOnAC -OutputPath .\host-health.json
```

Omit `-KeepAwakeOnAC` for inventory only. Save work before normal guest shutdown;
Hyper-V **Turn Off** removes power. Checkpoint restores rewind saved work.

## SSH keys

A public key authorizes one client/account. Keep the private key on that client.
If the Windows host needs a new key, run `ssh-keygen -t ed25519`. Add its public
key to the Windows Administrator login from the repository root:

```powershell
.\ceh-local-lab\Copy-SSHKey-To-Windows.ps1 -ComputerName 10.10.10.19
.\ceh-local-lab\Copy-SSHKey-To-Windows.ps1 -ComputerName 10.10.10.22
```

The helper keeps password authentication enabled and expects the standard
Windows OpenSSH Administrator key-file configuration.

## Parrot accounts and sleep prevention

`redwan` is the original desktop/sudo account with verified per-user ShellGPT.
`attacker` is an additional sudo user: password SSH, host public-key SSH and
password-authenticated sudo were tested. No passwordless-sudo rule was added.
SSH directory/file modes are 700/600. Passwords are not stored here. ShellGPT
and its API key are per-user; use the [Linux setup command](../README.md)
separately for each account that needs it.

To reproduce the attacker account setup, from the repository root on the host:

```powershell
scp .\ceh-local-lab\Create-ParrotAttacker.sh redwan@10.10.10.13:
scp "$env:USERPROFILE\.ssh\id_ed25519.pub" redwan@10.10.10.13:host-login-key.pub
ssh redwan@10.10.10.13
```

Then in Parrot:

```bash
bash ~/Create-ParrotAttacker.sh ~/host-login-key.pub
```

It prompts for the password. **Rerunning resets that password.** To verify sudo,
log in as attacker and run `sudo -k; sudo id -u`; after the password, expect `0`.

Parrot's five sleep/hibernate targets are persistently masked, with systemd
logind/sleep drop-ins. Copy `keep-parrot-awake.sh` to Parrot to apply or check:

```bash
sudo bash keep-parrot-awake.sh
bash keep-parrot-awake.sh --check
```

`disable-unused-parrot-services.sh` disables only four named optional services
when failed, without uninstalling tools. Configure before re-enabling them for
an exercise.

## Android mobile target

Generation 1, 2 CPUs, 2 GiB RAM. Verified interface `wifi_eth`, IP `10.10.10.9/24`,
gateway `10.10.10.1`, DNS property `net.dns1=8.8.8.8`, ADB TCP/5555. From Parrot:

```bash
adb connect 10.10.10.9:5555
adb devices
adb -s 10.10.10.9:5555 shell
```

Expect `10.10.10.9:5555 device`. In the Android shell:

```sh
getprop ro.build.version.release
ip -4 addr show
ip route
getprop service.adb.tcp.port
```

Both TCP and actual ADB shell were verified. Recheck after reboot: the original
image used manual networking. If unreachable, check VM power/switch settings,
then its root console with Alt+F1 (Alt+F7 returns to the GUI). Confirm interface
names before applying the source guide's image-specific network commands. Keep
ADB on the internal lab network.

Approved checkpoint recovery restored working ADB on 2026-11-06 after saving
current state. The helper is **inspection-only** by default. On physical
Redwan-PC in Administrator PowerShell, from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Restore-AndroidAdbCheckpoint.ps1
```

Its explicit `-RestoreAdbCheckpoint` flag creates a current-state checkpoint,
then rewinds Android's disk/RAM. Preserve work and review the restore before
using that flag. Do not restore automatically every session. Recovery details
are in the [health report](HEALTH-REPORT.md).

## Original scripts and rebuild reference

- `enable-ceh-ssh-windows-server.ps1`: original local installer; can assign
  `10.10.10.19` if its expected subnet is absent. Use only for this lab.
- `setup-openssh-windows-universal.ps1`: original proven SSH script, unchanged.
  The maintained generic version is under `../universal/windows`.
- `Set-StandaloneLabDns.ps1`: local DNS correction; refuses domain members,
  domain controllers and active DNS servers.
- [Gemini Hyper-V build guide](reference/gemini-hyper-v-guide.md): unchanged
  historical source supplied on 2026-11-06. SHA256:
  `580C949946DF945E5D8B139938F82EF81ACE8B8CB82CEB5070D30FB5E4A5E9C8`.

The source records VM creation and the Android-x86 8.1-r6 installation that
produced this Android 8.1.0 target. Its server role labels are planned exercises;
old installer URLs, network assignment blocks and firewall-disable examples are
historical. Use maintained setup on new machines. Existing Windows lab firewalls
were disabled before the audit; new installs should keep firewalls enabled and
allow intended services explicitly.
