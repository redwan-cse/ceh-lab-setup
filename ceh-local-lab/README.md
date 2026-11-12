# Local Hyper-V lab

For a new practice target or network, use the [normal lab setup commands](../README.md#normal-local-lab).
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
and its API key are per-user; use the [normal lab setup guidance](../README.md#local-shellgpt-and-ssh-setup)
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

## Defender scanning controls for the three Windows lab VMs

At the user's request, real-time, behavior, downloaded-file/attachment (IOAV)
and script scanning were disabled and verified on `.11`, `.19` and `.22`.
Defender remains installed; its service/platform was not removed. The physical
host was not changed. No folder exclusions were added for this deployment.

From the repository root on Redwan-PC:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Set-LabDefender.ps1 -Mode Status
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Set-LabDefender.ps1 -Mode Disable
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Set-LabDefender.ps1 -Mode Restore
```

The helper targets only the three known Windows lab VMs over SSH. Disable saves
the four original preferences in the guest account's
`%LOCALAPPDATA%\CEHLab\defender-before.json`. Restore uses that snapshot and
verifies runtime protection state. It does not bypass Tamper Protection: turn
that setting off through Windows Security in the guest if Windows blocks the
change. Tamper Protection itself must also be re-enabled through that UI when
returning the guest to normal protection.

Windows/policy can reactivate scanning; use Status before another lab session.
[Microsoft documents automatic real-time protection reactivation](https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-security-center-antivirus).

## Shared CEHv13 tools

**Deployed and verified on 2026-11-06.** The read-only share is live on Server
2022. Its dedicated account uses the existing Windows lab password, entered
privately; no password is saved in these scripts. The original archives stay
unchanged on the physical host. All three Windows accounts passed read/write-
denial checks, Parrot's encrypted persistent mount works, and Android file
delivery through ADB passed. See the [health report](HEALTH-REPORT.md).

Source on Redwan-PC:

```text
D:\CEHv13\CEHv13_Tools_26-Nov-2025\
```

The 2026-11-06 inventory found 20 included ZIP archives: Lab Prerequisites and
Modules 02–20. Exclude **exactly `CEHv13 ISO.zip`**. The included ZIPs occupy
7.19 GiB and contain 49,052 entries totaling about 9.00 GiB after first-level
extraction. All 32,837 extracted files passed size and ZIP CRC verification.
The ZIP entries are not encrypted; embedded archives may have their own rules.
Some relative paths are 259 characters long, so extraction must support long paths.

### Selected layout

| Item | Value |
|---|---|
| File server | Server 2022, `10.10.10.22`, hostname `WIN-L4HLUP8AT8K` |
| Extracted library | `C:\CEH-Tools` inside that VM |
| SMB share | `\\10.10.10.22\CEH-Tools` |
| Guest access | Dedicated non-administrator `cehshare` account, read-only |
| Windows drive | `T:` persistent machine-wide mount on all three Windows VMs; visible under This PC |
| Parrot mount | `/mnt/ceh-tools`, persistent, encrypted and read-only |
| Android | Copy selected files from the same library through ADB; browsing SMB requires a compatible Android client |

Server 2022 had about 43.7 GiB free at inspection, enough for the 7.19 GiB
staging ZIPs plus the 9 GiB extracted library and some working headroom.
Windows/Parrot users should copy tools into their own working directory before
editing them. A read-only master library prevents one VM from changing the
tools everyone else uses. A writable exchange share can be added separately
if needed later.

### Reusable deployment and connection commands

On Redwan-PC, from the repository root, with Python 3.10+, SSH/scp and working
Administrator SSH key access to Server 2022:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ceh-local-lab\Setup-CehToolsShare.ps1
```

The server also needs Python (already installed by the ShellGPT setup). The
command inventories/checksums ZIPs, resumes verified transfers, extracts with
long-path handling, verifies every extracted file and then prompts privately
for the share password. The master share uses SMB3 encryption, read-only share
and NTFS permissions for `cehshare`, and administrator maintenance access.
Existing unrelated directories, accounts and shares are refused. A rerun
verifies an existing complete library and skips transfer/extraction. Unexpected
existing or altered libraries require inspection rather than blind replacement.

Use `-PrepareOnly` to stop after verified extraction without publishing SMB.
`-SourcePath`, `-Server`, `-UserName`, `-LibraryPath` and `-LabSubnet` allow
explicit adjustments. Library paths must be dedicated drive-root CEH-Tools
folders, not OS/user folders.

Only after deliberately approving storage of lab tools in these VM folders,
add `-AllowLabDefenderExclusions`. For the selected layout it adds exactly:

```text
C:\CEH-Tools
C:\CEH-Tools-Staging
C:\Users\Administrator\ceh-tools-deployment\archives
```

This is an optional alternative; it was not used in the completed deployment.
The user instead requested the lab-wide scanning changes described above.
The exclusion option leaves Defender protection elsewhere active. Failed extraction staging is
preserved for inspection. Originals are never deleted. Verified copied ZIPs
are removed from server staging after successful share publication.

Once publication succeeds, copy `Connect-CehTools.ps1` to each Windows guest
and run it there in **Administrator PowerShell**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Connect-CehTools.ps1
```

Enter `WIN-L4HLUP8AT8K\cehshare` and its password. The helper uses native
`New-SmbGlobalMapping -Persistent $true -RequirePrivacy $true` to mount `T:`
for all local sessions, including the desktop, and lets Windows retain the
connection credential. The dedicated server account remains read-only for
everyone using this mount. No plaintext password is saved in source files.

The helper verifies 20 readable folders and denied file creation. `-DriveLetter`
selects another unused letter. It refuses to replace an unrelated mapping or
local disk. Old per-login mappings to this same library are replaced with the
machine-wide mount. The mounted drive was verified inside all three existing
desktop sessions and appeared in the **This PC** shell view. If an Explorer
window was already open, refresh that window.

For a fresh-session check, copy `Test-CehToolsVolume.ps1` to the guest and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Test-CehToolsVolume.ps1
```

This checks the native global mapping, encryption, folder listing and actual
manifest-file reading without another credential prompt. `-DesktopCheck`
additionally checks This PC when run in the logged-in desktop session.

Copy `mount-ceh-tools.sh` to Parrot and run after other package operations finish:

```bash
bash mount-ceh-tools.sh --persist
```

The script installs `cifs-utils` if needed, prompts for sudo and the share
password, and mounts `/mnt/ceh-tools` read-only with SMB3 encryption and
`nosuid,nodev,noexec`. With `--persist`, it adds a managed fstab automount and
saves the SMB credential in root-owned `/etc/samba/ceh-tools/credentials`
(directory 700/file 600). Without that flag it creates a temporary mount and
does not save the credential. Copy tools to a local workspace before using them.

The offline extraction fixtures can be repeated without touching course data:

```powershell
python -m unittest discover -s ceh-local-lab -p test_ceh_tools_library.py -v
```

Android ADB supports copying files, rather than automatically providing a
Windows-style network drive. Example after the Parrot mount is configured:

```bash
adb -s 10.10.10.9:5555 push /mnt/ceh-tools/PATH_TO_FILE /sdcard/Download/
```

The tested transfer placed the library's inventory at
`/sdcard/Download/ceh-tools-manifest.json`. Android is not configured with a
direct SMB mount; use ADB for selected files or configure an SMB-capable client.

References: [Microsoft SMB share creation](https://learn.microsoft.com/en-us/powershell/module/smbshare/new-smbshare)
and [Android ADB file transfer](https://developer.android.com/tools/adb#copyfiles).

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
