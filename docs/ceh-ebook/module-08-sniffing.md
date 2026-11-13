# Module 08: Sniffing - Lab Guide

## Tools Used & Purpose

- **Wireshark**: Capturing network packet frames, analyzing communication protocols, reconstructing cleartext sessions, and carving transmitted files.
- **tcpdump**: Command-line packet capture and protocol filtering on Linux network interfaces.
- **macof**: Flooding switch CAM tables with randomized MAC addresses to force the switch into fail-open (hub) broadcast mode.
- **Yersinia**: Executing Layer 2 protocol manipulation attacks (DHCP starvation, STP root bridge takeover, 802.1Q trunking).
- **Cain & Abel**: Conducting dynamic ARP spoofing / cache poisoning, credential sniffing, and password hash extraction on switched LANs.
- **rpcapd**: Remote packet capture daemon enabling remote network interfaces to stream live packet captures into a central Wireshark instance.
- **Nmap (`sniffer-detect.nse`)**: Scanning local subnets to detect network interface cards operating in promiscuous (sniffing) mode.
- **Promqry / XArp**: Auditing network segments to detect promiscuous mode interfaces and alert on ARP spoofing attacks in real time.

---

# Part II: Hands-on Lab Exercises

## Lab 01: Perform Active Sniffing

### Lab Overview & Topology

- <b>Lab Purpose</b>: Demonstrate how an attacker actively bypasses switch port isolation by executing MAC flooding to force fail-open hub behavior, and performs a DHCP starvation attack to exhaust network IP leases.
- <b>Target Environment</b>:
  - Attacker Machine: Parrot Security Linux (<code>10.10.1.13</code>)
  - Target Machines: Windows Server 2022 (<code>10.10.1.19</code>), Windows Server 2019, Windows 11 (<code>10.10.1.11</code>)
- <b>Primary Tools</b>: <b>macof (dsniff suite), Yersinia, Wireshark</b>

---

### Task 1: Perform MAC Flooding using macof

#### Operational Methodology & Step-by-Step Procedure

1. <b>Initialize Traffic Baseline in Wireshark</b>:
   - On the Parrot Security machine (<code>10.10.1.13</code>), launch Wireshark as root (<code>sudo wireshark</code>).
   - Select the primary network interface <b><code>eth0</code></b> and click the Start icon to monitor live traffic.
2. <b>Execute MAC Flooding Attack via macof</b>:
   - Open a root terminal session (<code>sudo su</code>, password: <code>toor</code>).
   - Launch <code>macof</code> to flood the local switch port with randomized Ethernet frames:
     ```bash
     macof -i eth0 -n 100
     ```

     <p>
     <i>(Note: </i><i><code>-i eth0</code></i><i> specifies the target interface; </i><i><code>-n</code></i><i> specifies the packet count. In an unrestricted attack, omit </i><i><code>-n</code></i><i> to flood continuously).</i>
     </p>
3. <b>Analyze Packet Storm in Wireshark</b>:
   - Switch to Wireshark and observe the massive flood of newly captured packets.
   - Every captured packet displays a completely randomized source MAC address and randomized source IP address.
   - Observe how the switch CAM table becomes saturated.
4. <b>Verify Hub Mode Broadcasts on Target Systems</b>:
   - Switch to the secondary target machine (e.g., Windows Server 2022 or Windows 11).
   - Open a packet capture on the target machine. Observe that the exact same randomized MAC flood packets captured on Parrot Linux are now being broadcast across all switch ports, confirming the switch has failed open into a Hub.
5. <b>Terminate Attack & Restore Baseline</b>:
   - Press <code>Ctrl + C</code> in the Parrot terminal to terminate <code>macof</code>.

#### Realistic Output Analysis & Artifacts

```javascript
===================================================================
MACOF PACKET INJECTION - CONSOLE CAPTURE
===================================================================
root@parrot:~# macof -i eth0 -n 20
0:0:0:0:0:0 10.10.1.13.4426 > 0:0:0:0:0:0 10.10.1.22.867: S 512
0:0:0:0:0:0 10.10.1.13.60627 > 0:0:0:0:0:0 10.10.1.24.901: S 512
0:0:0:0:0:0 10.10.1.13.46128 > 0:0:0:0:0:0 10.10.1.92.81: S 512
0:0:0:0:0:0 10.10.1.13.18607 > 0:0:0:0:0:0 10.10.1.32.831: S 512
0:0:0:0:0:0 10.10.1.13.58295 > 0:0:0:0:0:0 10.10.1.52.728: S 512
[+] 20 packets sent across eth0 ... CAM table saturation verified.
===================================================================
```

---

### Task 2: Perform DHCP Starvation Attack using Yersinia

#### Operational Methodology & Step-by-Step Procedure

1. <b>Launch Yersinia in Interactive Mode</b>:
   - In the Parrot Linux root terminal, execute:
     ```bash
     yersinia -I
     ```

     <p>
     <i>(Note: </i><i><code>-I</code></i><i> starts the ncurses interactive terminal interface).</i>
     </p>
