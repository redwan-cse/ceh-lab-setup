# Module 04: Enumeration - Lab Guide

## Tools Used & Purpose

- **nbtstat**: Displaying NetBIOS over TCP/IP name tables, workgroups, and remote machine MAC addresses (`nbtstat -A <IP>`).
- **NetBIOS Enumerator**: Scanning remote Windows subnets for NetBIOS computer names, logged-in usernames, MAC addresses, and open SMB shares.
- **snmpwalk / snmp-check**: Interrogating SNMP agents (port 161) with community strings to dump MIB tables, system info, network interfaces, and user accounts.
- **Active Directory Explorer (AD Explorer)**: Sysinternals GUI tool to traverse Active Directory hierarchies, inspect schema objects, SIDs, and user attributes.
- **ldap3 (Python)**: Scripting programmatic queries to authenticate with LDAP servers (port 389) and extract domain users and organizational units.
- **rpcinfo**: Querying RPC portmappers (port 111) to list registered program numbers, service names, and socket versions on UNIX/Linux hosts.
- **showmount**: Enumerating exported directories and file systems accessible on Network File System (NFS) servers (`showmount -e <target>`).
- **RPCScan / SuperEnum**: Automated enumeration scripts chaining NetBIOS, RPC, SMB, and NFS interrogation to quickly identify open service shares.
- **dig / nslookup**: Interrogating DNS servers, attempting full zone transfers (`axfr`), and performing DNS cache snooping.
- **smtp-user-enum**: Validating valid internal system email accounts using SMTP commands (`VRFY`, `EXPN`, `RCPT TO`).
- **ShellGPT (`sgpt`)**: Automating complex enumeration tasks (e.g., AD queries, RPC calls, and SMB userlist parsing) from the command line.

---

# Topic 08: Hands-On Lab Walkthroughs & AI-Assisted Enumeration

<i>(Reference: Official CEH v13 Lab Manual, Pages 125–170 & iLabs Curriculum, Labs 01–09)</i>

All lab exercises were performed within the official virtualized lab environment (<code>10.10.1.0/24</code>) using Parrot Security (<code>10.10.1.13</code>), Windows Server 2022 (<code>10.10.1.22</code>), Windows Server 2019 (<code>10.10.1.19</code>), and Windows 11 (<code>10.10.1.11</code>).

---

### Lab 01: Perform NetBIOS Enumeration

<i>(Lab Manual Pages 128–131 \| Video: CEHv13-M04-L01-T01)</i>

#### Task 1: NetBIOS Enumeration using Windows Command-Line Utilities

- <b>Objective:</b> Interrogate remote Windows targets using native Windows networking utilities.
- <b>Execution from Windows Server 2019 targeting Windows 11 (</b><b><code>10.10.1.11</code></b><b>):</b>
  ```shell
  nbtstat -a 10.10.1.11
  ```
- <b>Output Analysis:</b>
  - Displays remote name table: <code>WINDOWS11 <00></code> (Unique Workstation), <code>WORKGROUP <00></code> (Group), <code>WINDOWS11 <20></code> (Server service running / File and Printer sharing enabled).
  - MAC Address: <code>00-0C-29-3A-4F-1B</code>.
- <b>Session and Share Verification:</b>
  ```shell
  net view \\\\10.10.1.11
  net use \\\\10.10.1.11\\IPC$ "" /u:""
  ```

#### Task 2: NetBIOS Enumeration using NetBIOS Enumerator

- <b>Objective:</b> Automated GUI scanning across network ranges.
- <b>Procedure:</b>
  1. Launch <b>NetBIOS Enumerator</b> on Windows Server 2019.
  2. Enter IP range <code>10.10.1.11</code> to <code>10.10.1.22</code>.
  3. Click <b>Scan</b>.
- <b>Results:</b> Discovers NetBIOS hostnames, workgroups, domain roles, and MAC addresses across all alive hosts.

---

### Lab 02: Perform SNMP Enumeration

<i>(Lab Manual Pages 132–134 \| Video: CEHv13-M04-L02-T03)</i>

#### Task 1: SNMP Enumeration using SnmpWalk

- <b>Objective:</b> Traverse MIB tree of target server using <code>snmpwalk</code>.
- <b>Execution from Parrot Security targeting Windows Server 2022 (</b><b><code>10.10.1.22</code></b><b>):</b>
  ```bash
  snmpwalk -v2c -c public 10.10.1.22
  ```
- <b>Output Telemetry:</b>
  - <code>iso.3.6.1.2.1.1.1.0 = STRING: "Hardware: Intel Family 6 Model 85 Stepping 7 - Software: Windows Version 6.3 (Build 20348 Multiprocessor Free)"</code>
  - <code>iso.3.6.1.2.1.1.5.0 = STRING: "server2022.CEH.com"</code>
  - <code>iso.3.6.1.2.1.1.3.0 = Timeticks: (2887671405) 334 days...</code>

