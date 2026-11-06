# Local lab health — 2026-11-06 (Asia/Dhaka)

This report distinguishes checks that passed from work that is still pending.
It does not claim that every optional CEH service has been provisioned.

| Machine | Verified working | Remaining limits |
|---|---|---|
| Windows host `.1` | `10.10.10.1/24` on the lab vEthernet adapter; `CEH-Lab-NAT` for `10.10.10.0/24`; guest Internet works | Elevated Hyper-V inventory and host AC sleep change await the host-only command below |
| Windows 11 `.11` | Static IP/gateway, corrected DNS, SSH key login, password/public-key SSH enabled, SMB2/445, ShellGPT high reasoning; 11 offline and 3 live checks passed | WORKGROUP; pending Windows servicing reboot; RDP not listening |
| Parrot `.13` | Static IP/gateway/DNS, SSH, synchronized UTC time, 3 live ShellGPT checks; all 5 sleep/hibernate targets persistently masked | Optional wireless/DHCP/multiplexer/CPU-tuning boot services require exercise-specific setup; physical host must remain awake |
| Server 2019 `.19` | Static IP/gateway/DNS, SSH key login, both SSH auth methods, SMB2/445, 3 live ShellGPT checks | WORKGROUP; AD DS/DNS not installed; pending servicing reboot; RDP not listening |
| Server 2022 `.22` | Static IP/gateway, corrected DNS, SSH key login, both SSH auth methods, SMB2/445, authorized key configured, 3 live ShellGPT checks | WORKGROUP; IIS/FTP/DNS/SQL services not provisioned; RDP not listening |
| Android `.9` | No successful network/ADB check at its expected address | No ARP, ping or TCP/5555 response from the lab; ADB reports no route. VM power state and console configuration need host-side inspection |

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

## Complete the host check on the physical PC

The automation session lacked Hyper-V administrator rights. Its elevation attempt
was canceled, so **no host power setting was changed**. The last observed host
AC sleep timeout was 18,000 seconds (5 hours); AC hibernation timeout was 0.
Parrot's guest masks cannot prevent physical-host sleep.

Open a **new Windows PowerShell window from the physical host's Start menu**
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

The guest network scan found `.1`, `.11`, `.13`, `.19` and `.22`; `.9` was absent.
That does not prove the Android VM is powered off. Check its Hyper-V state,
internal-switch attachment and local Android root console. The supplied image's
manual IP/ADB settings may have been lost after reboot. Follow the
[beginner guide](BEGINNER-GUIDE.md) and verify ADB before taking a new working
checkpoint. Do not restore an old checkpoint without considering later changes.

The source guide's domain-controller/web/FTP/SQL labels were plans, not service
installation steps. No domain join or new server roles were performed during
this audit. Provision them deliberately for an exercise after choosing its
domain, service and credential requirements.

Current guest Windows firewalls are disabled, matching the historical lab setup.
They were not toggled during this audit. This is not a recommendation to disable
firewalls on a general-purpose or externally connected machine. The intended
internal-switch membership still needs the elevated Hyper-V check.

Windows guests use a Pacific display time zone, while Parrot/host use Dhaka.
Their UTC clocks matched during checks; differing displayed dates were not clock
drift. No VM was rebooted or checkpoint-restored during the audit.
