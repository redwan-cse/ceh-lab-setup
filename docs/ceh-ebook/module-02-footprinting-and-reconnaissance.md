# Module 02: Footprinting and Reconnaissance - Lab Guide

## Tools Used & Purpose

- **Google Advanced Search / Google Dorking**: Information gathering using advanced search operators, cached pages, filetype filters, and directory indexing discovery.
- **Netcraft**: Passive infrastructure discovery, hosting history analysis, IP address mapping, and web technology identification.
- **DNSdumpster**: Domain research, DNS mapping, and automated subdomain discovery.
- **Sherlock**: OSINT hunting of target usernames across hundreds of social media platforms and public forums.
- **DomainTools**: Reverse WHOIS lookup, registrant contact enumeration, and historical domain ownership tracking.
- **nslookup**: DNS record interrogation (A, MX, NS, SOA, CNAME) and testing for unauthorized DNS zone transfers (AXFR).
- **eMailTrackerPro**: Email header analysis to extract originating IP addresses, tracing mail server routing hops, and geolocation.
- **Recon-ng**: Automated modular OSINT reconnaissance framework for harvesting hosts, contacts, subdomains, and credential leaks.
- **theHarvester**: Passive harvesting of employee emails, subdomains, employee names, and open ports from public search engines and PGP servers.
- **ShellGPT (`sgpt`)**: AI-assisted CLI command generation, automated target reconnaissance scripting, and OSINT data synthesis.
- **Maltego**: Visual link analysis and interactive graph transform mapping for network infrastructure, domain entities, and individuals.
- **FOCA**: Extracting and analyzing hidden metadata inside publicly accessible documents (.pdf, .docx, .xlsx) to reveal internal usernames and printer/server paths.

---

# Hands-On Lab Walkthroughs (Labs 1–9)

<i>(Detailed Step-by-Step Breakdown Verified Against Official CEH v13 Lab Manual, Pages 1–62)</i>

---

### Lab 1: Perform Footprinting Through Search Engines

- <b>Lab Environment:</b> Windows 11 VM (<code>Admin</code> / <code>Pa$$w0rd</code>), Web Browser
- <b>Scenario:</b> Gather preliminary intelligence on <code>certifiedhacker.com</code> without direct target interaction.
- <b>Step-by-Step Execution:</b>
  1. <b>Google Advanced Operators:</b>
     - Query: <code>site:certifiedhacker.com</code> $\to$ Returns all indexed pages under the target domain.
     - Query: <code>EC-Council filetype:pdf ceh</code> $\to$ Locates publicly accessible PDF study documents and whitepapers.
     - Query: <code>intitle:"index of /" site:certifiedhacker.com</code> $\to$ Identifies exposed parent directories and unprotected web paths.
     - Query: <code>inurl:admin site:certifiedhacker.com</code> $\to$ Locates administrative portals and login scripts.
  2. <b>Google Hacking Database (GHDB) on Exploit-DB:</b>
     - Navigate to <code>exploit-db.com/google-hacking-database</code>.
     - Filter by category <b>"Pages Containing Login Portals"</b> and <b>"Files Containing Passwords"</b>.
     - Test dorks targeting VPN portals and cloud storage buckets (<code>inurl:vpn/index.html</code>, <code>site:s3.amazonaws.com</code>).
  3. <b>Device Footprinting via Shodan (</b><b><code>shodan.io</code></b><b>):</b>
     - Enter target network or device query (e.g., <code>certifiedhacker.com</code> or IP blocks).
     - Inspect discovered listening services: Port 21 (FTP), Port 22 (SSH), Port 80 (HTTP), Port 443 (HTTPS).
     - Extract server banners, SSL certificate issuer details, geographic hosting location, and detected CVE vulnerabilities.
  4. <b>Reverse Image Search:</b>
     - Open Google Images (<code>google.com/imghp</code>) and TinEye (<code>tineye.com</code>).
     - Upload employee profile pictures from target site to locate alternate social media accounts, stock photo originations, and real identities.

---

### Lab 2: Perform Footprinting Through Internet Research Services