2. <b>Select DHCP Protocol Mode</b>:
   - Press <b><code>F2</code></b> on the keyboard to switch protocol mode from STP to <b>DHCP mode</b>.
   - Observe the lower status panel update, displaying DHCP fields: <code>MessageType</code>, <code>Source MAC</code>, <code>Destination MAC (255.255.255.255)</code>, <code>SIP (0.0.0.0)</code>, and <code>DIP (255.255.255.255)</code>.
3. <b>Configure & Launch DHCP Starvation</b>:
   - Press <b><code>x</code></b> to open the Yersinia <b>Attack Panel</b>.
   - Press <b><code>1</code></b> to select: <b><code>sending RAW packet</code></b><b> / </b><b><code>sending DISCOVER packet</code></b>.
   - Yersinia immediately begins generating and broadcasting an immense volume of <code>DHCPDISCOVER</code> packets, cycling source MAC addresses rapidly.
4. <b>Monitor Protocol Depletion in Wireshark</b>:
   - Open Wireshark and set the display filter to:
     ```javascript
     bootp || dhcp
     ```
   - Observe hundreds of incoming <code>DHCPDISCOVER</code> frames broadcast across the subnet per second.
   - Legitimate DHCP servers respond with <code>DHCPOFFER</code> packets until the IP pool is exhausted. Once depleted, any new device attempting to join the network receives an APIPA address (<code>169.254.x.x</code>), confirming full DoS.
5. <b>Stop the Attack</b>:
   - In Yersinia, press <b><code>x</code></b> and then select <b><code>l</code></b> (or press <code>Ctrl + C</code>) to halt the starvation flood.

---

## Lab 02: Perform Network Sniffing using Various Sniffing Tools

### Lab Overview & Topology

- <b>Lab Purpose</b>: Capture and extract sensitive application authentication credentials transmitted in cleartext over HTTP, and configure Wireshark to perform remote packet capture over the network using the <code>rpcapd</code> service.
- <b>Target Environment</b>:
  - Attacker / Analyst Machine: Windows Server 2019 / Windows 11 (<code>10.10.1.19</code> / <code>10.10.1.11</code>)
  - Application Server: MOVIESCOPE Web Application (<code>10.10.1.19:8080</code>)
- <b>Primary Tools</b>: <b>Wireshark, Remote Packet Capture Protocol (rpcapd)</b>

---

### Task 1: Analyze Network Traffic using Wireshark (Credential Harvesting)

#### Operational Methodology & Step-by-Step Procedure

1. <b>Initialize Packet Capture</b>:
   - On Windows Server 2019, launch <b>Wireshark</b>.
   - Double-click the primary Ethernet interface to start capturing live packets.
2. <b>Generate Target Web Traffic</b>:
   - Switch to the Windows 11 workstation (<code>10.10.1.11</code>).
   - Open Mozilla Firefox and navigate to the enterprise web portal:<br /><code>http://www.moviescope.com</code> (or target IP <code>http://10.10.1.19:8080</code>).
   - On the login page, enter valid user credentials:
     - <b>Username</b>: <code>sam</code>
     - <b>Password</b>: <code>test</code>
   - Click <b>Login</b>.
3. <b>Isolate and Reconstruct Authentication in Wireshark</b>:
   - Return to Wireshark on Windows Server 2019. Click the red square icon to stop capturing.
   - In the display filter bar, apply:
     ```javascript
     http.request.method == "POST"
     ```
   - Press Enter. Wireshark filters out all non-essential frames, isolating the specific HTTP POST request.
4. <b>Extract Plaintext Credentials</b>:
   - Click on the filtered POST packet.
   - Expand the <b><code>HTML Form URL Encoded: application/x-www-form-urlencoded</code></b> subtree in the packet details pane.
   - View the extracted form values:
     - <code>username: sam</code>
     - <code>password: test</code>
   - Right-click the packet and select <b>Follow -> HTTP Stream</b> to view the entire unencrypted login transaction in full text.

---

### Task 2: Perform Remote Packet Sniffing using Wireshark & rpcapd

#### Operational Methodology & Step-by-Step Procedure

1. <b>Enable rpcapd Service on Remote Target Machine</b>:
   - On the Windows 11 machine (<code>10.10.1.11</code>), open the Windows Services console (<code>services.msc</code>).
   - Locate the <b><code>Remote Packet Capture Protocol v.0 (experimental)</code></b> service (<code>rpcapd</code>).
   - Right-click the service and select <b>Start</b>. Verify status changes to <b>Running</b>.
2. <b>Configure Remote Interface in Local Wireshark</b>:
   - Switch to the analyst workstation (Windows Server 2019).
   - In Wireshark, click the <b>Capture -> Options</b> gear icon (or press <code>Ctrl + K</code>).
   - In the bottom-right corner, click <b>Manage Interfaces</b>.
   - Select the <b>Remote Interfaces</b> tab and click the <b>Add (</b><b><code>+</code></b><b>)</b> icon.
