# Module 20: Cryptography - Lab Guide

## Tools Used & Purpose

- **CyberChef**: Multi-functional web-based cryptographic Swiss Army knife for encoding, decoding, hashing, and decrypting data.
- **CryptoForge**: Windows-based file encryption utility utilizing AES, Triple-DES, and Blowfish algorithms.
- **OpenSSL**: Command-line cryptographic utility for generating keys, creating digital certificates, and symmetric/asymmetric encryption.
- **ShellGPT (`sgpt`)**: Generating custom cryptographic code, hash cracking scripts, and analyzing cryptographic parameters.
- **VeraCrypt**: Creating, mounting, and managing encrypted virtual disk volumes and partitions.
- **Hashcat / John the Ripper**: Auditing and recovering passwords from cryptographic hashes (MD5, SHA-256, NTLM).
- **BCTextEncoder / HashCalc**: Windows GUI tools for encoding plain text and computing cryptographic hash checksums.
- **GnuPG (GPG)**: Implementing OpenPGP encryption, digital signatures, and asymmetric key pair management.

---

## 6. Hands-On Practical Labs Walkthrough

### Lab 1: Encrypt the Information using Various Cryptography Tools

#### Task 1: Perform Multi-Layer Hashing using CyberChef

- <b>Environment:</b>
  - System: Windows 11 Virtual Machine (<code>10.10.1.11</code>).
  - Tool: CyberChef (The Cyber Swiss Army Knife).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Launch CyberChef in Web Browser:</b>
     - Open Mozilla Firefox on Windows 11 and navigate to <code>https://cyberchef.org/</code> (or local CyberChef offline build).
  2. <b>Construct Multi-Layer Cryptographic Recipe:</b>
     - In the Operations search panel, drag the following components into the <b>Recipe</b> pane:
       1. <code>MD5</code>
       2. <code>To Hexdump</code> or <code>To Base64</code>
       3. <code>SHA256</code>
  3. <b>Execute Multi-Stage Cryptographic Transformation:</b>
     - In the <b>Input</b> pane, enter sensitive data:
       ```txt
       AccountBalance: $1,000,000 - WireTransferAuthorized
       ```
     - Observe the step-by-step intermediate execution in the Output pane:
       - Level 1 MD5 Hash: <code>32-character hexadecimal digest</code>
       - Level 2 Base64 Encoding: Encodes the raw hash bytes
       - Level 3 SHA-256 Digest: Produces the final 64-character hash digest
     - Demonstrates data pipelines and layered verification routines.

---

#### Task 2: Perform File and Text Message Encryption using CryptoForge

- <b>Environment:</b>
  - System: Windows 11 (<code>10.10.1.11</code>) / Windows Server 2019.
  - Tool: <code>CryptoForge</code> (Military-grade file and text encryption).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Launch CryptoForge Text Editor:</b>
     - Launch CryptoForge from desktop shortcuts.
     - Select <b>CryptoForge Text</b> to open the secure text processing interface.
     - Type a confidential transmission:
       ```txt
       Confidential Audit Finding: Server 10.10.1.19 root credentials compromised.
       ```
  2. <b>Execute Military-Grade Symmetric Encryption:</b>
     - Click <b>Encrypt Text</b> on the toolbar.
     - Select cipher: <b>AES (Rijndael) - 256 bit key length</b>.
     - Enter and confirm a strong passphrase.
     - The text in the editor is immediately replaced with an armored ciphertext block.
  3. <b>Perform Secure File Shredding:</b>
     - Right-click a sensitive local document on Windows 11 and select <b>CryptoForge Shredder</b>.
     - Select the DoD 5220.22-M wiping standard (multi-pass overwrite of random bit patterns) to permanently sanitize the underlying flash sectors against forensic recovery.

---

#### Task 3: Create Self-Signed Certificates using OpenSSL

- <b>Environment:</b>
  - System: Parrot Security (<code>10.10.1.13</code>) / Linux terminal.
  - Tool: OpenSSL CLI.
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Generate RSA Private Key & Self-Signed X.509 Certificate:</b>
     - Open Terminal on Parrot Security, gain root privileges via <code>sudo su</code>.
     - Execute the OpenSSL generation command:
       ```bash
       openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout private_key.pem -out server_cert.pem
       ```
     - Supply the required X.509 Distinguished Name (DN) parameters:
       - Country Name: <code>US</code>
       - State: <code>California</code>
       - Locality: <code>San Jose</code>
       - Organization Name: <code>Enterprise Defense Corp</code>
       - Common Name (CN): <code>secure.enterprise.com</code>
  2. <b>Inspect Generated Certificate Metadata:</b>
     - Verify and print certificate parameters:
       ```bash
       openssl x509 -in server_cert.pem -text -noout
       ```
     - Observe the 4096-bit RSA public key, SHA-256 signature algorithm, validity timestamps, and Issuer/Subject equivalence confirming a self-signed root certificate.

---

#### Task 4: AI-Driven Cryptography using ShellGPT in Parrot Security

- <b>Environment:</b>
  - System: Parrot Security (<code>10.10.1.13</code>).
  - Tool: <code>ShellGPT</code> (<code>sgpt</code>).
