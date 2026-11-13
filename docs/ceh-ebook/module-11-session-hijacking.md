# Module 11: Session Hijacking - Lab Guide

## Tools Used & Purpose

- **Caido**: Lightweight web security proxy for intercepting, modifying, and replaying HTTP requests and stolen session tokens.
- **Hetty**: Fast modular HTTP interception proxy for inspecting request headers, session cookies, and tampering with application states.
- **Bettercap**: Complete MITM framework performing ARP spoofing, DNS spoofing, and sniffing active session cookies from cleartext traffic.
- **Wireshark**: Inspecting intercepted web traffic to extract session cookies (e.g., `PHPSESSID`), authentication tokens, and TCP sequence numbers.
- **Burp Suite (Sequencer)**: Evaluating the predictability and cryptographic entropy of session tokens to determine session prediction feasibility.
- **OWASP ZAP**: Intercepting web traffic, token manipulation, and replaying authenticated requests to hijack user sessions.
- **Scapy**: Python packet manipulation library used to craft custom TCP packets with predicted sequence numbers for session desynchronization.

---

## 6. Detailed Hands-On Labs (Official CEHv13 Curriculum)

### Lab 1: Perform Session Hijacking

#### Task 1: Hijack a Session using Caido

- <b>Lab Duration:</b> 25 Minutes \| <b>Required Privilege:</b> Administrator
- <b>Target Environment:</b>
  - <i>Attacker VM:</i> Windows 11 (<code>10.10.1.11</code>) running Caido proxy
  - <i>Victim VM:</i> Windows Server 2019 (<code>10.10.1.19</code>) accessing web apps

#### Practical Execution Steps:

1. <b>Prepare Network Environment & Launch Caido:</b>
   - On Windows 11, open Command Prompt and flush the DNS cache:
     ```shell
     ipconfig /flushdns
     ```
   - Launch Caido from the Start menu.
   - In Caido, edit instance settings: select <b>All interfaces (0.0.0.0)</b> to allow remote machines on the subnet to route through the proxy on port <code>8080</code>, and click <b>Save</b> $\rightarrow$ <b>Start</b>.
   - Create a new project named <code>Session Hijacking</code>.
   - On the left navigation pane, navigate to <b>Intercept</b> and ensure request interception is active.
2. <b>Install Caido Root CA on Victim Machine:</b>
   - Switch to the victim machine (Windows Server 2019).
   - Open Mozilla Firefox and download the Caido root certificate by navigating to:
     ```txt
     http://10.10.1.11:8080/ca.crt
     ```
   - In Firefox Settings, search for <b>Certificates</b> $\rightarrow$ click <b>View Certificates...</b> $\rightarrow$ select the <b>Authorities</b> tab $\rightarrow$ click <b>Import...</b>.
   - Select the downloaded <code>ca.crt</code> file, check <b>Trust this CA to identify websites</b>, and click <b>OK</b>.
3. <b>Configure Victim Browser Proxy:</b>
   - In Firefox Settings on Windows Server 2019, search for <b>Proxy</b> $\rightarrow$ open <b>Connection Settings...</b>.
   - Select <b>Manual proxy configuration</b>:
     - <i>HTTP Proxy:</i> <code>10.10.1.11</code>
     - <i>Port:</i> <code>8080</code>
     - Check the box: <b>Also use this proxy for HTTPS</b>.
     - Click <b>OK</b>.
4. <b>Intercept and Manipulate Active Web Sessions:</b>
   - On the victim machine, browse to <code>http://www.moviescope.com</code>.
   - Switch to the attacker machine (Windows 11). Observe that Caido intercepts the HTTP GET requests from <code>10.10.1.19</code> in real-time.
   - On the <b>Requests</b> tab in Caido, tamper with the incoming request:
     - Replace the requested host header and URL <code>www.moviescope.com</code> with <code>www.goodshopping.com</code>.
     - Click <b>Forward</b> for all successive requests.
   - Switch back to the victim machine: Although the browser address bar still shows <code>www.moviescope.com</code>, the actual webpage content rendered on the victim's screen has been hijacked to display <code>www.goodshopping.com</code>!

---

#### Task 2: Intercept HTTP Traffic using Hetty

- <b>Target Environment:</b>
  - <i>Attacker VM:</i> Windows 11 (<code>10.10.1.11</code>) running Hetty
  - <i>Victim VM:</i> Windows Server 2022 (<code>10.10.1.22</code>) accessing <code>http://www.moviescope.com</code>

#### Practical Execution Steps:

1. <b>Initialize Hetty Proxy on Windows 11:</b>
   - Navigate to <code>E:\CEH-Tools\CEHv13 Module 11 Session Hijacking\Hetty</code> and launch <code>hetty.exe</code>.
   - Open Firefox and navigate to the local management dashboard:
     ```txt
     http://localhost:8080
     ```
   - Click <b>MANAGE PROJECTS</b> $\rightarrow$ enter Project name <code>Moviescope</code> $\rightarrow$ click <b>+ CREATE & OPEN PROJECT</b>.
   - From the left sidebar, click the <b>Proxy logs</b> icon to monitor real-time traffic.