#### Task 2: SNMP Enumeration using snmp-check

- <b>Objective:</b> Automated intelligence extraction and user account enumeration.
- <b>Execution:</b>
  ```bash
  snmp-check 10.10.1.22 -c public
  ```
- <b>Results Extracted:</b>
  - User accounts enumerated: <code>Administrator</code>, <code>Guest</code>, <code>Martin</code>, <code>Shiela</code>, <code>jason</code>, <code>krbtgt</code>.
  - Network shares enumerated: <code>C$</code>, <code>ADMIN$</code>, <code>SYSVOL</code>, <code>NETLOGON</code>.
  - Process list with running daemons and memory consumption.

---

### Lab 03: Perform LDAP Enumeration

<i>(Lab Manual Pages 135–138 \| Video: CEHv13-M04-L03-T01)</i>

#### Task 1: LDAP Enumeration using Active Directory Explorer (AD Explorer)

- <b>Objective:</b> Explore Active Directory hierarchy using Sysinternals AD Explorer.
- <b>Procedure:</b>
  1. Launch <code>ADExplorer.exe</code> on Windows 11.
  2. Connect to <code>10.10.1.22</code> with username <code>Martin</code> and password <code>Pa$$w0rd</code>.
  3. Navigate directory tree: <code>dc=CEH,dc=com</code> → <code>CN=Users</code>.
- <b>Results:</b> Displays attributes for all domain users, Security Identifiers (SIDs), email addresses, group memberships, and service account configurations.

#### Task 2: LDAP Enumeration using Python Script (<code>ldap3</code>)

- <b>Objective:</b> Programmatic LDAP interrogation without third-party tools.
- <b>Execution from Parrot Security terminal:</b>
  ```bash
  python3
  ```

  ```py
  import ldap3
  server = ldap3.Server('10.10.1.22', get_info=ldap3.ALL, port=389)
  connection = ldap3.Connection(server)
  connection.bind()
  print(server.info)
  connection.search('DC=CEH,DC=com', '(&(objectClass=person))', search_scope='SUBTREE', attributes=['*'])
  print(connection.entries)
  ```
- <b>Output:</b> Dumps complete Active Directory user database, including account creation timestamps and organizational assignments.

---

### Lab 04: Perform NFS Enumeration

<i>(Lab Manual Pages 139–144 \| Video: CEHv13-M04-L04-T01)</i>

#### Task 1: NFS Enumeration using RPCScan and SuperEnum

- <b>Objective:</b> Scan RPC services and identify exposed NFS shares on Linux server (<code>10.10.1.9</code>).
- <b>Execution:</b>
  ```bash
  # Probe RPC endpoints
  rpcinfo -p 10.10.1.9

  # Discover exported mount points
  showmount -e 10.10.1.9
  ```
- <b>Automated Scanning with SuperEnum:</b>
  1. Run <code>./superenum</code> on Parrot Security.
  2. Input target IP <code>10.10.1.9</code>.
  3. SuperEnum executes <code>showmount</code>, <code>rpcinfo</code>, and checks for open NFS exports, revealing <code>/home</code> exported to <code>*</code> without IP restrictions.

---

### Lab 05: Perform DNS Enumeration

<i>(Lab Manual Pages 145–148 \| Video: CEHv13-M04-L05-T01)</i>

#### Task 1: DNS Zone Transfer using dig and nslookup

- <b>Objective:</b> Attempt full zone transfer (AXFR) against domain controller DNS server (<code>10.10.1.22</code>).
- <b>Execution using dig:</b>
  ```bash
  dig @10.10.1.22 ceh.com axfr
  ```
- <b>Execution using nslookup:</b>
  ```shell
  nslookup
  > server 10.10.1.22
  > set type=any
  > ls -d ceh.com
  ```
- <b>Results:</b> If zone transfers are misconfigured to allow queries from arbitrary IPs, the complete record table (A, AAAA, MX, NS, SRV, SOA, PTR) is displayed, dumping internal network naming conventions.

---

### Lab 06: Perform SMTP Enumeration

<i>(Lab Manual Pages 149–152 \| Video: CEHv13-M04-L06-T01)</i>

#### Task 1: Perform SMTP Enumeration using Nmap

