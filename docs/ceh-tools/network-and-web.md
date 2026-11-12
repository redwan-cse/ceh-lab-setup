# Network and web tasks (Parrot)

For active tests, use the targets or CIDR assigned to your lab, including
public lab websites. Public-source research and ordinary public-page/DNS
lookups do not need a private network range. `TARGET`,
`AUTHORIZED_CIDR`, `DNS_SERVER`, `LAB_NAME`, `LAB_USER`, and `BASE_DN` are
placeholders: replace them before running a command. The audit ran none of
these probes. See [availability](inventory-linux.md) before choosing a tool.
When using ShellGPT, submit each command through its existing guarded execution
flow and approve when requested; retain the current approval policy.

## Passive sources and public website research

Reuse the URL/domain supplied in the task; no extra scope confirmation, CIDR,
initialization or lab-only DNS is needed for this read-only work. Use available
public search results, WHOIS/RDAP, certificate-transparency, passive DNS and
public documents. Ordinary page retrieval and normal DNS queries make network
requests, although they are not vulnerability scans or login attempts.

```bash
curl --head --max-time 15 'https://TARGET/'
curl --max-time 20 --output "$CEH_EXAM_DIR/homepage.html" 'https://TARGET/'
dig TARGET MX +noall +answer
dig TARGET TXT +noall +answer
```

Check the actual response, then inspect relevant public contact/about pages or
links. Preserve source URLs and retrieved evidence in the exam folder. Verify
any email/answer against returned content rather than guessing. Public lookup
permission does not make port scans, directory brute force, DNS brute force,
login attempts or exploitation passive. Keep active tests on assigned task
targets. Windows alternatives include `Invoke-WebRequest -UseBasicParsing`
with `-OutFile` inside `$env:CEH_EXAM_DIR` and `Resolve-DnsName`.

## Find hosts, then inspect selected services

```bash
nmap -sL -n AUTHORIZED_CIDR
nmap -sn -n AUTHORIZED_CIDR
nmap -sT -sV --version-light -n -p 22,80,443,445 TARGET
```

The first command lists the scope without target probes or reverse DNS. Review
it first. The second performs host discovery; a missing response does not prove
that a host is down. The third connects only to four selected TCP ports on one
host and attempts light service identification. Change the ports to those in
the exercise. An open port or banner is evidence, not proof of vulnerability.
[Nmap discovery](https://nmap.org/book/man-host-discovery.html) and
[service detection](https://nmap.org/book/man-version-detection.html).

## Query the lab DNS server

```bash
dig @DNS_SERVER LAB_NAME A +noall +answer
nslookup LAB_NAME DNS_SERVER
```

Use the assigned DNS service, not an arbitrary VM. `NXDOMAIN` means the queried
name was not found; a timeout points to server/connectivity problems.
[BIND command manuals](https://bind9.readthedocs.io/en/stable/manpages.html).

The explicit `DNS_SERVER` examples above apply to internal lab names. Public
domain research can use the configured resolver as shown in the public-source
workflow; a lab DNS address is not mandatory for it.

## List SMB shares and LDAP naming contexts

```bash
smbclient -L TARGET -U LAB_USER
smbclient '//TARGET/SHARE' -U LAB_USER -c 'ls'
smbmap -H TARGET -u LAB_USER --prompt --no-write-check --no-update
ldapsearch -x -LLL -H 'ldap://TARGET' -s base -b '' '(objectClass=*)' namingContexts
```

SMB commands prompt for the lab password instead of putting it in shell
history. `--no-write-check` prevents SMBMap's write-permission test. Listing
shows only what the account can access. A denied anonymous LDAP root-DSE query
does not prove LDAP is absent. If a directory exercise permits authenticated
queries, use verified LDAPS or StartTLS and `-D BIND_DN -W`; do not send a simple
bind password over plaintext LDAP. Use the returned naming context as `BASE_DN`
for a separately scoped query. [Samba](https://www.samba.org/samba/docs/current/man-html/smbclient.1.html),
[SMBMap](https://github.com/ShawnDEvans/smbmap),
[OpenLDAP guide](https://www.openldap.org/doc/admin26/OpenLDAP-Admin-Guide.pdf).

## Inspect an HTTP endpoint and identify its stack

```bash
curl --head --max-time 10 'http://TARGET/'
wget --spider --server-response --timeout=10 --tries=1 'http://TARGET/'
whatweb --aggression=1 'http://TARGET/'
```

Headers and WhatWeb fingerprints can suggest server/CMS versions. They may be
hidden, stale, or misleading. WhatWeb level 1 fetches the page and can follow
redirects. Inspect the destination: ordinary public-page retrieval is allowed,
but a redirect does not extend active-testing scope to that host.
Prefer HTTPS when available and keep certificate verification enabled.
Telnet is absent on this Parrot account; use the installed HTTP tools for this
task. [curl](https://curl.se/docs/manpage.html),
[Wget](https://www.gnu.org/software/wget/manual/wget.html),
[WhatWeb](https://github.com/urbanadventurer/WhatWeb).

## Discover content using a small exercise wordlist

```bash
gobuster dir -u 'http://TARGET/' -w './small-lab-paths.txt' -t 2 --delay 500ms --timeout 5s
```

Use a short, reviewed file containing only the paths needed for the exercise.
Inspect response status and length; redirects and wildcard responses can look
like discoveries. If the precheck finds wildcard behavior, investigate it
before changing filters. [Gobuster usage](https://github.com/OJ/gobuster).

## Check a deliberately vulnerable parameter / WordPress site

```bash
sqlmap -u 'http://TARGET/item.php?id=1' -p id --level=1 --risk=1 --threads=1 --timeout=10 --retries=0
wpscan --url 'http://TARGET/' --no-update
```

For SQLmap, use the exact assigned test URL and parameter. Review interactive
prompts and stop after detection; this example requests no database dump or OS
shell. Level/risk 1 still sends test payloads. The timeout applies to individual
requests, not the whole run. [SQLmap usage](https://github.com/sqlmapproject/sqlmap/wiki/Usage).

The WPScan command runs the normal site inventory without explicit username or
password testing. It may make many requests. `--no-update` uses local data;
stale data and an absent WPScan API token limit vulnerability information. Do
not add an update or token as part of this read-only inventory task.
[WPScan documentation](https://github.com/wpscanteam/wpscan/wiki/WPScan-User-Documentation).

For capture-file analysis, use [traffic analysis](traffic-analysis.md);
Wireshark/TShark/Tcpdump availability is recorded in the inventory.
