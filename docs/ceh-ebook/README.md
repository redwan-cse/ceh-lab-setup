# CEH v13 Practical Lab Guide & E-Book
This directory contains extracted hands-on lab guides for each CEH v13 module from the official course notes. Each module document outlines all required security tools, their specific operational purposes, and the step-by-step practical lab walkthroughs.
| Module | Topic | Lab Documentation | Primary Lab Tools |
| :--- | :--- | :--- | :--- |
| **Module 01** | Introduction to Ethical Hacking | [module-01-introduction-to-ethical-hacking.md](module-01-introduction-to-ethical-hacking.md) | None (Theory & Legal Frameworks Only) |
| **Module 02** | Footprinting and Reconnaissance | [module-02-footprinting-and-reconnaissance.md](module-02-footprinting-and-reconnaissance.md) | Google Advanced Search / Google Dorking, Netcraft, DNSdumpster, Sherlock, DomainTools, ... |
| **Module 03** | Scanning Networks | [module-03-scanning-networks.md](module-03-scanning-networks.md) | Nmap, Wireshark, Hping3, Zenmap, Metasploit Framework, ... |
| **Module 04** | Enumeration | [module-04-enumeration.md](module-04-enumeration.md) | nbtstat, NetBIOS Enumerator, snmpwalk / snmp-check, Active Directory Explorer (AD Explorer), ldap3 (Python), ... |
| **Module 05** | Vulnerability Analysis | [module-05-vulnerability-analysis.md](module-05-vulnerability-analysis.md) | OpenVAS (Greenbone Vulnerability Management), Nessus Essentials, GFI LanGuard, Qualys VMDR, Nikto, ... |
| **Module 06** | System Hacking | [module-06-system-hacking.md](module-06-system-hacking.md) | Responder, Hashcat, John the Ripper, Metasploit Framework, Immunity Debugger with Mona.py, ... |
| **Module 07** | Malware Threats | [module-07-malware-threats.md](module-07-malware-threats.md) | njRAT, JPS Virus Maker, Hybrid Analysis, Detect It Easy (DIE) / PEiD, IDA Pro / OllyDbg, ... |
| **Module 08** | Sniffing | [module-08-sniffing.md](module-08-sniffing.md) | Wireshark, tcpdump, macof, Yersinia, Cain & Abel, ... |
| **Module 09** | Social Engineering | [module-09-social-engineering.md](module-09-social-engineering.md) | Social-Engineer Toolkit (SET), Netcraft Anti-Phishing Extension, PhishTank, ChatGPT / AI Prompts, OhPhish / GoPhish |
| **Module 10** | Denial-of-Service | [module-10-denial-of-service.md](module-10-denial-of-service.md) | LOIC (Low Orbit Ion Cannon), HOIC (High Orbit Ion Cannon), ISB (I'm So Bored), UltraDDOS-v2, Hping3, ... |
| **Module 11** | Session Hijacking | [module-11-session-hijacking.md](module-11-session-hijacking.md) | Caido, Hetty, Bettercap, Wireshark, Burp Suite (Sequencer), ... |
| **Module 12** | Evading IDS, Firewalls, and Honeypots | [module-12-evading-ids-firewalls-and-honeypots.md](module-12-evading-ids-firewalls-and-honeypots.md) | Snort, Suricata, Cowrie, BITSAdmin, Nmap, ... |
| **Module 13** | Hacking Web Servers | [module-13-hacking-web-servers.md](module-13-hacking-web-servers.md) | Netcraft / WhatWeb, Telnet / Netcat, Nmap, WAFW00F, THC Hydra, ... |
| **Module 14** | Hacking Web Applications | [module-14-hacking-web-applications.md](module-14-hacking-web-applications.md) | Burp Suite, OWASP ZAP, Recon-ng, Vega / Wapiti, Wfuzz / ffuf / Gobuster, ... |
| **Module 15** | SQL Injection | [module-15-sql-injection.md](module-15-sql-injection.md) | SQLMap, jSQL Injection, Havij, BBQSQL, NoSQLMap, ... |
| **Module 16** | Hacking Wireless Networks | [module-16-hacking-wireless-networks.md](module-16-hacking-wireless-networks.md) | Aircrack-ng, Airmon-ng, Airodump-ng, Aireplay-ng, Airbase-ng, ... |
| **Module 17** | Hacking Mobile Platforms | [module-17-hacking-mobile-platforms.md](module-17-hacking-mobile-platforms.md) | PhoneSploit, AndroRAT, MobSF (Mobile Security Framework), Apktool, Dex2jar / JD-GUI / JADX, ... |
| **Module 18** | IoT and OT Hacking | [module-18-iot-and-ot-hacking.md](module-18-iot-and-ot-hacking.md) | Shodan / Censys, Wireshark, Bevywise IoT Simulator, Bevywise MQTTRoute, ICSim (Instrument Cluster Simulator), ... |
| **Module 19** | Cloud Computing | [module-19-cloud-computing.md](module-19-cloud-computing.md) | AWS CLI, AADInternals, lazys3 / S3Scanner, Trivy, Docker, ... |
| **Module 20** | Cryptography | [module-20-cryptography.md](module-20-cryptography.md) | CyberChef, CryptoForge, OpenSSL, ShellGPT (`sgpt`), VeraCrypt, ... |

---

## Certified Ethical Hacker (Practical) Exam Blueprint

> **Exam Format:** 6 hours, 20 hands-on practical questions, passing score 70% (14/20). Open-book environment with live targets and network access.

| Domain | Sub Domain | Number of Questions | Weightage (%) |
| :--- | :--- | :---: | :---: |
| **1. Information Security and Ethical Hacking** | Introduction to Ethical Hacking | 1 | 5% |
| **2. Reconnaissance Techniques** | Footprinting and Reconnaissance, Scanning Networks, Enumeration | 3 | 15% |
| **3. System Hacking Phases and Attack Techniques** | Vulnerability Analysis, System Hacking, Malware Threats | 3 | 15% |
| **4. Network and Perimeter Hacking** | Sniffing, Social Engineering, Denial-of-service, Session Hijacking, Evading IDS, Firewalls and Honeypots | 5 | 25% |
| **5. Web Application Hacking** | Hacking Web Servers, Hacking Web Applications, SQL Injection | 3 | 15% |
| **6. Tools/Systems/Programs** | Hacking Wireless Networks | 1 | 5% |
| **7. Mobile Platform, IoT and OT Hacking** | Hacking Mobile Platforms, IoT and OT Hacking | 2 | 10% |
| **8. Cloud Computing** | Cloud Computing | 1 | 5% |
| **9. Cryptography** | Cryptography | 1 | 5% |
| **Total** | | **20** | **100%** |

---

## Recommended Practical Exam Solving Order

> **Strategy Note:** Ranked by expected speed of obtaining an answer, not by syllabus order. Start with low-friction, high-confidence domains to lock in early points before tackling time-consuming multi-step exploitation scenarios.

| Priority | Domain | Questions | Estimated Difficulty | Recommended Tools & Tactics |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **9. Cryptography** | 1 | **Easy–Medium** | CyberChef, OpenSSL, Hashcat/John, VeraCrypt, BCTextEncoder |
| **2** | **2. Reconnaissance Techniques** | 3 | **Easy–Medium** | Nmap port/service scans, WHOIS, DNS queries (nslookup), theHarvester |
| **3** | **1. Information Security & Ethical Hacking** | 1 | **Likely Easy** | Regulatory frameworks, reconnaissance logic, basic perimeter discovery |
| **4** | **4. Network & Perimeter Hacking** | 5 | **Medium–Hard** | Wireshark (.pcap traffic analysis), Cain, Hping3, Snort rule evaluation |
| **5** | **5. Web Application Hacking** | 3 | **Medium** | Burp Suite, SQLMap, directory brute-forcing, parameter manipulation |
| **6** | **8. Cloud Computing** | 1 | **Medium, variable** | AWS CLI S3 bucket enumeration, Azure AD queries, container inspection |
| **7** | **3. System Hacking** | 3 | **Medium–Hard** | Responder, privilege escalation, Windows/Linux hash dumping & cracking |
| **8** | **6. Wireless Hacking** | 1 | **Medium–Hard** | Aircrack-ng, airodump-ng, dictionary attack on WPA2 4-way handshake |
| **9** | **7. Mobile, IoT & OT Hacking** | 2 | **Potentially Hard** | ICSim/can-utils, MQTT analysis, APK reverse-engineering (Apktool/dex2jar) |
