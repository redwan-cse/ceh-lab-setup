# Supplied Gemini guide: setup summary

The user supplied `ceh_practical_hyper_v_lab_setup_guide.md` on 2026-11-06.
An exact copy and its provenance are in [reference](reference/README.md).
This summary reflects that document and the subsequent local review; it does
not invent a missing conversation transcript.

The intended lab uses Hyper-V, an Internal switch named `CEH-Lab-Switch`,
and Windows NAT for `10.10.10.0/24`. The host is gateway `10.10.10.1`;
the guest addresses are Android `.9`, Windows 11 `.11`, Parrot `.13`,
Server 2019 `.19` and Server 2022 `.22`.

The source explains VM creation, static guest addressing, an Android-x86 8.1-r6
installation, Parrot SSH access and Windows OpenSSH setup. It also records
password authentication and optional SSH public-key authentication for local
practice. Passwords, API keys and private keys are not part of this repository.

Review corrected several assumptions: both Windows servers are in WORKGROUP,
and AD DS/DNS/IIS/FTP roles are absent. Domain controller, web, FTP and SQL
labels in the source describe intended exercises, not a provisioned environment.
Server 2019 is not currently a usable DNS server. All Windows guest firewall
profiles were found disabled as part of the earlier lab setup; this is recorded
state, not the recommended default for new builds. Both servers also have no
SQL/MSSQL services. Windows SSH and SMB were reachable, SMB2 was enabled and
SMB1 disabled; RDP was not listening.

Windows 11 and Server 2022 used `.19` as backup DNS despite its missing DNS
service. Their DNS was corrected to `8.8.8.8`, `1.1.1.1`; Server 2019 already
used that pair. The guarded local DNS helper refuses domain members and domain
controllers rather than applying standalone DNS settings to them.

Parrot uses KDE Plasma/Wayland. The local keep-awake script was applied and
verified: all five sleep/hibernate targets are persistently masked, with
additional logind/sleep drop-ins. The physical host's observed AC sleep timeout
was still five hours, with AC hibernation disabled. Host UAC elevation was
canceled; no host power change or administrator Hyper-V inventory was completed.
NAT and the host gateway exist, but current VM power states and switch membership
remain unverified. The prepared host audit must be run from a fresh elevated
PowerShell on physical host `Redwan-PC`, not from a guest SSH prompt. The `J:`
repository path belongs to the host.

Android's expected `.9` address did not answer ARP, ping or ADB TCP checks.
Parrot discovery saw the host plus `.11`, `.13`, `.19` and `.22`; ADB reported
no route to `.9`. Android's VM state/console and its root-console networking/ADB
procedure were not verified or changed. This is not proof that the VM is off.

All four SSH-accessible guests passed fresh ShellGPT text, shell-command and
tool-round-trip API tests. Windows 11's guarded installer update preserved its
API key and passed 11 offline checks. Server 2022's API key setup was authorized,
saved in protected configuration and then passed the live checks. No key values
are included here. UTC clocks agreed; the Windows Pacific time-zone display was
not clock drift. Windows 11 and Server 2019 reported pending reboots, and no
reboot was performed during this review.

Four failed optional Parrot boot services were disabled without removing their
tools: cpupower-gui, hostapd-wpe, isc-dhcp-server and sslh. They were not configured
for this static-address, synthetic-Ethernet VM; the final failed-unit list was
empty. Enable them deliberately only after configuring the relevant exercise.

The maintained universal kit replaces the historical SSH install fallback,
preserves addressing and DNS, and separates Windows setup from Linux setup.
The [beginner guide](BEGINNER-GUIDE.md) gives ordered daily-use, new-machine
setup, troubleshooting and rebuild steps without requiring the old guide's
blocks to be pasted wholesale.
