# Tool availability: local lab

Read-only audit on **12 November 2026**. No requested software was installed,
removed or launched for inventory. No critical system settings were changed.

| Machine/account | Result | Practical choice |
|---|---|---|
| Parrot `.13`, `attacker` | 32 of 46 checked names resolve on PATH; John is installed outside PATH | Use Parrot for most CLI tasks; see [exact inventory](inventory-linux.md) |
| Windows 11 `.11`, `Win11-Client` | Native PowerShell, SSH, curl.exe and nslookup; several GUI launchers/media in `T:\` | Use native alternatives or verified GUI paths; [detail](inventory-windows.md) |
| Server 2022 `.22`, `Administrator` | Same requested-tool classifications as Windows 11; local library `C:\CEH-Tools` readable | Use native alternatives or Parrot; `T:\` was denied in this SSH session |
| Server 2019 `.19` | SSH timed out | Unverified, not classified as missing |
| Android `.9` | Not package-audited in this pass | Mobile target; use the existing ADB workflow and verify the current device before use |

The Windows audit covers 51 names, including individual hashing/utilities;
the Linux audit groups some utilities into packages. Counts are not a
cross-platform score. Windows `find.exe` is not GNU `find`; a Wget PowerShell
alias is not GNU Wget. A source file, installer or archive is not an installed
working tool. GPU, driver, GUI and capture permissions remain separate checks.

## Missing or unverified on Parrot

Missing within the checked scope: Telnet, Yersinia, Steghide, Zsteg, SNOW,
VeraCrypt2John, Radare2 and PowerShell. John exists at `/usr/sbin/john`; use its
full path rather than assuming it is missing. OpenStego, VeraCrypt, BinText,
PhoneSploit and APKTool have library artifacts but unverified runtime readiness.
Windows-only L0phtCrack, CrypTool and BCTextEncoder are not Linux CLI equivalents.
AES-Tool needs a precise product/version before syntax can be documented.

## Priorities before requesting installation

Use already available Nmap, DNS tools, SMB/LDAP clients, SQLmap, WPScan, Gobuster,
TShark, tcpdump, John/Hashcat, Ghidra, ADB and standard utilities on Parrot.
For a specific task that needs a missing tool, request approval for that tool
and its prerequisites. Do not bulk-install the list or execute unknown course
archives. Some GUI tools require Windows, Java, drivers or interactive access.

The tools share is read-only and available on Parrot at `/mnt/ceh-tools`.
Inventory verified metadata rather than archive contents or successful tool
execution. Runtime success must be established by actual task output.
