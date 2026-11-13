# Module 03: Scanning Networks - Lab Guide

## Tools Used & Purpose

- **Nmap**: Network host discovery (ARP, ICMP, TCP/UDP pings), port scanning, service/version detection, OS fingerprinting, and perimeter evasion.
- **Wireshark**: Packet inspection, analyzing 3-way handshakes, monitoring TTL values, and verifying scan evasion techniques at the wire level.
- **Hping3**: Custom packet crafting, TCP/UDP/ICMP probing, firewall rule statefulness testing, and SYN flood denial-of-service simulations.
- **Zenmap**: GUI interface for Nmap to manage scan profiles, inspect host topology graphs, and filter open port outputs.
- **Metasploit Framework**: Automating multi-threaded port scans and service version identification using auxiliary modules (`auxiliary/scanner/portscan/syn`, `auxiliary/scanner/smb/smb_version`).
- **ShellGPT (`sgpt`)**: Natural language CLI automation for ping sweeps, stealth scanning pipelines, and automated scanning script generation.
- **Advanced IP Scanner**: Multi-threaded Windows GUI network scanner for rapid device discovery, MAC address identification, and shared folder detection.
- **Colasoft Packet Builder**: Creating, editing, and transmitting custom raw packet fragments and hex payloads to test IDS/IPS detection thresholds.
- **SolarWinds Network Topology Mapper (NTM)**: Automated discovery of network devices and generation of exportable network topology maps.

---

## Hands-On Lab Walkthroughs (Labs 1–6)

<i>(Verified against Official CEH v13 Lab Manual, Pages 63–124)</i>

### Lab 1: Perform Host Discovery

- <b>Objective:</b> Discover active machines across <code>10.10.1.0/24</code> using various Nmap ping options.
- <b>Executed Commands & Observations:</b>
  - <code>nmap -sn -PR 10.10.1.11</code>: ARP Ping Scan. Extremely fast; returns MAC address and vendor.
  - <code>nmap -sn -PU 10.10.1.11</code>: UDP Ping to port 40,125. Returns host up if ICMP Port Unreachable received.
  - <code>nmap -sn -PE 10.10.1.11</code>: ICMP Echo Ping. Standard ping probe.
  - <code>nmap -sn -PE 10.10.1.10-23</code>: Subnet sweep discovering active Windows 11 (<code>.11</code>), Server 2022 (<code>.22</code>), Server 2019 (<code>.19</code>), and Ubuntu (<code>.9</code>).
  - <code>nmap -sn -PP 10.10.1.11</code>: ICMP Timestamp Ping (Type 13).
  - <code>nmap -sn -PM 10.10.1.11</code>: ICMP Address Mask Ping (Type 17).
  - <code>nmap -sn -PS 10.10.1.11</code>: TCP SYN Ping to port 80.
  - <code>nmap -sn -PA 10.10.1.11</code>: TCP ACK Ping to port 80. Returns <code>RST</code> indicating live host.
  - <code>nmap -sn -PO 10.10.1.11</code>: IP Protocol Ping across IP protocols 1, 2, 4.

### Lab 2: Perform Port and Service Discovery

- <b>Objective:</b> Identify open ports, services, and evaluate firewall filtering responses.
- <b>Executed Commands & Observations:</b>
  - <code>nmap -sT -v 10.10.1.22</code>: Full TCP Connect Scan. Completes 3-way handshake on ports 53, 88, 135, 139, 389, 445, 464, 593, 636, 3268, 3269, 3389.
  - <b>Firewall Enablement:</b> Enabled Windows Defender Firewall on Windows Server 2022 (<code>10.10.1.22</code>).
  - <code>nmap -sS -v 10.10.1.22</code>: Stealth SYN Scan. Fast and bypasses standard application-level logging.
  - <code>nmap -sX -v 10.10.1.22</code>: Xmas Scan. When firewall was enabled, returned all ports as <code>open|filtered</code> because Windows drops non-standard flags with <code>RST</code>, which the firewall dropped.
  - <code>nmap -sM -v 10.10.1.22</code>: Maimon Scan (<code>FIN/ACK</code>). Returns <code>open|filtered</code> or <code>closed</code>.
  - <code>nmap -sA -v 10.10.1.22</code>: ACK Flag Probe. Without firewall, all ports returned <code>unfiltered</code> (<code>RST</code> received). With firewall enabled, returned <code>filtered</code> (no response).
  - <code>nmap -sU -v 10.10.1.22</code>: UDP Scan. Discovered open UDP ports 53 (DNS), 88 (Kerberos), 123 (NTP), 389 (LDAP).

