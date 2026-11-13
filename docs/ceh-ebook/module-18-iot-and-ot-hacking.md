# Module 18: IoT and OT Hacking - Lab Guide

## Tools Used & Purpose

- **Shodan / Censys**: Search engines for discovering internet-connected IoT devices, smart cameras, routers, and OT controllers.
- **Wireshark**: Capturing and dissecting IoT/OT network protocols (MQTT, CoAP, Modbus TCP, DNP3, CIP).
- **Bevywise IoT Simulator**: Simulating IoT sensor networks, devices, and message broker communication for security testing.
- **Bevywise MQTTRoute**: Centralized MQTT broker used to route, log, and analyze IoT publish/subscribe message streams.
- **ICSim (Instrument Cluster Simulator)**: Simulating CAN bus vehicle networks for automotive security auditing.
- **can-utils (`candump`, `cansniffer`, `canplayer`)**: Sniffing, filtering, and replaying CAN bus packet frames on vehicle networks.
- **Nmap**: Scanning for specialized IoT and OT/SCADA ports (e.g., Modbus port 502, EtherNet/IP port 44818, MQTT port 1883).
- **Binwalk**: Extracting and analyzing firmware file systems, embedded kernels, and bootloaders from IoT device ROMs.
- **Firmwalker**: Script for searching extracted IoT firmware file systems for sensitive keys, passwords, and certificates.

---

## 6. Hands-On Practical Labs Walkthrough

### Lab 1: Perform Footprinting using Various Footprinting Techniques

#### Task 1: Gather Information using Online Footprinting Tools

- <b>Environment:</b>
  - System: Windows 11 Virtual Machine (<code>10.10.1.11</code>).
  - Tools: Web Browser, Whois Domain Lookup, Google Hacking Database (GHDB), Shodan, Censys.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Investigate Target Protocols & Governing Standards via Whois:</b>
     - Open Mozilla Firefox on Windows 11 and navigate to <code>https://www.whois.com/whois</code>.
     - Query <code>www.oasis-open.org</code> (the international consortium governing the MQTT standard).
     - Review domain registrar details, administrative contacts, name servers, and raw Whois data to establish organizational intelligence.
  2. <b>Audit Google Hacking Database (GHDB) for Industrial Dorks:</b>
     - Navigate to <code>https://www.exploit-db.com/google-hacking-database</code>.
     - In the Quick Search field, type <code>SCADA</code>.
     - Review active dorks that discover exposed human-machine interfaces, PLC web management consoles, and unauthenticated industrial controllers:
       - <code>intitle:"SCADA Engine" inurl:8080</code>
       - <code>intext:"Siemens SIMATIC S7" inurl:index.htm</code>
  3. <b>Perform Global IoT Device Reconnaissance with Shodan:</b>
     - Navigate to <code>https://www.shodan.io</code>.
     - Search for exposed MQTT brokers: <code>port:1883 "MQTT"</code>.
     - Analyze banner output revealing broker version, client connection permissions, and geographic coordinates.
     - Search for Modbus controllers: <code>port:502</code>. Identify Unit IDs and PLC hardware details.

---

### Lab 2: Capture and Analyze IoT Traffic using Wireshark

#### Task 1: Capture and Analyze IoT Traffic using Wireshark