2. <b>Configure Victim System Proxy on Windows Server 2022:</b>
   - On Windows Server 2022, open Windows Settings $\rightarrow$ <b>Network & Internet</b> $\rightarrow$ <b>Proxy</b>.
   - Under <b>Manual proxy setup</b>, toggle <b>Use a proxy server</b> to <b>On</b>:
     - <i>Address:</i> <code>10.10.1.11</code>
     - <i>Port:</i> <code>8080</code>
     - Click <b>Save</b>.
3. <b>Capture Cleartext Credentials & Session Data:</b>
   - On Windows Server 2022, open Google Chrome and navigate to <code>http://www.moviescope.com</code>.
   - Log into MovieScope using test credentials:
     - <b>Username:</b> <code>sam</code>
     - <b>Password:</b> <code>test</code>
   - Switch to Windows 11. In the Hetty <b>Proxy logs</b> dashboard, locate the captured <code>POST /login.html</code> request.
   - Click on the log entry $\rightarrow$ inspect the <b>Body</b> tab:
     - The victim's plain-text credentials (<code>sam</code> / <code>test</code>) and server-issued session cookies are clearly exposed in the request payload.

---

### Lab 2: Detect Session Hijacking using Wireshark & Bettercap

- <b>Target Environment:</b>
  - <i>Attacker VM:</i> Parrot Security (<code>10.10.1.13</code>) running Bettercap
  - <i>Victim VM:</i> Windows 11 (<code>10.10.1.11</code>) running Wireshark

#### Practical Execution Steps:

1. <b>Initialize Network Capture on Windows 11:</b>
   - On Windows 11, launch Wireshark and begin capturing on the primary network interface (<code>Ethernet</code>).
2. <b>Launch Network-Level MitM & ARP Spoofing from Parrot Security:</b>
   - On Parrot Security, open a root shell (<code>sudo su</code>, password <code>toor</code>).
   - Launch Bettercap bound to the primary interface:
     ```bash
     bettercap -iface eth0
     ```
   - In the interactive Bettercap shell, activate discovery and ARP poisoning modules:
     ```txt
     net.probe on
     net.recon on
     net.sniff on
     ```
   - Bettercap sweeps the subnet (<code>10.10.1.0/24</code>), populates its endpoint table, and transmits continuous gratuitous ARP packets claiming to be the default gateway for <code>10.10.1.11</code>.
3. <b>Detect Anomalous Traffic Signatures in Wireshark:</b>
   - Switch to Windows 11 and inspect the Wireshark packet capture.
   - <i>Observation:</i> Filter for <code>arp</code>. Wireshark displays a massive flood of unsolicited ARP replies originating from <code>10.10.1.13</code>.
   - Wireshark triggers internal protocol warnings:
     ```txt
     [Duplicate IP address detected for 10.10.1.1 (also in use by 00:0c:29:...)]
     ```
   - This anomalous signature confirms an active ARP Poisoning / Man-in-the-Middle attack attempting to intercept and hijack local network sessions.

---

## 7. CEHv13 High-Frequency Exam Anchors & Review Checklist

### 7.1 Core Exam Distinctions Summary

- <b>Spoofing vs. Hijacking:</b> Spoofing <i>initiates</i> a connection by pretending to be someone else (prior to authentication); Hijacking <i>takes over</i> an already established, authenticated session.
- <b>Session Fixation vs. Session Hijacking:</b> In Session Fixation, the attacker provides a known session ID to the victim <i>before</i> login; in classic hijacking, the attacker steals or predicts the session ID <i>after</i> login.
- <b>IPsec AH vs. ESP:</b>
  - <b>AH (Protocol 51):</b> Authentication + Integrity + Anti-Replay (<b>NO Encryption/Confidentiality</b>).
  - <b>ESP (Protocol 50):</b> Confidentiality (Encryption) + Authentication + Integrity + Anti-Replay.
- <b>IPsec Transport Mode vs. Tunnel Mode:</b>
  - <b>Transport Mode:</b> Encrypts/authenticates payload only; original IP header is preserved (Host-to-Host).
  - <b>Tunnel Mode:</b> Encrypts entire original IP packet (header + payload) inside a new IP packet (Gateway-to-Gateway / VPN).
- <b>The </b><b><code>HttpOnly</code></b><b> Cookie Flag:</b> Specifically prevents client-side scripts (JavaScript / XSS) from reading or manipulating <code>document.cookie</code>.
- <b>ACK Storm:</b> A phenomenon during TCP hijacking where desynchronized client and server continuously exchange acknowledgment packets back and forth trying to re-establish sequence parity.
- <b>CRIME vs. BREACH Attacks:</b> CRIME exploits <b>TLS-level compression</b>; BREACH exploits <b>HTTP response-level compression</b> (gzip).