- <b>Objective:</b> Interrogate SMTP services on Windows Server 2019 (<code>10.10.1.19</code>) using Nmap NSE scripts.
- <b>Execution from Parrot Security (</b><b><code>10.10.1.13</code></b><b>):</b>
  ```bash
  # Enumerate possible mail users on target machine
  nmap -p 25 --script=smtp-enum-users 10.10.1.19
  ```

  <p>
  <i>Output:</i> Discovers valid user accounts: <code>root</code>, <code>admin</code>, <code>administrator</code>, <code>webadmin</code>, <code>sysadmin</code>, <code>netadmin</code>, <code>guest</code>, <code>user</code>, <code>web</code>, <code>test</code>.
  </p>

  ```bash
  # Check if SMTP server acts as an open mail relay
  nmap -p 25 --script=smtp-open-relay 10.10.1.19
  ```

  <p>
  <i>Output:</i> <code>_smtp-open-relay: Server is an open relay (14/16 tests)</code>.
  </p>

  ```bash
  # List all available SMTP commands supported by the daemon
  nmap -p 25 --script=smtp-commands 10.10.1.19
  ```

  <p>
  <i>Output:</i> Discovers commands: <code>HELO</code>, <code>EHLO</code>, <code>STARTTLS</code>, <code>RCPT</code>, <code>DATA</code>, <code>RSET</code>, <code>MAIL</code>, <code>QUIT</code>, <code>AUTH</code>, <code>TURN</code>, <code>ETRN</code>, <code>VRFY</code>.
  </p>

#### Task 2: SMTP User Verification via Telnet, Netcat, and smtp-user-enum

- <b>Objective:</b> Test mail server user verification commands against Windows Server 2019 (<code>10.10.1.19</code>).
- <b>Execution via Netcat:</b>
  ```bash
  nc -nv 10.10.1.19 25
  HELO attacker.com
  VRFY administrator
  # Returns: 250 2.1.5 Administrator
  VRFY bogususer
  # Returns: 550 5.1.1 User unknown
  ```
- <b>Automated Enumeration via smtp-user-enum:</b>
  ```bash
  smtp-user-enum -M VRFY -U /usr/share/wordlists/metasploit/unix_users.txt -t 10.10.1.19
  ```
- <b>Output:</b> Accurately isolates valid usernames on the mail server.

---

### Lab 07: Perform SMB, MSRPC, and NULL Session Enumeration

<i>(Official Courseware / iLabs Core Practical)</i>

#### Task 1: Windows Command-Line NULL Session Interrogation

- <b>Objective:</b> Connect anonymously to the Inter-Process Communication share (<code>IPC$</code>) on Windows 11 (<code>10.10.1.11</code>).
- <b>Execution from Windows Command Prompt:</b>
  ```shell
  net use \\\\10.10.1.11\\IPC$ "" /u:""
  net view \\\\10.10.1.11
  ```
- <b>Analysis:</b> Demonstrates how unhardened systems allow anonymous access to list shares and named pipes.

#### Task 2: Automated Linux-to-Windows Enumeration via enum4linux & enum4linux-ng

- <b>Execution from Parrot Security (</b><b><code>10.10.1.13</code></b><b>):</b>
  ```bash
  # Comprehensive enumeration of domain, shares, users, password policies, and RID cycling
  enum4linux -a 10.10.1.11

  # Next-generation modern Python 3 rewrite
  enum4linux-ng -A 10.10.1.11
  ```
- <b>Telemetry Gathered:</b>
  - Workgroup / Domain SID: <code>S-1-5-21-397955417-626881126-188441402</code>
  - Password policy: Minimum length, lockout threshold, lockout duration
  - RID Cycling: Extracts usernames by brute-forcing Relative Identifiers (500 to 1100)

#### Task 3: Interactive MSRPC Interrogation via rpcclient

- <b>Execution:</b>
  ```bash
  rpcclient -U "" -N 10.10.1.11
  rpcclient $> enumdomusers
  rpcclient $> enumdomgroups
  rpcclient $> queryuser 0x1f4
  rpcclient $> lookupnames administrator
  ```
- <b>Output:</b> Dumps precise user RID mappings and group memberships directly from SAM/LSA.

#### Task 4: SMB Share Inspection via smbclient & CrackMapExec

```bash
smbclient -L //10.10.1.11/ -N
crackmapexec smb 10.10.1.11 -u '' -p '' --shares
```

---

### Lab 08: Perform Enumeration using Various Tools

<i>(Lab Manual Pages 153–160 \| Video: CEHv13-M04-L08-T01)</i>

- <b>Task 1: Global Network Inventory:</b> Comprehensive Windows inventory tool that interrogates remote systems via WMI and SMB to build hardware and software asset reports.
- <b>Task 2: Advanced IP Scanner:</b> Fast multi-threaded IP scanner that detects NetBIOS shares, HTTP/HTTPS services, and remote desktop ports.
- <b>Task 3: SoftPerfect Network Scanner:</b> Enterprise scanning utility that maps listening ports, checks user permissions, discovers hidden administrative shares (<code>C$</code>, <code>ADMIN$</code>), and retrieves SNMP sysDescr strings.