- <b>Lab Environment:</b> Windows 11 VM, Web Browser
- <b>Scenario:</b> Map the external perimeter, web server technology stacks, and historical changes of <code>certifiedhacker.com</code> and <code>microsoft.com</code>.
- <b>Step-by-Step Execution:</b>
  1. <b>Netcraft Site Report (</b><b><code>netcraft.com</code></b><b>):</b>
     - Navigate to Netcraft $\to$ Resources $\to$ Research Tools $\to$ <b>Site Report</b>.
     - Target: <code>certifiedhacker.com</code>.
     - Extracted Intelligence: Domain registrar (<code>FastDomain Inc.</code>), primary nameservers, IPv4 address (<code>162.241.216.11</code>), hosting company (<code>Unified Layer</code>), netblock owner, web server operating system (Linux), and web server application version (Apache).
  2. <b>Subdomain & Infrastructure Mapping via DNSdumpster (</b><b><code>dnsdumpster.com</code></b><b>):</b>
     - Enter target domain: <code>certifiedhacker.com</code>.
     - Harvested Records:
       - <b>DNS Servers:</b> <code>ns1.bluehost.com</code>, <code>ns2.bluehost.com</code>.
       - <b>MX Records:</b> <code>mail.certifiedhacker.com</code> (Preference 0).
       - <b>Host Records (A):</b> Discovers subdomains, intranet portals, webmail gateways, and IP addresses.
     - Downloaded complete <code>.xlsx</code> target host inventory and analyzed interactive network relationship diagram.
  3. <b>Subdomain Enumeration via Pentest-Tools:</b>
     - Run <b>Subdomain Finder (Light Scan)</b> against target domain to cross-validate discovered web properties.
  4. <b>Historical Website Retrieval via Wayback Machine (</b><b><code>archive.org</code></b><b>):</b>
     - Enter <code>http://www.certifiedhacker.com</code> into the Wayback Machine search field.
     - Select calendar snapshots spanning several years.
     - Identified obsolete URL endpoints, previous technical staff names, retired product architectures, and legacy contact emails that remain vulnerable to social engineering.

---

### Lab 3: Perform Footprinting Through Social Networking Sites

- <b>Lab Environment:</b> Parrot Security VM (<code>attacker</code> / <code>toor</code>), Terminal
- <b>Scenario:</b> Investigate public profiles and corporate presence across 300+ social platforms.
- <b>Step-by-Step Execution:</b>
  1. Open terminal on Parrot Security.
  2. Execute the <b>Sherlock</b> CLI utility against a target handle or employee name:
     ```bash
     sherlock "Elon Musk"
     ```
  3. <b>Output Analysis:</b> Sherlock automatically probes hundreds of social networks, discussion boards, and developer repositories (GitHub, Reddit, Twitter, Instagram, TikTok, Steam, Vimeo).
  4. Dumps verified URL links to live profiles. Ethical hackers inspect profile descriptions, location tags, and associated email handles for credential harvesting and password recovery clues.

---

### Lab 4: Perform Whois Footprinting

- <b>Lab Environment:</b> Windows 11 VM, Web Browser
- <b>Scenario:</b> Obtain registrar, administrative, and ownership records for <code>certifiedhacker.com</code>.
- <b>Step-by-Step Execution:</b>
  1. Open browser and navigate to <code>whois.domaintools.com</code>.
  2. Enter domain: <code>certifiedhacker.com</code>.
  3. <b>Extracted Whois Fields Analyzed:</b>
     - <b>Domain Profile:</b> Registrant Org, Dates (Registration created date, registry expiration date, last update timestamp).
     - <b>Registrar Info:</b> Registrar name (<code>FastDomain Inc.</code>), IANA ID, Registrar Status (<code>clientTransferProhibited</code>).
     - <b>Administrative & Technical Contacts:</b> Name, postal address, telephone number, and administrative email address.
     - <b>Name Servers:</b> <code>NS1.BLUEHOST.COM</code>, <code>NS2.BLUEHOST.COM</code>.
     - <b>IP Location & ASN:</b> IP <code>162.241.216.11</code>, Autonomous System Number, and physical hosting coordinates.

---

### Lab 5: Perform DNS Footprinting

