# Module 14: Hacking Web Applications - Lab Guide

## Tools Used & Purpose

- **Burp Suite**: Core web application penetration testing platform for intercepting traffic, fuzzing parameters, and exploiting web flaws.
- **OWASP ZAP**: Open-source web application vulnerability scanner for automated crawling, spidering, and active scanning.
- **Recon-ng**: Web infrastructure OSINT gathering, host enumeration, and contact discovery.
- **Vega / Wapiti**: Automated web application vulnerability auditing tools for detecting XSS, SQLi, and file inclusion.
- **Wfuzz / ffuf / Gobuster**: High-speed fuzzing tools for discovering hidden directories, parameters, and virtual hosts.
- **cURL**: Command-line HTTP utility for crafting custom requests, manipulating headers, and sending test payloads.
- **Commix**: Automated command injection and exploitation tool for identifying OS command injection vulnerabilities.
- **WhatWeb**: Fingerprinting CMS platforms (WordPress, Joomla), plugins, and JavaScript libraries.
- **ShellGPT (`sgpt`)**: Generating custom payload encoders, deciphering obfuscated scripts, and analyzing web responses.

---

## 6. Hands-On Practical Labs Walkthrough

### Lab 1: Footprint the Web Infrastructure

#### Task 1: Footprint a Web Infrastructure using Recon-ng

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Target: Public domain <code>certifiedhacker.com</code> / Lab Target.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Initialize Recon-ng Framework:</b>
     - Open Terminal on Parrot Security and launch Recon-ng:
       ```bash
       recon-ng
       ```
     - Create dedicated workspace:
       ```txt
       [recon-ng][default] > workspaces create WebRecon
       ```
  2. <b>Install & Configure Modules from Marketplace:</b>
     - Query and install discovery modules:
       ```txt
       [recon-ng][WebRecon] > marketplace install recon/domains-hosts/brute_hosts
       [recon-ng][WebRecon] > marketplace install recon/hosts-hosts/resolve
       ```
  3. <b>Load Target Domain & Execute Reconnaissance:</b>
     - Set target domain:
       ```txt
       [recon-ng][WebRecon] > db insert domains
       domain (TEXT): certifiedhacker.com
       ```
     - Run brute force host discovery:
       ```txt
       [recon-ng][WebRecon] > modules load recon/domains-hosts/brute_hosts
       [recon-ng][WebRecon][brute_hosts] > run
       ```
     - Run DNS resolver module to map discovered subdomains to IP addresses:
       ```txt
       [recon-ng][WebRecon] > modules load recon/hosts-hosts/resolve
       [recon-ng][WebRecon][resolve] > run
       ```
     - View discovered infrastructure assets:
       ```txt
       [recon-ng][WebRecon] > show hosts
       ```

---

#### Task 2: Detect Web Application Vulnerabilities using OWASP ZAP

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Target: Lab Web Application <code>http://www.moviescope.com</code> (<code>10.10.1.22</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Launch OWASP ZAP & Initiate Automated Scan:</b>
     - Launch OWASP ZAP from Applications menu.
     - On the Quick Start tab, select <b>Automated Scan</b>.
     - In <b>URL to attack</b>, enter <code>http://www.moviescope.com</code>.
     - Click <b>Attack</b>.
  2. <b>Analyze Spidering & Active Scan Progression:</b>
     - ZAP initiates traditional Spider crawler, mapping URL endpoints, login forms, and hidden parameters.
     - Once crawling finishes, Active Scan begins, injecting test payloads for SQLi, XSS, and directory traversal.
  3. <b>Evaluate Vulnerability Alerts:</b>
     - Navigate to the <b>Alerts</b> tab.
     - Inspect flagged vulnerabilities:
       - <i>High:</i> SQL Injection in query parameters.
       - <i>Medium:</i> Missing Anti-CSRF Tokens, Cookie Without SameSite Attribute.
       - <i>Low:</i> Missing X-Frame-Options (Clickjacking vulnerability), X-Content-Type-Options Header Missing.
     - Review detailed alert descriptions, evidence payloads, and remediation guidance.

---

### Lab 2: Perform Web Application Attacks

#### Task 1: Perform Brute-Force Attack using Burp Suite

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>) running Burp Suite Community Edition.
  - Target Web Portal: <code>http://10.10.1.22:8080/CEH/</code> login page.
  - Wordlists: <code>username.txt</code> and <code>password.txt</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Configure Browser Proxy & Intercept Traffic:</b>
     - Configure Firefox network settings to proxy traffic through <code>127.0.0.1:8080</code>.
     - In Burp Suite, navigate to <b>Proxy -> Intercept</b> and confirm intercept is <b>ON</b>.
     - In Firefox, attempt login with placeholder credentials <code>testuser</code> / <code>testpass</code>.
  2. <b>Transfer Intercepted Request to Burp Intruder:</b>
     - Right-click the intercepted HTTP POST request and select <b>Send to Intruder</b>.
     - Navigate to the <b>Intruder -> Positions</b> tab.
     - Clear default markers (<code>§</code>) and set attack positions around username and password parameters:
       ```javascript
       POST /CEH/login.php HTTP/1.1
       ...
       username=§testuser§&password=§testpass§
       ```
  3. <b>Configure Cluster Bomb Attack:</b>
     - Set <b>Attack type</b> to <b>Cluster bomb</b>.
     - In <b>Payloads</b> tab:
       - Payload Set 1 (Username): Load <code>username.txt</code>.
       - Payload Set 2 (Password): Load <code>password.txt</code>.
  4. <b>Execute Attack & Analyze Results:</b>
     - Click <b>Start attack</b>.
     - In the attack window, sort results by HTTP <b>Status Code</b> and response <b>Length</b>.
     - Identify valid credential pair exhibiting divergent length (e.g., 302 redirect or unique response body size): <code>admin</code> / <code>password</code>.
     - Disable proxy intercept and authenticate successfully into the target application.