- <b>Environment:</b>
  - Attacking Machine: Windows 11 (<code>10.10.1.11</code>) running Wireshark & Bevywise IoT Simulator Client.
  - Server Machine: Windows Server 2019 (<code>10.10.1.19</code>) running Bevywise MQTTRoute Broker.
  - Protocols: MQTT (TCP Port 1883).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Initialize Bevywise MQTTRoute Broker on Windows Server 2019:</b>
     - Log in to Windows Server 2019 (<code>10.10.1.19</code>).
     - Navigate to <code>Z:\CEHv13 Module 18 IoT and OT Hacking\Bevywise IoT Simulator\</code> and run <code>Bevywise_MQTTRoute_4.exe</code>.
     - Complete installation and launch MQTTRoute.
     - Observe command prompt confirming broker is actively listening on TCP port <code>1883</code> and web socket port <code>8081</code>.
  2. <b>Launch Wireshark Packet Capture on Windows 11:</b>
     - Switch to Windows 11 (<code>10.10.1.11</code>) and launch Wireshark as Administrator.
     - Select the active network interface and start capture.
     - In the display filter bar, enter:
       ```javascript
       mqtt
       ```
  3. <b>Simulate IoT Telemetry Stream with Bevywise IoT Simulator:</b>
     - On Windows 11, install and run <code>Setup-IoTSimulator_3.0.exe</code>.
     - Configure simulated IoT smart devices (Temperature Sensor, Smart Light, Energy Meter).
     - Configure the target broker IP address to point to Windows Server 2019 (<code>10.10.1.19</code>) on port <code>1883</code>.
     - Click <b>Start Simulation</b> to begin transmitting telemetry events.
  4. <b>Analyze MQTT Handshake & Message Exchanges in Wireshark:</b>
     - Examine captured packets:
       - <b>Connect Command (</b><b><code>0x10</code></b><b>):</b> Client establishes connection; observe client identifier and Keep Alive timer in cleartext.
       - <b>Connect Ack (</b><b><code>0x20</code></b><b>):</b> Server acknowledges connection.
       - <b>Subscribe Request (</b><b><code>0x80</code></b><b>):</b> Client requests subscription to topics (e.g., <code>home/livingroom/temperature</code>).
       - <b>Publish Message (</b><b><code>0x30</code></b><b>):</b> Sensor transmits telemetry; inspect packet payload revealing cleartext temperature values and sensor metadata.
       - <b>Ping Request / Response (</b><b><code>0xC0</code></b><b> / </b><b><code>0xD0</code></b><b>):</b> Heartbeat packets maintaining the connection.

---

### Lab 3: Performing IoT Attacks

#### Task 1: Perform Replay Attack on CAN Protocol

- <b>Environment:</b>
  - Operating System: Ubuntu Virtual Machine (<code>10.10.1.9</code>).
  - Target Network: Virtual CAN Bus (<code>vcan0</code>).
  - Tools: <code>can-utils</code> (<code>candump</code>, <code>cansniffer</code>, <code>canplayer</code>), <code>ICSim</code> (Instrument Cluster Simulator).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Initialize Virtual CAN Interface in Ubuntu:</b>
     - Open terminal in Ubuntu, gain root privileges via <code>sudo su</code> (password: <code>toor</code>).
     - Install CAN utility suite:
       ```bash
       apt-get install can-utils -y
       ```
     - Load kernel modules and create a virtual CAN interface:
       ```bash
       modprobe can
       modprobe vcan
       ip link add dev vcan0 type vcan
       ip link set up vcan0
       ```
     - Run <code>ifconfig vcan0</code> to verify the interface is operational (<code>UP RUNNING NOARP</code>).
  2. <b>Launch Instrument Cluster Simulator (ICSim):</b>
     - Navigate to ICSim directory and compile:
       ```bash
       cd ICSim
       chmod -R 777 .
       make
       ```
     - Start the simulated vehicle instrument dashboard:
       ```bash
       ./icsim vcan0
       ```
     - Open a second terminal and start the CANBus Control Panel:
       ```bash
       ./controls vcan0
       ```
     - Press the accelerator key on the control panel; observe the speedometer needle rising in real time on the ICSim dashboard.
  3. <b>Sniff and Filter Automotive CAN Bus Frames:</b>
     - Open a third terminal and run <code>cansniffer</code> to identify the specific CAN arbitration ID governing vehicle speed:
       ```bash
       cansniffer -c vcan0
       ```
     - Observe dynamic packet changes; identify arbitration ID <code>244</code> or <code>188</code> fluctuating when the throttle is applied.
  4. <b>Record Real-Time CAN Packets:</b>
     - Start recording CAN bus traffic to an exfiltration log file:
       ```bash
       candump -l vcan0
       ```
     - Press the accelerator to generate speed packets, then press <code>Ctrl+C</code> to stop logging.
     - Verify log file generation (e.g., <code>candump-2026-11-03_xxxxxx.log</code>).
  5. <b>Execute Vehicle Replay Attack:</b>
     - Ensure the throttle is released on the control panel (speedometer returns to 0 MPH).
     - Replay the recorded acceleration packets into the virtual CAN bus:
       ```bash
       canplayer -I candump-2026-11-03_xxxxxx.log vcan0
       ```
     - <b>Observed Result:</b> The speedometer needle immediately spikes and mirrors the recorded acceleration sequence on the vehicle dashboard without touching the controls, demonstrating an unauthorized physical vehicle replay attack.

