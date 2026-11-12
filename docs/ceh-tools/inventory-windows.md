# Windows CEH tool inventory

Observed **12 November 2026, approximately 12:44–12:45 Asia/Dhaka (UTC+06:00)**, using read-only key-authenticated SSH. This is installed-command and file-metadata evidence, not execution validation. No packages, settings, shares, SSH configuration or VM power state were changed. No course executables, installers, scripts or JARs were launched. No credentials or provider configuration were read.

| Target | Observation | Library access |
|---|---|---|
| `Win11-Client@10.10.10.11` | Reachable; `DESKTOP-5AJ4QBL`; Windows PowerShell `5.1.26100.9818` | `T:\` readable; manifest has 32,837 file entries across 20 course archives; `C:\CEH-Tools` absent |
| `Administrator@10.10.10.19` | SSH connection timed out | Unavailable; every tool remains unverified on this target |
| `Administrator@10.10.10.22` | Reachable; `WIN-L4HLUP8AT8K`; Windows PowerShell `5.1.20348.5756` | `C:\CEH-Tools` readable with the same 32,837-entry manifest; `T:\` access denied in this SSH session |

The two reachable targets have the same classifications for all 51 requested tool names: five PATH commands, three extracted Windows launchers, four unverified source/JAR groups, seven installer/archive-only groups and 32 missing within the audited scope. None of these 51 names matched the machine/user uninstall registries. The shared library is one course collection accessible from two machines; it is not two independent software installations.

## Classification and scope

- **PATH**: a native executable resolved with `Get-Command -CommandType Application,ExternalScript`. It was not launched.
- **Registry**: matching uninstall registration, if present. No matching entries were observed here.
- **Extracted/manual**: an executable or Windows batch launcher exists at a verified library path. This does not establish prerequisites, runtime compatibility, a valid installation or successful operation.
- **Source/unverified**: source or JAR metadata exists. Required interpreters, packages, drivers and behavior have not been validated.
- **Installer/archive only**: installation media or a nested archive exists, with no installed/native launcher found. This is not installed software.
- **Missing in scope**: no matching PATH command, uninstall registration, known-directory executable or manifest launcher/archive was found. This is not proof of absence anywhere on the disk.
- **Unavailable**: the machine could not be inspected. This is not a missing-tool result.

`ceh-local-lab/Inspect-CehTools.ps1` reads the HKLM 64-bit/WOW6432Node and current-user uninstall display metadata, native command resolution, and immediate files in a fixed list of common application directories. It does not recurse through `C:\`, profiles or arbitrary directories. It indexes the existing `.ceh-library-manifest.json` only (maximum 16 MiB / 50,000 entries), matches bounded evidence per tool, and checks the matched files' existence and byte length. All matched library launchers/installers/source files reported below matched their manifest byte lengths; this audit did not recheck CRCs or hashes. Nested archive contents were not inspected. An archive filename is evidence of media only.

## All requested tools

Both columns below refer to the logged-in SSH context. Every entry on `.19` is **unverified/unavailable**.

| Tool | Windows 11 `.11` | Windows Server `.22` | Evidence or limitation |
|---|---|---|---|
| Nmap | Installer only | Installer only | `nmap-7.95-setup.exe`; no `nmap.exe` found |
| Dig | Missing in scope | Missing in scope | `Resolve-DnsName` is available as a Windows alternative |
| Nslookup | PATH | PATH | `C:\Windows\System32\nslookup.exe` |
| WhatWeb | Missing in scope | Missing in scope | SpiderFoot integration filenames do not establish WhatWeb itself |
| Telnet | Missing in scope | Missing in scope | No `telnet.exe` resolved; Windows feature state not changed |
| Curl | PATH | PATH | `C:\Windows\System32\curl.exe`; use the `.exe` name in Windows PowerShell |
| Wget | Missing in scope | Missing in scope | `wget` is an `Invoke-WebRequest` alias, not GNU Wget |
| LDAPSearch | Missing in scope | Missing in scope | No native executable verified |
| SMBClient | Source/unverified | Source/unverified | Impacket `smbclient.py`; not the Samba `smbclient` command |
| SMBMap | Missing in scope | Missing in scope | No native executable or launcher verified |
| Gobuster | Missing in scope | Missing in scope | No native executable verified |
| John | Missing in scope | Missing in scope | No `john.exe` verified |
| Hydra | Missing in scope | Missing in scope | No native executable verified |
| Hashcat | Missing in scope | Missing in scope | No native executable or GPU runtime verified |
| L0phtCrack | Installer only | Installer only | `lc7setup_v7.2.0_Win64.exe`; no `lc7.exe` verified |
| WPScan | Source/unverified | Source/unverified | Ruby project with `bin/wpscan` and `lib/wpscan.rb`; Ruby not resolved on either VM |
| SQLmap | Missing in scope | Missing in scope | No `sqlmap.py` or native command verified |
| Wireshark | Installer only | Installer only | `Wireshark-4.2.3-x64.exe`; no installed `wireshark.exe` verified |
| TShark | Missing in scope | Missing in scope | Wireshark installer is not a verified TShark installation |
| Tcpdump | Missing in scope | Missing in scope | Neither `tcpdump.exe` nor WinDump verified |
| Yersinia | Missing in scope | Missing in scope | No native Windows executable verified |
| Steghide | Missing in scope | Missing in scope | No native executable verified |
| Zsteg | Missing in scope | Missing in scope | No Ruby launcher verified |
| OpenStego | Installer only | Installer only | `Setup-OpenStego-0.8.6.exe`; no installed launcher verified |
| SNOW | Missing in scope | Missing in scope | Neither `snow.exe` nor `stegsnow.exe` verified |
| Binwalk | Missing in scope | Missing in scope | No native executable/launcher verified |
| VeraCrypt | Installer only | Installer only | `VeraCrypt Setup 1.26.7.exe`; no installed launcher/driver verified |
| VeraCrypt2John | Missing in scope | Missing in scope | No matching `.py`, `.pl` or `.exe` verified |
| CrypTool | Installer only | Installer only | `SetupCrypTool_1_4_42_en.exe`; GUI installation not verified |
| BCTextEncoder | Extracted/manual | Extracted/manual | `BCTextEncoder.exe` (1,373,872 bytes); GUI not launched |
| AES-Tool | Missing in scope | Missing in scope | Exact tool/distribution identity remains unspecified |
| 7-Zip | Missing in scope | Missing in scope | No PATH, registry or common-location launcher verified |
| Ghidra | Extracted/manual | Extracted/manual | `ghidraRun.bat` (348 bytes); GUI/Java runtime compatibility not exercised |
| Radare2 | Missing in scope | Missing in scope | Neither `radare2.exe` nor `r2.exe` verified |
| BinText | Extracted/manual | Extracted/manual | `bintext.exe` (35,840 bytes); GUI not launched |
| Strings | Missing in scope | Missing in scope | No Sysinternals/GNU strings executable verified |
| File | Missing in scope | Missing in scope | No GNU `file.exe` verified; Ghidra source ZIP names are unrelated |
| ADB | Missing in scope | Missing in scope | No `adb.exe` verified; no Android device or port was contacted |
| PhoneSploit | Source/unverified | Source/unverified | `PhoneSploit-Pro/phonesploitpro.py`; dependencies and Windows support unverified |
| APKTool | Source/unverified | Source/unverified | `AndroRAT/Jar_utils/apktool.jar`; bundled JAR is not a standalone installed APKTool command |
| Aircrack-ng | Archive only | Archive only | `aircrack-ng-1.2-rc4-win.zip` and `.tar.gz`; no extracted Windows binary verified |
| PowerShell | PATH | PATH | Windows PowerShell 5.1; no `pwsh.exe` resolved |
| OpenSSH | PATH | PATH | `C:\Windows\System32\OpenSSH\ssh.exe`; SSH key access worked |
| SHA1SUM | Missing in scope | Missing in scope | `Get-FileHash -Algorithm SHA1` is available |
| SHA224SUM | Missing in scope | Missing in scope | Windows `Get-FileHash` does not provide SHA224 |
| SHA256SUM | Missing in scope | Missing in scope | `Get-FileHash -Algorithm SHA256` is available |
| Base64 | Missing in scope | Missing in scope | .NET `[Convert]` provides encoding/decoding; no GNU command verified |
| Grep | Missing in scope | Missing in scope | `Select-String` is available; syntax and output differ |
| Find | PATH (Windows) | PATH (Windows) | `C:\Windows\System32\find.exe` searches text; it is not GNU filesystem `find` |
| Awk | Missing in scope | Missing in scope | `Select-Object` / `ForEach-Object` provide partial workflow alternatives |
| Sed | Missing in scope | Missing in scope | PowerShell `-replace` offers some substitutions; no GNU Sed verified |

## Verified library paths

Prepend **`T:\` on `.11`** or **`C:\CEH-Tools\` on `.22`** to each relative path. These paths were checked on both targets. They are locations for review; none was executed.

| Tool / kind | Relative path |
|---|---|
| Nmap installer | `CEHv13 Module 03 Scanning Networks\Scanning Tools\Nmap\nmap-7.95-setup.exe` |
| Wireshark installer | `CEHv13 Module 03 Scanning Networks\Banner Grabbing Tools\Wireshark\Wireshark-4.2.3-x64.exe` |
| L0phtCrack installer | `CEHv13 Module 06 System Hacking\Password Cracking Tools\L0phtCrack\lc7setup_v7.2.0_Win64.exe` |
| OpenStego installer | `CEHv13 Module 06 System Hacking\Steganography Tools\Image Steganography Tools\OpenStego\Setup-OpenStego-0.8.6.exe` |
| Impacket example | `CEHv13 Module 06 System Hacking\Active Directory\impacket\examples\smbclient.py` |
| Impacket implementation | `CEHv13 Module 06 System Hacking\Active Directory\impacket\impacket\examples\smbclient.py` |
| Additional Impacket example | `CEHv13 Module 13 Hacking Web Servers\GitHub Tools\impacket\examples\smbclient.py` |
| Additional Impacket implementation | `CEHv13 Module 13 Hacking Web Servers\GitHub Tools\impacket\impacket\examples\smbclient.py` |
| Ghidra launcher | `CEHv13 Module 07 Malware Threats\Malware Analysis Tools\Static Malware Analysis Tools\Disassembling and Debugging Tools\Ghidra\ghidraRun.bat` |
| BinText GUI | `CEHv13 Module 07 Malware Threats\Malware Analysis Tools\Static Malware Analysis Tools\String Searching Tools\BinText\bintext.exe` |
| WPScan launcher | `CEHv13 Module 14 Hacking Web Applications\GitHub Tools\wpscan\bin\wpscan` |
| WPScan Ruby source | `CEHv13 Module 14 Hacking Web Applications\GitHub Tools\wpscan\lib\wpscan.rb` |
| Aircrack-ng Windows archive | `CEHv13 Module 16 Hacking Wireless Networks\Raw Packet Capturing Tools\Airodump-ng\aircrack-ng-1.2-rc4-win.zip` |
| Aircrack-ng source archive | `CEHv13 Module 16 Hacking Wireless Networks\Raw Packet Capturing Tools\Airodump-ng\aircrack-ng-1.2-rc4.tar.gz` |
| PhoneSploit-Pro source | `CEHv13 Module 17 Hacking Mobile Platforms\GitHub Tools\PhoneSploit-Pro\phonesploitpro.py` |
| Bundled APKTool JAR | `CEHv13 Module 17 Hacking Mobile Platforms\GitHub Tools\AndroRAT\Jar_utils\apktool.jar` |
| CrypTool installer | `CEHv13 Module 20 Cryptography\Cryptanalysis Tools\CrypTool\SetupCrypTool_1_4_42_en.exe` |
| BCTextEncoder GUI | `CEHv13 Module 20 Cryptography\Cryptography Tools\BCTextEncoder\BCTextEncoder.exe` |
| VeraCrypt installer | `CEHv13 Module 20 Cryptography\Disk Encryption Tools\VeraCrypt\VeraCrypt Setup 1.26.7.exe` |

## Windows alternatives and prerequisites

Both reachable machines resolve `Resolve-DnsName`, `Invoke-WebRequest`, `Get-FileHash`, `Select-String`, `Get-ChildItem`, `Select-Object` and `ForEach-Object`. Windows PowerShell 5.1 also defines both `curl` and `wget` as aliases for `Invoke-WebRequest`; use `curl.exe` when native Curl semantics are required. Use `Get-ChildItem -Recurse` for a deliberately scoped filesystem search, not Windows `find.exe`.

Python command metadata was found on `.11` at `C:\Users\Win11-Client\AppData\Local\Programs\Python\Python312\python.exe` and on `.22` at `C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe`. Java resolves on `.11` through both Oracle's `javapath` shim and `C:\Program Files\Microsoft\jdk-21.0.3.9-hotspot\bin\java.exe`. Java, Ruby and Perl did not resolve on `.22`; Ruby and Perl did not resolve on `.11`. These are command/path observations, not version execution or dependency validation. Python's presence alone does not validate PhoneSploit or Impacket packages, and Ghidra on `.22` has no verified Java command.

No assumption is made that Linux-oriented programs run natively on these Windows machines. WSL/Cygwin/container installations were not audited. Tools found in course source trees, including scripts with matching names, remain unverified until their supported platform and dependencies are deliberately checked. GUI tools remain manual/unverified for operation.

## Repeating the inventory

Run the script locally in the Windows session being inspected; it emits JSON and does not write a report on that machine:

```powershell
.\ceh-local-lab\Inspect-CehTools.ps1
# Or inspect only an explicitly selected library:
.\ceh-local-lab\Inspect-CehTools.ps1 -LibraryRoots 'T:\'
```

For SSH, stream the script through standard input to a short encoded PowerShell wrapper which reads `[Console]::In.ReadToEnd()` and invokes the inventory script block. Use existing key authentication, `BatchMode=yes`, a finite `ConnectTimeout`, and save captured JSON only where authorized. Do not copy/install tools onto the VMs merely to inventory them. The `.19` timeout and `.22` `T:\` denial remain blockers for those specific checks; no VM startup, remount or permission changes were attempted.
