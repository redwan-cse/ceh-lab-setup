# Parrot tool inventory

Audited **2026-11-12**, Parrot Security **7.4 (echo)** / Debian 13, using
`attacker` over SSH. The share `/mnt/ceh-tools` is read-only. This was a local
host inventory: no target scans, credential reads, installations, GUI launches,
archive extraction or CEH-tool execution. Versions below come from installed
Debian package metadata; they are not `--version` output or runtime tests.

- **Ready / PATH:** command resolved on this account; executable metadata exists.
  Dependencies, permissions, capture access and hardware remain untested.
- **Verified path:** installed executable found outside PATH; use the given path.
- **Archive only:** only an archive filename found; not installed or validated.
- **Unverified:** library installer, source tree, JAR or executable metadata only.
- **Missing:** no command, checked alternate, installed package or matching product
  filename found in the bounded audit. This does not establish machine-wide absence.

The reusable [inventory script](../../ceh-local-lab/inspect-ceh-tools-linux.py)
uses Python's standard library, executable metadata, and trusted `dpkg-query`.
Its filename walk examined **18,846 entries**, up to seven directory levels,
without truncation or access errors. It skips `.git`, `node_modules` and
`__pycache__`, and never reads library file contents or follows directory
symlinks. Generic source modules named `telnet` or `powershell` do not establish
availability of those clients. No requested tool was classified archive-only
in this run.

## Network, web and passwords

All Ready paths in this table start with `/usr/bin/`.

| Tool | State | Command / installed package version |
|---|---|---|
| Nmap | Ready / PATH | `nmap`; `7.98+dfsg-1~bpo13+1` |
| Dig | Ready / PATH | `dig`; bind9-dnsutils `1:9.20.30-1~deb13u1` |
| Nslookup | Ready / PATH | `nslookup`; same bind9-dnsutils package |
| WhatWeb | Ready / PATH | `whatweb`; `0.5.5-1` |
| Telnet | Missing | No `telnet` command or client package found |
| Curl | Ready / PATH | `curl`; `8.21.0-2~bpo13+1` |
| Wget | Ready / PATH | `wget`; `1.25.0-2` |
| LDAPSearch | Ready / PATH | `ldapsearch`; ldap-utils `2.6.10+dfsg-1` |
| SMBClient | Ready / PATH | `smbclient`; `2:4.24.7+dfsg-1~bpo13+1` |
| SMBMap | Ready / PATH | `smbmap`; `1.10.7-1` |
| Gobuster | Ready / PATH | `gobuster`; `3.6.0-1+b10` |
| John | Verified path | `/usr/sbin/john`; `1.9.0-Jumbo-1+git20211102-0parrot1` |
| Hydra | Ready / PATH | `hydra`; `9.5-3` |
| Hashcat | Ready / PATH | `hashcat`; `6.2.6+ds2-1` |
| WPScan | Ready / PATH | `wpscan`; `3.8.28-1parrot3` |
| SQLmap | Ready / PATH | `sqlmap`; `1.10.4-0parrot1` |

John resolves to `/usr/lib/john/john-avx512bw-omp`; CPU compatibility was not
tested. Use `/usr/sbin/john` instead of changing PATH. Workflow guides:
[network/web](network-and-web.md), [password auditing](password-auditing.md).

## Capture, files, reverse engineering and mobile

