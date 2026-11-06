# Local lab health — 2026-11-06 (Asia/Dhaka)

This report distinguishes checks that passed from work that is still pending.
It does not claim that every optional CEH service has been provisioned.

| Machine | Verified working | Remaining limits |
|---|---|---|
| Windows host `.1` | All 5 CEH VMs Running on the verified Internal switch; active NAT; host AC sleep/hibernate set to Never | Keep the host powered on; battery settings were not changed |
| Windows 11 `.11` | Static IP/gateway, corrected DNS, SSH key login, password/public-key SSH enabled, SMB2/445, ShellGPT high reasoning; 11 offline and 3 live checks passed | WORKGROUP; pending Windows servicing reboot; RDP not listening |
| Parrot `.13` | Static IP/gateway/DNS, SSH, UTC time, 3 live ShellGPT checks, 5 sleep targets masked; attacker account with tested sudo/password/key SSH | Optional tools need exercise-specific setup; ShellGPT remains per-user for redwan |
| Server 2019 `.19` | Static IP/gateway/DNS, SSH key login, both SSH auth methods, SMB2/445, 3 live ShellGPT checks | WORKGROUP; AD DS/DNS not installed; pending servicing reboot; RDP not listening |
| Server 2022 `.22` | Static IP/gateway, corrected DNS, SSH key login, both SSH auth methods, SMB2/445, authorized key configured, 3 live ShellGPT checks | WORKGROUP; IIS/FTP/DNS/SQL services not provisioned; RDP not listening |
| Android `.9` | Android-8.1-Target, Mobile Target (ADB), Android 8.1.0; ADB device online; wifi_eth 10.10.10.9/24, gateway .1, DNS 8.8.8.8, TCP/5555 | Recovered using the ADB checkpoint after preserving current state; recheck after reboot |

## Repairs made

- Parrot: masked `sleep.target`, `suspend.target`, `hibernate.target`,
  `hybrid-sleep.target` and `suspend-then-hibernate.target`; installed systemd
  logind/sleep drop-ins. Repeated `keep-parrot-awake.sh --check` passed without
  suspending, restarting or logging out the guest.
- Parrot: disabled only the four currently failed optional boot services
  (`cpupower-gui`, `hostapd-wpe`, `isc-dhcp-server`, `sslh`) and cleared their
  failed states. Logs showed no wireless device, no DHCP configuration and an
  `sslh` placeholder address; CPU tuning also failed inside the VM. No tools
  were removed. The final failed-unit list was empty; these services can be
  configured and enabled deliberately for a relevant exercise.
- Windows 11: upgraded the earlier non-tool ShellGPT setup to the tested guarded
  tool/automatic-shell configuration, preserving its existing StepFun key.
- Server 2022: saved the lab API key after explicit destination approval and
  passed real text, shell and tool-continuation tests.
- Windows 11 and Server 2022: replaced the inactive `.19` DNS backup with
  `1.1.1.1`; the current standalone pair is `8.8.8.8`, `1.1.1.1`. Static IPs
  and routes were preserved. Domain/DC users need their domain DNS instead.

All four configured ShellGPT guests passed live text, automatic inspection
shell execution and automatic tool-call continuation with step-5-preview/high.
No credentials or raw logs are included in this report.

## Completed host check on the physical PC

The initial automation session lacked Hyper-V administrator rights. The user
then ran the audit successfully on physical Redwan-PC. All five CEH VMs were
Running/Operating normally on the actual Internal CEH-Lab-Switch; NAT was active
for 10.10.10.0/24. Host AC sleep and hibernation are now **0 (Never)**, rechecked
with powercfg. Battery sleep remains 10 minutes; display settings are unchanged.

Android has 2 vCPUs/2 GiB RAM (Generation 1); Parrot has 4 vCPUs/8 GiB
(Generation 2); each Windows guest has 4 vCPUs/4 GiB (Generation 2).
An unrelated UbuntuServerPro VM was Off on External Bridge and was left alone.
The host had approximately 64 GiB RAM with 18 GiB free at collection.

