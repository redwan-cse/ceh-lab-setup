# CEH practical tool reference

Start with the task, check availability, then use the smallest relevant command.
Examples use placeholders: replace `HOST`, `URL`, `DOMAIN`, `USER`, `FILE` and
`AUTHORIZED_CIDR` with values from your task. They are not runnable defaults or
permission to scan. Use only the assigned machines, accounts and files.

| Task | Guide |
|---|---|
| What is installed, missing or only in the share? | [Inventory summary](inventory.md), [Parrot detail](inventory-linux.md), [Windows detail](inventory-windows.md) |
| Host discovery, ports, DNS, SMB/LDAP, web enumeration/testing | [Network and web](network-and-web.md) |
| Hash identification, offline cracking, limited online audits | [Password auditing](password-auditing.md) |
| PCAP filtering, conversations, HTTP/DNS, capture limits | [Traffic analysis](traffic-analysis.md) |
| Extraction, hashes, decoding, steganography, binary/crypto tools | [Forensics and crypto](forensics-and-crypto.md) |
| ADB, APKs, PhoneSploit variants, wireless captures | [Mobile and wireless](mobile-and-wireless.md) |
| Native PowerShell equivalents and Windows GUI tools | [Windows PowerShell](windows-powershell.md) |

## Use with ShellGPT

The exam installer copies these Markdown files beside its runtime. It does not
send the whole library with every request. Use the same `sgpt` command after
selecting DeepSeek or StepFun; `sgpt --model-info` shows its configured model
and endpoint without a paid call. Local lookup costs no API tokens:

```text
sgpt --tool-help "nmap"
sgpt --tool-help "hashing"
```

During a normal task the model can call `find_ceh_reference` for up to 5,000
characters of relevant excerpts. `find_ceh_tools` separately finds existing
paths in your indexed tools folder. A reference example is not proof that a
tool is installed or its dependencies work. The model must check the current
OS, tool version, scope and actual output, and ask before installation or
critical configuration changes.

```text
sgpt "Use the tool reference to explain how to inspect my supplied PCAP. Check which tool is available first."
```

For GUI tasks, give sgpt the actual tools root and the observations it requests.
It can provide steps and save a confirmed flag plus how it was found; it cannot
see GUI results automatically. Terminal commands/output stay in `terminal.md`;
confirmed findings stay in `findings.txt` under the selected IP folder.

## Refresh the inventory without installing tools

Run on the machine being inspected, from the repository root:

```powershell
powershell -NoProfile -File .\ceh-local-lab\Inspect-CehTools.ps1
```

```bash
python3 ./ceh-local-lab/inspect-ceh-tools-linux.py
```

These read-only scripts inspect metadata. Inspect their help/parameters to
select your current tools root. They do not launch course tools or install
packages. The saved inventory pages describe a dated local lab observation,
not a guarantee about a fresh exam machine.