- <b>Lab Environment:</b> Windows 11 VM, Command Prompt & Online DNS Tools
- <b>Scenario:</b> Extract all public DNS zone records using command-line interrogation.
- <b>Step-by-Step Execution:</b>
  1. Launch Command Prompt on Windows 11.
  2. Start <code>nslookup</code> in interactive mode:
     ```shell
     nslookup
     ```
  3. Query <b>A Records</b> (IPv4 Address):
     ```shell
     set type=a
     certifiedhacker.com
     ```

     - <i>Result:</i> Returns address <code>162.241.216.11</code>.
  4. Query <b>CNAME Records</b> (Canonical Aliases):
     ```shell
     set type=cname
     www.certifiedhacker.com
     ```

     - <i>Result:</i> Reveals canonical name mapping.
  5. Query <b>NS Records</b> (Authoritative Name Servers):
     ```shell
     set type=ns
     certifiedhacker.com
     ```

     - <i>Result:</i> Discloses primary DNS servers <code>ns1.bluehost.com</code> and <code>ns2.bluehost.com</code>.
  6. Query <b>MX Records</b> (Mail Exchange Handlers):
     ```shell
     set type=mx
     certifiedhacker.com
     ```

     - <i>Result:</i> Discloses <code>mail.certifiedhacker.com</code> with priority/preference <code>0</code>.
  7. Query <b>SOA Records</b> (Start of Authority):
     ```shell
     set type=soa
     certifiedhacker.com
     ```

     - <i>Result:</i> Returns Primary Name Server, Responsible Administrator Mailbox (<code>hostmaster</code>), Serial Number, and Refresh/Retry/Expire timers.
  8. <b>Online Web DNS Tools:</b> Access <code>kloth.net</code> or <code>nslookup.io</code> to query <code>AAAA</code> (IPv6) and <code>PTR</code> (Reverse IP) records.

---

### Lab 6: Perform Network Footprinting

- <b>Lab Environment:</b> Windows 11 VM & Parrot Security VM
- <b>Scenario:</b> Trace the router hop path to target host <code>www.certifiedhacker.com</code> and compare Layer-3/4 packet behaviors.
- <b>Step-by-Step Execution:</b>
  1. <b>Windows 11 ICMP Tracerouting:</b>
     - Open Command Prompt and execute:
       ```shell
       tracert -h 5 www.certifiedhacker.com
       ```
     - <i>Mechanism:</i> Windows transmits <b>ICMP Echo Request</b> packets with incrementing TTL values (from 1 to 5).
     - <i>Observation:</i> Displays 5 intermediate router hops, round-trip times (RTT), and hop IP addresses.
  2. <b>Parrot Security UDP Tracerouting:</b>
     - Open Terminal on Parrot Security and execute:
       ```bash
       traceroute www.certifiedhacker.com
       ```
     - <i>Mechanism:</i> Linux transmits <b>UDP probe packets</b> to high destination ports (33434+).
     - <i>Observation:</i> Intermediary routers decrement TTL to <code>0</code> and return <b>ICMP Type 11 Code 0 (Time-to-Live Exceeded in Transit)</b>.

---

### Lab 7: Perform Email Footprinting

- <b>Lab Environment:</b> Windows 11 VM, <code>eMailTrackerPro</code>
- <b>Scenario:</b> Dissect email headers to identify the originating sender IP, mail server path, and geographic trace.
- <b>Step-by-Step Execution:</b>
  1. Open webmail client in Windows 11 and open a received test email.
  2. Access the <b>Raw / Original Message Source</b> and copy the complete email header text.
  3. Launch <b>eMailTrackerPro</b>.
  4. Click <b>My Trace Reports</b> $\to$ Select <b>Trace an email I have received</b>.
  5. Paste the copied email header into the <b>Email headers:</b> dialog box and click <b>Trace</b>.
  6. <b>Analysis of Trace Results:</b>
     - Decodes <code>Received: from</code> headers in reverse chronological order (bottom to top).
     - Identifies the originating client IP address (<code>X-Originating-IP</code>).
     - Extracts intermediate Mail Transfer Agent (MTA) server hops, domain names, and timestamps.
     - Displays sender ISP, geographic coordinates, and plots the transmission route on an interactive 3D world map.

---

### Lab 8: Perform Footprinting using Various Footprinting Tools (Recon-ng)