- <b>Step-by-Step Operational Procedure:</b>
  1. <b>Calculate Cryptographic Hash via ShellGPT:</b>
     - Open Terminal on Parrot Security and execute natural language cryptographic query:
       ```bash
       sgpt --shell "Calculate MD5 hash of text 'My Account number is 0234569198'"
       ```
     - ShellGPT constructs and displays the Unix command:
       ```bash
       echo -n 'My Account number is 0234569198' | md5sum | awk '{print $1}'
       ```
     - Press <code>E</code> to execute. Observe generated 128-bit MD5 digest:
       ```txt
       0492bacab27860f27b6e7adfcb31a0e8
       ```
  2. <b>Perform Multi-Layer Chained Hashing:</b>
     - Prompt ShellGPT to chain hash functions:
       ```bash
       sgpt --shell "Calculate MD5 hash of text 'My Account number is 0234569198' and calculate the SHA1 hash value of that MD5 value"
       ```
     - ShellGPT generates piped execution pipeline:
       ```bash
       echo -n 'My Account number is 0234569198' | md5sum | awk '{print $1}' | tr -d '\n' | sha1sum | awk '{print $1}'
       ```
     - Press <code>E</code> to execute and obtain the 160-bit SHA-1 digest.
  3. <b>Perform File Checksums with CRC32:</b>
     - Query ShellGPT for checksum calculation:
       ```bash
       sgpt --chat hash --shell "Calculate CRC32 hash of the file passwords.txt located at /home/attacker"
       ```
     - ShellGPT outputs <code>crc32 /home/attacker/passwords.txt</code>, returning the 32-bit checksum.
  4. <b>Base64 Encoding and Decoding Workflows:</b>
     - Encode plaintext:
       ```bash
       sgpt --shell "Encrypt 'Hello World' text using base64 algorithm and save the result to Output.txt file"
       ```
     - Decrypt/Decode ciphertext:
       ```bash
       sgpt --shell "Decrypt the contents of encrypted Output.txt file located at /home/attacker using base64 algorithm"
       ```
     - View decoded file with <code>cat DecryptedOutput.txt</code> confirming <code>"Hello World"</code>.

---

## 7. High-Frequency Exam Indicators & Key Memory Anchors

```javascript
+----------------------------------------------------------------------------------------------------+
|                                  CEH v13 EXAM CRITICAL FOCUS POINTS                                |
+----------------------------+-----------------------------------------------------------------------+
| Exam Question Theme        | Key Answer / Official EC-Council Exam Concept                         |
+----------------------------+-----------------------------------------------------------------------+
| Kerckhoffs's Principle     | A cryptosystem must remain secure even if everything about the system |
|                            | is public knowledge, except the secret cryptographic key.             |
+----------------------------+-----------------------------------------------------------------------+
| Shannon's Concepts         | Diffusion hides plaintext redundancy (avalanche effect / ShiftRows);   |
| (Confusion vs. Diffusion)  | Confusion complicates key-ciphertext relationship (S-Boxes / SubBytes)|
+----------------------------+-----------------------------------------------------------------------+
| AES Structure & Rounds     | Non-Feistel Substitution-Permutation Network; 128-bit block size;     |
|                            | 128-bit key (10 rds), 192-bit key (12 rds), 256-bit key (14 rds).    |
+----------------------------+-----------------------------------------------------------------------+
| Block Cipher Mode Flaw     | Electronic Codebook (ECB) encrypts identical plaintext blocks into    |
| (ECB Mode)                 | identical ciphertext blocks; leaks underlying data patterns; INSECURE.|
+----------------------------+-----------------------------------------------------------------------+
| Asymmetric vs Symmetric    | Asymmetric (RSA/ECC) solves key distribution; slow computationally.   |
| Usage (Hybrid Systems)     | Symmetric (AES) handles bulk data payload encryption at high speed.   |
+----------------------------+-----------------------------------------------------------------------+
| Digital Signature Principle| Sender encrypts message digest with SENDER'S PRIVATE KEY; recipient   |
|                            | verifies with SENDER'S PUBLIC KEY; guarantees Non-Repudiation.        |
+----------------------------+-----------------------------------------------------------------------+
| Birthday Attack Mechanics  | Exploits Birthday Paradox to find hash collisions in O(2^(n/2));      |
|                            | targeting weak hashes (MD5 64-bit collision space, SHA-1).            |
+----------------------------+-----------------------------------------------------------------------+
| Meet-in-the-Middle Attack  | Reduces 2DES effective security from 2^112 to 2^57 operations by      |
|                            | computing forward encryption and backward decryption tables.          |
+----------------------------+-----------------------------------------------------------------------+
| Quantum Impact on Crypto   | Shor's algorithm breaks RSA, ECC, and DH in polynomial time;          |
| (Shor's vs. Grover's)      | Grover's algorithm halves symmetric key strength (AES-256 -> AES-128).|
+----------------------------+-----------------------------------------------------------------------+
| Broken Hash Functions      | MD5 (128-bit) and SHA-1 (160-bit) are cryptographically broken;       |
|                            | collisions demonstrated; banned for secure digital signatures.        |
+----------------------------+-----------------------------------------------------------------------+
| PKI Revocation Checking    | CRL is a periodic signed list; OCSP queries live revocation status;   |
| (CRL vs. OCSP)             | OCSP Stapling allows web server to bundle cached signed OCSP response.|
+----------------------------+-----------------------------------------------------------------------+
| Secure Password KDFs       | Argon2id (memory-hard, side-channel resistant), bcrypt (cost factor), |
|                            | PBKDF2; require salting and high iteration counts to defeat GPUs.     |
+----------------------------+-----------------------------------------------------------------------+
```