### Lab 3: Perform OS Discovery (Banner Grabbing)

- <b>Objective:</b> Fingerprint OS and service versions using Nmap and NSE scripts.
- <b>Executed Commands & Observations:</b>
  - <code>nmap -O 10.10.1.22</code>: Active OS Detection. Identifies Microsoft Windows Server 2022.
  - <code>nmap -A 10.10.1.22</code>: Aggressive scan incorporating OS, version detection, script scanning, and traceroute.
  - <code>nmap --script smb-os-discovery.nse 10.10.1.22</code>:
    - <b>Host Script Result:</b>
      - OS: <code>Windows Server 2022 Standard 20348</code>
      - Computer name: <code>Server2022</code>
      - NetBIOS computer name: <code>SERVER2022</code>
      - Domain name: <code>CEH.com</code>
      - Forest name: <code>CEH.com</code>
      - FQDN: <code>Server2022.CEH.com</code>
      - System time: Displays server clock-skew.

### Lab 4: Scan Beyond IDS and Firewall (Evasion Labs)

- <b>Objective:</b> Bypass perimeter packet filters and hide attacker identity.
- <b>Executed Commands & Wireshark Observations:</b>
  - <code>nmap -f 10.10.1.11</code>: Packet Fragmentation (8-byte chunks). Wireshark verified IP packets with <code>Flags: 0x01 (More Fragments)</code>, <code>Fragment offset: 0</code> and <code>Fragment offset: 8</code>.
  - <code>nmap -g 80 10.10.1.11</code>: Source Port Manipulation. Wireshark confirmed all outbound SYN probes originated from source port <code>80</code>.
  - <code>nmap -mtu 8 10.10.1.11</code>: Custom MTU tuning.
  - <code>nmap -D RND:10 10.10.1.11</code>: Decoy Scan. Wireshark verified 10 spoofed IP addresses transmitting SYN packets simultaneously alongside real attacker IP <code>10.10.1.13</code>.
  - <code>nmap -sT -Pn --spoof-mac 0 10.10.1.11</code>: MAC Address Spoofing. Wireshark confirmed random source MAC address on Ethernet frames.

### Lab 5: Network Scanning using Metasploit

- <b>Objective:</b> Execute network reconnaissance and port scanning from Metasploit Framework.
- <b>Executed Commands & Modules:</b>
  - <code>msfconsole -q</code>
  - <code>nmap -Pn -sS -A -oX Test 10.10.1.0/24</code>: Direct Nmap execution inside msfconsole.
  - <code>use auxiliary/scanner/portscan/syn</code>: Parameterized <code>RHOSTS 10.10.1.22</code>, <code>PORTS 80,445,3389</code>, <code>THREADS 10</code>, <code>run</code>.
  - <code>use auxiliary/scanner/smb/smb_version</code>: Parameterized <code>RHOSTS 10.10.1.22</code>, <code>run</code>. Extracted exact SMB dialect and Windows build.

### Lab 6: Perform Network Scanning using AI (ShellGPT / <code>sgpt</code>)

- <b>Objective:</b> Use LLM natural language prompts in Parrot Security terminal to orchestrate scanning.
- <b>Executed Commands:</b>
  - <code>sgpt --chat scan --shell "Use Hping3 to perform ICMP scanning on target IP address 10.10.1.11 and stop after 10 iterations"</code> → Executes <code>hping3 --icmp --count 10 10.10.1.11</code>.
  - <code>sgpt --chat scan --shell "Use Hping3 to perform ACK scan on port 80 of target IP 10.10.1.11"</code> → Executes <code>hping3 -A -p 80 10.10.1.11</code>.
  - <code>sgpt --chat scan --shell "Scan the target network 10.10.1.0/24 for active hosts and place only the IP addresses into a file scan1.txt"</code> → Executes <code>nmap -sn 10.10.1.0/24 -oG - | awk '/Up$/{print $2}' > scan1.txt</code>.
  - <code>sgpt --chat scan --shell "Use Nmap to scan for open ports and services against a list of IP addresses in scan1.txt and copy only the port, service and version information with the respective IP address to a new file called scan3.txt"</code> → Generates awk parsing pipeline.
  - <code>sgpt --chat scan --shell "Use TTL to identify the operating system running on the target IP address 10.10.1.11"</code> → Executes ping with TTL threshold evaluation.
  - <code>sgpt --chat scancode --code "develop a python script which will automate network scanning efforts and find open ports, services and vulnerabilities"</code> → Generates <code>python_scan.py</code> executing Nmap + Nikto via Python <code>subprocess.run()</code>.