To repeat it, open a **new Windows PowerShell window from the physical host's Start menu**
using **Run as administrator**. Run `hostname`: it must say `Redwan-PC`.
The `J:` project path is on that host and will not exist inside an SSH-connected
Windows VM just because the terminal application itself is on the host.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "J:\MyProjects\ceh-lab-setup\ceh-local-lab\Get-HostLabState.ps1" -OutputPath "J:\MyProjects\ceh-lab-setup\host-health.json" -KeepAwakeOnAC
```

This records VM states, switch membership, checkpoints and NAT, then disables
automatic host sleep/hibernation on AC only. Battery/display settings remain
unchanged. Omitting `-KeepAwakeOnAC` makes it a read-only host snapshot.

Then repeat the regular checker:

```powershell
.\ceh-local-lab\Test-CehLab.ps1 -OutputPath .\lab-health.json
```

## Android and optional roles

Initially `.9` was absent even though Hyper-V confirmed Android was running
on the correct switch. After explicit user approval, the recovery helper saved
current state as `before-adb-recovery-20261106-135746-13dca2`, then restored the
existing ADB checkpoint. Host TCP/5555 and actual ADB shell checks from Parrot
now pass. See [Android ADB instructions](README.md#android-mobile-target). No other guest was restored.

The new attacker user on Parrot has sudo membership and this host's public key.
Password SSH, key-only SSH and password-authenticated sudo were tested. Its
.ssh/key file are attacker-owned with modes 700/600. Password login stays enabled.
No password or private key is stored in the repository.

The source guide's domain-controller/web/FTP/SQL labels were plans, not service
installation steps. No domain join or new server roles were performed during
this audit. Provision them deliberately for an exercise after choosing its
domain, service and credential requirements.

Current guest Windows firewalls are disabled, matching the historical lab setup.
They were not toggled during this audit. This is not a recommendation to disable
firewalls on a general-purpose or externally connected machine. The intended
internal-switch membership was confirmed by the elevated audit.

Windows guests use a Pacific display time zone, while Parrot/host use Dhaka.
Their UTC clocks matched during checks; differing displayed dates were not clock
drift. Android was restored only after approval and a current-state checkpoint;
the audit commands did not reboot or checkpoint-restore the Windows guests or Parrot.

## Installer validation scope

The universal Windows SSH source passed PowerShell 5.1 config, release-asset
and service-path fixtures. The official OpenSSH MSI download had a matching
digest and valid Microsoft signature; it was not installed on the physical host.
The portable Windows launcher was tested by itself on Server 2022, including
missing-Python bootstrap. Before/after IP, DNS and route checks confirmed SSH
setup preserved its network. Linux setup passed policy, provider-key and offline
SDK/CLI tests plus partial-venv recovery on Parrot. All four configured ShellGPT
guests passed the three live API checks described above. These are tested local
targets, not a guarantee for every OS, proxy, firewall or domain policy.

## Shared tools and Defender follow-up

The shared library was completed on Server 2022 at `C:\CEH-Tools`, published as
`\\10.10.10.22\CEH-Tools`. It contains 20 prerequisite/module folders and
32,837 files (9,666,733,364 bytes of original extracted file data). All files
passed size/ZIP-CRC checks after uploaded archives passed SHA256 validation.
`CEHv13 ISO.zip` was excluded; the host's 21 original ZIPs remain intact.
Embedded archives were preserved rather than recursively unpacked or executed.

Defender initially quarantined the uploaded Module 05 ZIP. The user then
requested active scanning disabled on all three Windows lab VMs and manually
turned off Windows 11 Tamper Protection. Real-time, behavior and IOAV runtime
status are now false on `.11`, `.19`, `.22`, with script scanning disabled.
Defender remains installed; the physical host was not changed. No folder
exclusions were added. The disable/restore helper preserves original preferences
inside each guest and checks the effective runtime state. Future Windows/policy
changes may reactivate scanning; verify before later sessions.

All three Windows accounts mapped `T:` and passed directory-read and denied-
file-creation checks using the dedicated non-admin `cehshare` identity. The
share grants that account Read and administrators Full maintenance access.
SMB encryption is required. Windows may ask for credentials after a later sign-in;
an already-open desktop may need its own reconnect.

Parrot's unrelated full upgrade completed without interruption. `cifs-utils`
was then installed and `/mnt/ceh-tools` mounted read-only with SMB 3.1.1, seal,
nosuid/nodev/noexec. A managed fstab automount and root-only credential file
support later starts. The five sleep/hibernate targets remain masked.
Android ADB received the 5,617,024-byte library inventory from that mount at
`/sdcard/Download/ceh-tools-manifest.json`; it does not have a direct SMB mount.
The Windows guests' existing disabled-firewall state was preserved; the added
lab-scoped SMB allow rule alone does not restrict other existing access.
The exact documented setup command passed a full rerun, verifying the existing
library and republishing the same share without transferring or extracting
archives again. Parrot's existing-mount/persistence rerun also passed, with
root-owned credential directory/file permissions confirmed as 700/600.