---

## 7. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| IT vs. OT Priorities       | IT focuses on C-I-A; OT strictly prioritizes Availability & Safety    |
| Priority Conflict          | (A-I-C); plant uptime and life safety outweigh data confidentiality.  |
+----------------------------+-----------------------------------------------------------------------+
| Purdue Model IDMZ          | Level 3.5 Industrial DMZ prevents direct IP communications between    |
| (ISA-99 / IEC 62443)       | Enterprise IT (Level 4) and Industrial Operations (Level 3).          |
+----------------------------+-----------------------------------------------------------------------+
| MQTT Ports & QoS           | Port 1883 (cleartext) / 8883 (TLS); Pub/Sub architecture;             |
|                            | QoS 0 (at most once), QoS 1 (at least once), QoS 2 (exactly once).    |
+----------------------------+-----------------------------------------------------------------------+
| CoAP Protocol Profile      | RESTful protocol over UDP; default port 5683 / 5684 (DTLS);           |
|                            | eliminates TCP 3-way handshake overhead for constrained nodes.        |
+----------------------------+-----------------------------------------------------------------------+
| Modbus Security Flaw       | Port 502 TCP; master/slave; lacks authentication and encryption;      |
|                            | vulnerable to unauthorized command injection & coil register overwrite|
+----------------------------+-----------------------------------------------------------------------+
| Mirai Botnet Vector        | Scans Telnet port 23/2323; brute-forces 62 default credentials;       |
|                            | launches massive volumetric SYN/ACK, GRE, and HTTP DDoS floods.       |
+----------------------------+-----------------------------------------------------------------------+
| Rolljam / Rolling Code     | Jams receiver frequency while sniffing/recording rolling code;        |
|                            | replays first code while saving second code for later access.         |
+----------------------------+-----------------------------------------------------------------------+
| Hardware Hacking (UART)    | TX, RX, GND, VCC pins identified with multimeter; provides unauth     |
|                            | interactive root console shell to bypass software security.           |
+----------------------------+-----------------------------------------------------------------------+
| Stuxnet Cyberweapon        | First ICS malware; targeted Siemens Step 7 / Simatic S7-300 PLCs;     |
|                            | sabotaged Natanz centrifuges while spoofing normal HMI telemetry.     |
+----------------------------+-----------------------------------------------------------------------+
| Industroyer / TRITON       | Industroyer speaks IEC 60870/61850 against electric substations;      |
|                            | TRITON targets Triconex Safety Instrumented Systems (SIS).            |
+----------------------------+-----------------------------------------------------------------------+
| Automotive CAN Bus         | Broadcast serial network lacking source authentication or encryption; |
| (can-utils tools)          | candump (sniff), cansniffer (isolate IDs), canplayer (replay attack). |
+----------------------------+-----------------------------------------------------------------------+
| Data Diode Defense         | Physical optical hardware allowing data flow in strictly one direction|
|                            | (OT to IT replica); physically prevents intrusions into OT network.   |
+----------------------------+-----------------------------------------------------------------------+
```