| Tool | State | Path / installed package version or library evidence |
|---|---|---|
| Wireshark | Ready / PATH | `/usr/bin/wireshark`; `4.4.19-0+deb13u1` |
| TShark | Ready / PATH | `/usr/bin/tshark`; `4.4.19-0+deb13u1` |
| Tcpdump | Ready / PATH | `/usr/bin/tcpdump`; `4.99.5-2` |
| Yersinia | Missing | No PATH command or `/usr/sbin/yersinia` |
| Steghide | Missing | No command/package/product match |
| Zsteg | Missing | No command/package/product match |
| OpenStego | Unverified | Module 06 `Steganography Tools/Image Steganography Tools/OpenStego/Setup-OpenStego-0.8.6.exe` |
| SNOW | Missing | Neither `snow` nor `stegsnow` found |
| Binwalk | Ready / PATH | `/usr/bin/binwalk`; `2.4.3+dfsg1-2+deb13u1` |
| VeraCrypt | Unverified | Module 20 `Disk Encryption Tools/VeraCrypt/VeraCrypt Setup 1.26.7.exe` |
| VeraCrypt2John | Missing | Neither command nor checked `/usr/share/john/veracrypt2john[.py]` |
| Ghidra | Ready / PATH | `/usr/bin/ghidra` -> `/usr/share/ghidra/ghidraRun`; `12.0.4-1parrot1` |
| Radare2 | Missing | Neither `radare2` nor `r2` found |
| BinText | Unverified | Module 07 `Malware Analysis Tools/Static Malware Analysis Tools/String Searching Tools/BinText/bintext.exe` |
| Strings | Ready / PATH | `/usr/bin/strings`; binutils `2.44-3` |
| File | Ready / PATH | `/usr/bin/file`; `1:5.46-5` |
| ADB | Ready / PATH | `/usr/bin/adb`; `1:34.0.5-12` |
| PhoneSploit | Unverified | Module 17 `GitHub Tools/PhoneSploit-Pro` source folder |
| APKTool | Unverified | Module 17 `GitHub Tools/AndroRAT/Jar_utils/apktool.jar`; no standalone command |
| Aircrack-ng | Ready / PATH | `/usr/bin/aircrack-ng`; `1:1.7+git20230807.4bf83f1a-2` |
| PowerShell | Missing | Neither `pwsh` nor `powershell` client/package found |

Library paths above are relative to the corresponding `CEHv13 Module NN ...`
folder under `/mnt/ceh-tools`. Windows `.exe` files are library artifacts, not
native Linux tools. No Wine/Java/runtime compatibility test was performed.
The library's separate Ghidra tree also remains unverified; the Ready entry
refers to the installed Parrot package. `/usr/share/john/truecrypt2john.py`
exists, but it is not evidence of a `veracrypt2john` command or compatible
VeraCrypt format. ADB device access, wireless adapter/monitor support and GUI
sessions were not exercised.

## Shell and integrity utilities

| Tool | State / path | Installed package version |
|---|---|---|
| OpenSSH | Ready / PATH: `/usr/bin/ssh` | openssh-client `1:10.3p1-1~bpo13+1` |
| SHA1SUM | Ready / PATH: `/usr/bin/sha1sum` | coreutils `9.7-3` |
| SHA224SUM | Ready / PATH: `/usr/bin/sha224sum` | coreutils `9.7-3` |
| SHA256SUM | Ready / PATH: `/usr/bin/sha256sum` | coreutils `9.7-3` |
| Base64 | Ready / PATH: `/usr/bin/base64` | coreutils `9.7-3` |
| Grep | Ready / PATH: `/usr/bin/grep` | grep `3.11-4` |
| Find | Ready / PATH: `/usr/bin/find` | findutils `4.10.0-3` |
| Awk | Ready / PATH: `/usr/bin/awk` | mawk `1.3.4.20250131-1`; gawk also installed `1:5.2.1-2+b1` |
| Sed | Ready / PATH: `/usr/bin/sed` | sed `4.9-2+deb13u1` |

`openssl`, `ssh-keyscan`, `dumpcap` and `7z` were also found on PATH in the
parent audit. Base64 is encoding, not encryption. Hash utilities compute file
digests; their presence does not identify a password hash format.

## Repeat without changing Parrot

From PowerShell in this repository on the Windows host:

```powershell
Get-Content -Raw .\ceh-local-lab\inspect-ceh-tools-linux.py | ssh attacker@10.10.10.13 python3 -
```

This uses the already authorized SSH key and streams the reviewed inventory
script to Python without copying or installing it. Inspect its JSON fields,
especially `package_query_error`, `library_walk_errors` and
`library_walk_truncated`, before relying on a future result. For another host,
replace only the SSH destination with your authorized Parrot VM. In ShellGPT,
script/interpreter commands require the normal approval flow.