---

#### Task 2: Perform Remote Code Execution (RCE) Attack

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Target Host: Windows Server 2022 hosting WordPress/PHP application (<code>10.10.1.22:8080</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Identify Vulnerable Endpoint:</b>
     - Reconnaissance reveals target web application contains an unauthenticated RCE flaw in an administrative AJAX endpoint or plugin file.
  2. <b>Craft & Execute Exploit Request via cURL:</b>
     - Execute cURL request injecting arbitrary operating system commands:
       ```bash
       curl -i -s -k -X POST 'http://10.10.1.22:8080/CEH/wp-admin/admin-ajax.php?action=vuln_action' \
            --data 'cmd=whoami'
       ```
     - Observe server executing command in response header/body, returning <code>nt authority\system</code> or <code>iis apppool\defaultapppool</code>.
  3. <b>Escalate to Interactive Shell:</b>
     - Inject Netcat reverse shell string or PowerShell payload to establish persistent interactive shell access to the underlying web host.

---

### Lab 3: Detect Web Application Vulnerabilities using Wapiti

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>).
  - Target: Web Application running on <code>http://10.10.1.22:8080/CEH/</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Execute Wapiti Web Application Audit:</b>
     - Open Terminal on Parrot Security:
       ```bash
       wapiti -u http://10.10.1.22:8080/CEH/ -f html -o /home/attacker/wapiti_report
       ```
  2. <b>Inspect Generated Vulnerability Report:</b>
     - Open Firefox and load <code>/home/attacker/wapiti_report/index.html</code>.
     - Review findings categorized by attack modules: Cross-Site Scripting, SQL Injection, File Disclosure, Command Execution, and Weak Credentials.

---

### Lab 4: Perform Web Application Hacking using AI

#### Task 1: Perform Web Application Hacking using ShellGPT

- <b>Environment:</b>
  - Attacking System: Parrot Security (<code>10.10.1.13</code>) with ShellGPT (<code>sgpt</code>).
  - Target: <code>www.moviescope.com</code> / <code>10.10.1.22</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Automated Web Directory Brute-Forcing:</b>
     - Instruct ShellGPT to generate and execute directory enumeration:
       ```bash
       sgpt --shell "Enumerate web directories on target http://10.10.1.22 using gobuster with common wordlist"
       ```
     - Confirm execution; review discovered endpoints (<code>/admin</code>, <code>/backup</code>, <code>/uploads</code>).
  2. <b>Automated Parameter Fuzzing with Wfuzz:</b>
     - Execute ShellGPT parameter fuzzing command:
       ```bash
       sgpt --shell "Fuzz the target url www.moviescope.com using wfuzz to identify hidden parameters"
       ```
     - Review discovered injection parameters.

## 7. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| OWASP A01 (Broken Access)  | IDOR (Insecure Direct Object Reference) occurs when internal database  |
|                            | IDs are exposed in URLs without access control checks.                |
+----------------------------+-----------------------------------------------------------------------+
| OWASP A10 (SSRF)           | Server-Side Request Forgery tricks server into making requests to     |
|                            | internal assets or cloud metadata service (169.254.169.254).          |
+----------------------------+-----------------------------------------------------------------------+
| Stored vs Reflected XSS    | Stored (Type II) is permanent in DB; Reflected (Type I) is in URL.    |
| DOM XSS (Type 0)           | DOM XSS executes entirely on client side without server involvement.  |
+----------------------------+-----------------------------------------------------------------------+
| CSRF Exploitation          | Relies on browser's automatic sending of session cookies; defended by |
|                            | Anti-CSRF Synchronizer Tokens and SameSite=Strict cookies.            |
+----------------------------+-----------------------------------------------------------------------+
| Cookie Security Flags      | HttpOnly prevents JavaScript access (mitigates cookie theft via XSS); |
|                            | Secure flag ensures cookie is transmitted only over HTTPS.            |
+----------------------------+-----------------------------------------------------------------------+
| Clickjacking Defense       | X-Frame-Options: DENY or SAMEORIGIN; CSP frame-ancestors 'self'.      |
+----------------------------+-----------------------------------------------------------------------+
| Burp Intruder Attack Modes | Sniper (1 payload, 1 position at a time); Battering Ram (1 payload in |
|                            | all positions); Pitchfork (parallel lists); Cluster Bomb (Cartesian). |
+----------------------------+-----------------------------------------------------------------------+
| Web Fuzzing Tools          | Wfuzz, ffuf, Gobuster test input parameters and discover directories. |
+----------------------------+-----------------------------------------------------------------------+
| Security Headers           | Content-Security-Policy (CSP) restricts executable script origins;    |
|                            | Strict-Transport-Security (HSTS) enforces HTTPS.                      |
+----------------------------+-----------------------------------------------------------------------+
```