---

### Lab 09: Perform Enumeration using AI (ShellGPT)

<i>(Lab Manual Pages 161–170 \| Video: CEHv13-M04-L09-T01)</i>

Ethical hackers leverage Generative AI through ShellGPT (<code>sgpt</code>) to generate, optimize, and execute enumeration commands dynamically on Parrot Security (<code>10.10.1.13</code>):

#### 1. AI-Driven NetBIOS Enumeration

```bash
sgpt --shell "Perform NetBIOS enumeration on target IP 10.10.1.11"
# ShellGPT generates and executes:
nbtscan 10.10.1.11
```

<i>Output:</i> Resolves <code>WINDOWS11</code> NetBIOS name, workstation service, and MAC address.

#### 2. AI-Driven SNMP Enumeration

```bash
# Query SNMP via SnmpWalk
sgpt --chat enum --shell "Perform SNMP enumeration on target IP 10.10.1.22 using SnmpWalk and display the result here"

# Query SNMP processes via Nmap
sgpt --chat enum --shell "Perform SNMP processes on target IP 10.10.1.22 using nmap and display the result here"
# ShellGPT executes:
nmap -sU -p 161 --script snmp-processes 10.10.1.22
```

<i>Output:</i> Enumerates active processes: <code>System Idle Process</code>, <code>svchost.exe</code>, <code>lsass.exe</code>.

#### 3. AI-Driven SMTP Enumeration

```bash
sgpt --chat enum --shell "Perform SMTP enumeration on target IP 10.10.1.19."
# ShellGPT executes:
nmap -sV -p 25 --script smtp-commands,smtp-open-relay,smtp-vuln* 10.10.1.19
```

<i>Output:</i> Lists supported SMTP verbs: <code>HELO</code>, <code>EHLO</code>, <code>STARTTLS</code>, <code>RCPT</code>, <code>DATA</code>, <code>VRFY</code>, <code>ETRN</code>.

#### 4. AI-Driven DNS Enumeration & Cache Snooping

```bash
# DNS enumeration using Nmap scripts
sgpt --chat enum --shell "Use Nmap to perform DNS Enumeration on target domain www.certifiedhacker.com"
# ShellGPT executes:
nmap -p 53 --script dns-brute,dns-zone-transfer,dns-service-discovery www.certifiedhacker.com

# DNS Cache Snooping using dig
sgpt --chat enum --shell "Use dig command to perform DNS cache snooping on target domain www.certifiedhacker.com using recursive method. Use DNS server IP as 162.241.216.11"
# ShellGPT executes:
dig @162.241.216.11 www.certifiedhacker.com A +recurse
```

#### 5. AI-Driven IPsec & SMB Enumeration

```bash
# IPsec enumeration
sgpt --shell "Perform IPsec enumeration on IP 10.10.1.22 using nmap"
# ShellGPT executes:
nmap -sU -p 500 --script ike-version 10.10.1.22

# SMB enumeration
sgpt --shell "Scan the target IP 10.10.1.22 for the port using SMB with Nmap"
# ShellGPT executes:
nmap -p 445 --script smb-protocols,smb-security-mode,smb2-security-mode 10.10.1.22
```

<i>Output:</i> Identifies supported dialects (<code>SMB 2.0.2</code>, <code>SMB 2.1</code>, <code>SMB 3.0</code>, <code>SMB 3.1.1</code>) and operating system build (<code>Windows Server 2022 Standard 20348</code>).

#### 6. AI-Driven Automation Script Development

```bash
sgpt --chat enum --shell "Develop and execute a script which will automate various network enumeration tasks on target IP range 10.10.1.0/24"
```

<i>Action:</i> ShellGPT generates and executes <code>network_enum.sh</code>:

```bash
#!/bin/bash
nmap -sn 10.10.1.0/24 -oG - | awk '/Up$/{print $2}' > live_hosts.txt
nmap -sV -iL live_hosts.txt -oA service_scan
nmap -O -iL live_hosts.txt -oA os_scan
nmap -p- -iL live_hosts.txt -oA full_ports
```

#### 7. AI-Driven LDAP Brute-Force & FTP Enumeration

```bash
# LDAP brute-forcing via Nmap
sgpt --shell "Use nmap script to perform ldap-brute-force on IP 10.10.1.22"
# ShellGPT executes:
nmap -p 389 --script ldap-brute --script-args ldap.base="cn=users,dc=CEH,dc=com" 10.10.1.22

# FTP enumeration
sgpt --shell "Use Nmap to perform FTP Enumeration on www.certifiedhacker.com"
# ShellGPT executes:
nmap -sV -p 21 --script=ftp-anon,ftp-bounce,ftp-proftpd-backdoor,ftp-vsftpd-backdoor www.certifiedhacker.com
```

---