- <b>Lab Environment:</b> Parrot Security VM (<code>attacker</code> / <code>toor</code>), Terminal
- <b>Scenario:</b> Execute a structured, multi-module OSINT investigation on <code>certifiedhacker.com</code> using the Recon-ng framework.
- <b>Step-by-Step Execution:</b>
  1. Open terminal on Parrot Security and launch Recon-ng:
     ```bash
     recon-ng
     ```
  2. Create an isolated workspace:
     ```bash
     [recon-ng][default] > workspaces create CEH
     [recon-ng][CEH] > workspaces list
     ```
  3. Search and install modules from the official marketplace:
     ```bash
     [recon-ng][CEH] > marketplace search
     [recon-ng][CEH] > marketplace install recon/domains-hosts/brute_hosts
     [recon-ng][CEH] > marketplace install recon/hosts-hosts/resolve
     [recon-ng][CEH] > marketplace install recon/domains-contacts/whois_pocs
     [recon-ng][CEH] > marketplace install reporting/html
     ```
  4. Seed the workspace database with the target domain:
     ```bash
     [recon-ng][CEH] > db insert domains
     domain (TEXT): certifiedhacker.com
     [recon-ng][CEH] > show domains
     ```
  5. Execute Subdomain Brute-Forcing:
     ```bash
     [recon-ng][CEH] > modules load recon/domains-hosts/brute_hosts
     [recon-ng][CEH][brute_hosts] > run
     ```
  6. Resolve Discovered Hostnames to IP Addresses:
     ```bash
     [recon-ng][CEH] > modules load recon/hosts-hosts/resolve
     [recon-ng][CEH][resolve] > run
     [recon-ng][CEH][resolve] > show hosts
     ```
  7. Harvest Point-of-Contact (POC) Information:
     ```bash
     [recon-ng][CEH] > modules load recon/domains-contacts/whois_pocs
     [recon-ng][CEH][whois_pocs] > run
     [recon-ng][CEH][whois_pocs] > show contacts
     ```
  8. Export Professional HTML Reconnaissance Report:
     ```bash
     [recon-ng][CEH] > modules load reporting/html
     [recon-ng][CEH][html] > options set FILENAME /home/attacker/CEH_Report.html
     [recon-ng][CEH][html] > options set CREATOR Certified Ethical Hacker
     [recon-ng][CEH][html] > run
     ```
  9. Open <code>/home/attacker/CEH_Report.html</code> in Firefox to review the complete consolidated summary of discovered hosts, contacts, and IP mappings.

---

### Lab 9: Perform Footprinting using AI (ShellGPT / <code>sgpt</code>)

- <b>Lab Environment:</b> Parrot Security VM (<code>attacker</code> / <code>toor</code>), Terminal
- <b>Scenario:</b> Automate complex terminal footprinting pipelines using natural language prompts via ShellGPT (<code>sgpt</code>).
- <b>Step-by-Step Execution:</b>
  1. Open terminal on Parrot Security.
  2. <b>Automated theHarvester OSINT Query:</b>
     ```bash
     sgpt --chat footprint --shell "Use theHarvester to gather emails, subdomains, hosts, and employee names from Baidu for domain microsoft.com and save to output.txt"
     ```

     - ShellGPT interprets prompt, generates <code>theHarvester -d microsoft.com -b baidu -f output.txt</code>, prompts user approval <code>[E]xecute</code>, and runs the command.
  3. <b>Automated Sherlock Social Investigation:</b>
     ```bash
     sgpt --chat footprint --shell "Use Sherlock to gather personal information about 'Sundar Pichai' and save the result in recon2.txt"
     ```

     - Automates Sherlock query and logs matching social profiles to disk.
  4. <b>Automated Website Mirroring via Photon:</b>
     ```bash
     sgpt --chat footprint --shell "Use website mirroring to footprint the target website www.certifiedhacker.com using Photon and save results in target_recon"
     ```

     - Crawls target site extracting internal links, scripts, and embedded documents.
  5. <b>Automated DNS Enumeration via DNSRecon:</b>
     ```bash
     sgpt --chat footprint --shell "Install and use DNSRecon to perform DNS enumeration on the target domain www.certifiedhacker.com"
     ```

     - Automatically verifies prerequisites, installs missing components, and executes comprehensive DNS record audits.
  6. <b>Automated Traceroute Path Discovery:</b>
     ```bash
     sgpt --chat footprint --shell "Perform network tracerouting to discover the routers on the path to a target host www.certifiedhacker.com"
     ```
  7. <b>Automated Python Script Creation:</b>
     ```bash
     sgpt --chat footprint --shell "Develop a Python script which will accept domain name microsoft.com as input and perform WHOIS and DNS lookup on it"
     ```

     - Generates <code>python_footprint.py</code> containing Python <code>subprocess.run()</code> calls for <code>whois</code> and <code>nslookup</code>.
     - Executes script via <code>python3 python_footprint.py</code>, outputting combined DNS and ownership intelligence.