3. <b>Authenticate to Remote Host</b>:
   - In the Remote Interface dialog, configure:
     - <b>Host</b>: <code>10.10.1.11</code>
     - <b>Port</b>: <code>2002</code> (Default rpcapd port)
     - Select <b>Password authentication</b>.
     - <b>User</b>: <code>Jason</code> (or target administrator account)
     - <b>Password</b>: <code>qwerty</code>
   - Click <b>OK</b>.
4. <b>Capture Remote Target Traffic Live</b>:
   - Wireshark queries the remote agent and lists all physical network adapters present on the remote Windows 11 machine.
   - Select the remote Ethernet adapter and click <b>Start</b>.
   - Wireshark now captures all traffic passing through the remote machine's physical network adapter in real time across the network connection.

---

## Lab 03: Detect Network Sniffing

### Lab Overview & Topology

- <b>Lab Purpose</b>: Demonstrate technical methodologies used to detect active ARP poisoning attacks using Wireshark's Expert Information system, and detect remote machines operating in promiscuous mode using Nmap NSE scripts.
- <b>Target Environment</b>:
  - Attacker Machine: Windows Server 2019 (<code>10.10.1.19</code>) running Cain & Abel
  - Victim / Sniffing Target: Windows 11 (<code>10.10.1.11</code>)
  - Scanning / Detection Machine: Parrot Security Linux (<code>10.10.1.13</code>)
- <b>Primary Tools</b>: <b>Cain & Abel, Wireshark, Nmap NSE (</b><b><code>sniffer-detect</code></b><b>)</b>

---

### Task 1: Detect ARP Poisoning using Wireshark and Cain & Abel

#### Operational Methodology & Step-by-Step Procedure

1. <b>Launch ARP Poisoning in Cain & Abel</b>:
   - On Windows Server 2019 (<code>10.10.1.19</code>), launch <b>Cain & Abel</b>.
   - Configure the sniffer adapter, then click the <b>Start/Stop Sniffer</b> icon.
   - Navigate to the <b>Sniffer -> Hosts</b> tab, right-click, and select <b>Scan MAC Addresses</b> to discover subnet nodes (<code>10.10.1.11</code> and <code>10.10.1.13</code>).
   - Click the <b>APR (ARP Poison Routing)</b> tab at the bottom.
   - Click the <b>Add (</b><b><code>+</code></b><b>)</b> icon. Select <code>10.10.1.11</code> (Windows 11) in the left pane and <code>10.10.1.13</code> (Parrot Linux) in the right pane. Click <b>OK</b>.
   - Click the yellow <b>Start/Stop APR</b> button to initiate active bidirectional ARP poisoning.
2. <b>Observe ARP Anomalies in Wireshark</b>:
   - On the Parrot Linux machine (<code>10.10.1.13</code>), launch Wireshark on interface <code>eth0</code>.
   - Apply the display filter:
     ```javascript
     arp
     ```
   - Observe high-frequency Gratuitous ARP packets arriving on the wire claiming that multiple IP addresses map to the exact same MAC address (<code>00:0c:29:8b:24:6a</code>).
3. <b>Analyze Wireshark Expert Information</b>:
   - Click the circle icon in the bottom-left corner of the Wireshark window (or select <b>Analyze -> Expert Information</b>).
   - Expand the <b>Warnings (Yellow)</b> category.
   - <b>Observed Forensic Indicator</b>: Wireshark explicitly flags:
     - <b><code>Duplicate IP address detected for 10.10.1.11 (00:0c:29:8b:24:6a) - also in use by (00:0c:29:a4:21:09)</code></b>.
   - This proves conclusively that an ARP poisoning / MitM attack is actively executing on the switched LAN.

---

### Task 2: Detect Promiscuous Mode using Nmap NSE

#### Operational Methodology & Step-by-Step Procedure

1. <b>Ensure Target Machine is Running Sniffer</b>:
   - On the target Windows 11 workstation (<code>10.10.1.11</code>), ensure Wireshark or another sniffer is actively capturing traffic (placing the NIC into Promiscuous mode).
2. <b>Execute Nmap Promiscuous Detection Script</b>:
   - On the Parrot Linux machine (<code>10.10.1.13</code>), open a root terminal.
   - Execute the Nmap script:
     ```bash
     sudo nmap -sV --script=sniffer-detect 10.10.1.11
     ```
3. <b>Examine Detection Verdict</b>:
   - Nmap sends a series of crafted Ethernet frames containing the target's IP address (<code>10.10.1.11</code>) paired with deliberately mismatched/bogus MAC addresses.
   - Because the target NIC is in promiscuous mode, the hardware filter is bypassed, and the OS replies to the probe.
   - Nmap reports:
     ```javascript
     Host script results:
     |_sniffer-detect: Likeliest opinion: Promiscuous mode detected!
     ```
   - If Wireshark is closed on the target (returning the NIC to non-promiscuous mode) and the scan is re-run, Nmap reports:
     ```javascript
     |_sniffer-detect: Likeliest opinion: Not promiscuous
     ```
